"""Real execution engine for ORCA ADE orchestration.

Wires plan_parser -> flight_plan -> worktree_engine -> state_engine ->
hooks -> gate_auditor -> circuit_breaker into one deterministic,
parallel, resumable multi-front orchestration run.

Specs:
  - docs/features/orquestracao-orca-ade/MANUAL-UNIFICADO-ORQUESTRACAO-ORCA-ADE.md

Known limitation: a front caught mid-RUNNING by a crash/--resume is retried
from scratch (stale worktree/branch purged, fresh dispatch) rather than
resumed mid-process — exact process resume for arbitrary third-party CLI
harnesses is not deterministically feasible, so partial in-progress work is
discarded. Hardened against the sharpest edge of that gap: the front's
agent pid is recorded while RUNNING, and a retry/resume kills that pid
before purging (an orphaned child process — subprocess.Popen does not tie
child lifetime to the parent — would otherwise hold file handles that make
``git worktree remove`` fail silently). If the purge still fails, the front
is marked FAILED with a clear reason instead of being silently re-dispatched
into a confusing "worktree already exists" error.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

try:
    from flight_plan import gerar_plano_de_voo, renderizar_plano_de_voo
    from worktree_engine import criar_worktree, mergear_worktree, purgar_worktree
    from state_engine import (
        FrontState,
        ResumeAction,
        _write_atomic,
        classify_resume,
        create_initial_state,
        load_state,
        render_memory_md,
        save_state,
        update_front_state,
    )
    from hooks import executar_post_hook, executar_pre_hook
    from circuit_breaker import (
        CircuitBreakerConfig,
        HealthStatus,
        avaliar_saude,
        interromper_processo,
    )
except ImportError:
    from scripts.flight_plan import gerar_plano_de_voo, renderizar_plano_de_voo
    from scripts.worktree_engine import criar_worktree, mergear_worktree, purgar_worktree
    from scripts.state_engine import (
        FrontState,
        ResumeAction,
        _write_atomic,
        classify_resume,
        create_initial_state,
        load_state,
        render_memory_md,
        save_state,
        update_front_state,
    )
    from scripts.hooks import executar_post_hook, executar_pre_hook
    from scripts.circuit_breaker import (
        CircuitBreakerConfig,
        HealthStatus,
        avaliar_saude,
        interromper_processo,
    )


BREAKER_POLL_SECONDS = 2.0
ENV_FILENAMES = (".env", ".env.local")


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def _run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)


def _repo_root(path: str | Path) -> Path:
    result = _run_git(["rev-parse", "--show-toplevel"], Path(path).resolve())
    if result.returncode != 0:
        raise RuntimeError(f"Nao foi possivel resolver a raiz git de {path}: {result.stderr}")
    return Path(result.stdout.strip())


def _git_path(worktree_path: Path, relative: str) -> Path:
    """Resolve a git-managed path (e.g. info/exclude) that may live in the
    common git dir rather than physically under <worktree>/.git (worktrees
    have .git as a *file*, not a directory)."""
    result = _run_git(["rev-parse", "--git-path", relative], worktree_path)
    if result.returncode != 0:
        raise RuntimeError(f"git rev-parse --git-path falhou: {result.stderr}")
    p = Path(result.stdout.strip())
    if not p.is_absolute():
        p = worktree_path / p
    return p


def _capture_base_sha(repo_path: Path) -> str:
    result = _run_git(["rev-parse", "HEAD"], repo_path)
    if result.returncode != 0:
        raise RuntimeError(f"Nao foi possivel capturar HEAD de {repo_path}: {result.stderr}")
    return result.stdout.strip()


def _auto_commit_front(worktree_path: Path, front_name: str) -> None:
    status = _run_git(["status", "--porcelain"], worktree_path)
    if not status.stdout.strip():
        return
    _run_git(["add", "-A"], worktree_path)
    _run_git(["commit", "-m", f"orca: frente {front_name} concluida pelo agente"], worktree_path)


def _touched_paths(worktree_path: Path, base_sha: str) -> list[str]:
    result = _run_git(["diff", "--name-only", base_sha, "HEAD"], worktree_path)
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def _quarantine_purge_if_stale(
    front_name: str, repo_path: Path, pid: int | None = None,
) -> tuple[bool, str]:
    """Purge a leftover worktree/branch before a retry — hardened.

    An orchestrator crash can leave the harness subprocess running as an
    orphan (subprocess.Popen does not tie child lifetime to the parent on
    its own), holding file handles inside the worktree that would make
    ``git worktree remove`` fail silently. If a pid was recorded for this
    front's last RUNNING attempt, it is killed first and given a brief
    moment to release its handles.

    Returns (ok, detail) — ok=False means the front must NOT be
    re-dispatched this run (a confusing "worktree already exists" failure
    downstream is worse than a clear, explicit FAILED here).
    """
    if pid:
        interromper_processo(pid)
        time.sleep(0.5)

    wt = repo_path / f"wt-{front_name}"
    if not wt.exists():
        _run_git(["branch", "-D", f"orca/{front_name}"], repo_path)
        return True, "sem worktree residual"

    result = purgar_worktree(front_name, repo_path)
    if not result.ok:
        return False, f"purga da worktree residual falhou: {result.stderr[:300]}"
    return True, "worktree residual purgada"


# ---------------------------------------------------------------------------
# Env propagation (manual, Secao 11.3)
# ---------------------------------------------------------------------------

def propagar_env(repo_path: Path, worktree_path: Path) -> list[str]:
    """Copy local-only env files into the worktree and git-exclude them.

    Worktrees only ever check out committed content; untracked local files
    like .env never appear in a fresh worktree on their own. Returns the
    list of filenames actually propagated.
    """
    propagated: list[str] = []
    for name in ENV_FILENAMES:
        src = repo_path / name
        if not src.is_file():
            continue
        shutil.copyfile(src, worktree_path / name)
        propagated.append(name)

    if propagated:
        exclude_path = _git_path(worktree_path, "info/exclude")
        exclude_path.parent.mkdir(parents=True, exist_ok=True)
        existing_lines = (
            exclude_path.read_text(encoding="utf-8").splitlines()
            if exclude_path.exists()
            else []
        )
        for name in propagated:
            if name not in existing_lines:
                existing_lines.append(name)
        exclude_path.write_text("\n".join(existing_lines) + "\n", encoding="utf-8")

    return propagated


# ---------------------------------------------------------------------------
# Circuit breaker wait loop (Secao 12)
# ---------------------------------------------------------------------------

def _wait_with_circuit_breaker(
    process: subprocess.Popen,
    exec_log_path: Path,
    config: CircuitBreakerConfig,
    front_name: str = "",
    stream: bool = False,
) -> tuple[int, HealthStatus]:
    start = time.time()
    last_pos = 0
    while True:
        ret = process.poll()

        # Se stream estiver ativo, le novas linhas adicionadas ao log e exibe
        if stream and exec_log_path.exists():
            try:
                with open(exec_log_path, "r", encoding="utf-8", errors="replace") as f:
                    f.seek(last_pos)
                    new_chunk = f.read()
                    last_pos = f.tell()
                    if new_chunk:
                        for line in new_chunk.splitlines():
                            if line.strip():
                                print(f"[{front_name}] {line}")
            except Exception:
                pass

        if ret is not None:
            return ret, HealthStatus.OK

        now = time.time()
        last_activity = exec_log_path.stat().st_mtime if exec_log_path.exists() else start
        health = avaliar_saude(start, last_activity, now, config)

        if health != HealthStatus.OK:
            interromper_processo(process.pid)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                pass
            return (process.returncode if process.returncode is not None else -9), health

        time.sleep(BREAKER_POLL_SECONDS)


# ---------------------------------------------------------------------------
# Forensic log/report preservation (Secao 11.2) — before any purge
# ---------------------------------------------------------------------------

def _orca_dir(repo_path: Path) -> Path:
    d = repo_path / ".orca"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _preservar_forensics(
    repo_path: Path,
    front_name: str,
    exec_log_path: Path,
    agent_exit_code: int,
    health: HealthStatus,
    new_state: str,
) -> None:
    orca = _orca_dir(repo_path)
    logs_dir = orca / "logs"
    reports_dir = orca / "reports"
    logs_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    if exec_log_path.exists():
        shutil.copyfile(exec_log_path, logs_dir / f"{front_name}.log")

    report = {
        "front": front_name,
        "state": new_state,
        "agent_exit_code": agent_exit_code,
        "circuit_breaker": health.value,
        "timestamp": time.time(),
    }
    (reports_dir / f"{front_name}.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Shared state-file mutation (always under state_lock — many threads write
# the same .orca_state.json concurrently)
# ---------------------------------------------------------------------------

def _set_front_state(
    state_path: Path, state_lock: threading.Lock, front_name: str,
    new_state: FrontState, commit_sha: str | None = None, pid: int | None = None,
) -> None:
    with state_lock:
        state = load_state(state_path)
        state = update_front_state(state, front_name, new_state, commit_sha=commit_sha, pid=pid)
        save_state(state, state_path)
        _write_atomic(state_path.parent / "memory.md", render_memory_md(state))


# ---------------------------------------------------------------------------
# Merge queue (Secao 11.1) — single global lock serializes all merges
# ---------------------------------------------------------------------------

def _merge_and_finalize(
    front_name: str,
    repo_path: Path,
    state_path: Path,
    merge_lock: threading.Lock,
    state_lock: threading.Lock,
    results: dict,
) -> None:
    with merge_lock:
        merge_result = mergear_worktree(front_name, repo_path)
        if not merge_result.ok:
            _set_front_state(state_path, state_lock, front_name, FrontState.FAILED)
            results[front_name] = "FAILED(merge_conflict)"
            return

        purge_result = purgar_worktree(front_name, repo_path)
        merge_sha = _run_git(["rev-parse", "HEAD"], repo_path).stdout.strip()
        _set_front_state(state_path, state_lock, front_name, FrontState.MERGED, commit_sha=merge_sha)
        results[front_name] = (
            FrontState.MERGED.value
            if purge_result.ok
            else f"MERGED(purge_failed:{purge_result.stderr[:200]})"
        )


# ---------------------------------------------------------------------------
# Per-front worker: full dispatch (worktree -> agent -> gate -> merge)
# ---------------------------------------------------------------------------

def _dispatch_front(
    front: dict,
    repo_path: Path,
    state_path: Path,
    state_lock: threading.Lock,
    base_sha: str,
    merge_lock: threading.Lock,
    breaker_config: CircuitBreakerConfig,
    results: dict,
    stream: bool = False,
    interactive: bool = False,
) -> None:
    front_name = front["name"]
    worktree_path = repo_path / f"wt-{front_name}"

    try:
        wt_result = criar_worktree(front_name, repo_path)
        if not wt_result.ok:
            _set_front_state(state_path, state_lock, front_name, FrontState.FAILED)
            results[front_name] = f"FAILED(worktree_create:{wt_result.stderr[:200]})"
            return

        propagar_env(repo_path, worktree_path)

        with state_lock:
            executar_pre_hook(front_name, worktree_path, state_path)

        exec_log_path = worktree_path / "exec.log"
        if interactive:
            print(f"\n{'='*70}\n[ORCA ADE] SESSAO INTERATIVA: {front_name} (Harness: {front.get('harness', '-')})\n{'='*70}")
            _set_front_state(
                state_path, state_lock, front_name, FrontState.RUNNING, pid=os.getpid()
            )
            proc = subprocess.run(front["command"], cwd=worktree_path)
            agent_exit_code = proc.returncode
            health = HealthStatus.OK
            with open(exec_log_path, "w", encoding="utf-8") as log_fh:
                log_fh.write(f"Interactive run exited with {agent_exit_code}\n")
        else:
            with open(exec_log_path, "w", encoding="utf-8") as log_fh:
                process = subprocess.Popen(
                    front["command"],
                    cwd=worktree_path,
                    stdout=log_fh,
                    stderr=subprocess.STDOUT,
                )
                _set_front_state(
                    state_path, state_lock, front_name, FrontState.RUNNING, pid=process.pid
                )
                agent_exit_code, health = _wait_with_circuit_breaker(
                    process, exec_log_path, breaker_config, front_name=front_name, stream=stream
                )

        _auto_commit_front(worktree_path, front_name)
        touched = _touched_paths(worktree_path, base_sha)

        with state_lock:
            post_result = executar_post_hook(
                front_name=front_name,
                worktree_path=worktree_path,
                state_path=state_path,
                agent_exit_code=agent_exit_code,
                touched_paths=touched,
            )
        new_state = post_result["state"]

        _preservar_forensics(
            repo_path, front_name, exec_log_path, agent_exit_code, health, new_state
        )

        if new_state == FrontState.GATE_PASSED.value:
            _merge_and_finalize(front_name, repo_path, state_path, merge_lock, state_lock, results)
        else:
            results[front_name] = new_state

    except Exception as exc:  # noqa: BLE001 — front isolation: 1 crash != whole run
        _set_front_state(state_path, state_lock, front_name, FrontState.FAILED)
        results[front_name] = f"FAILED(exception:{exc})"


# ---------------------------------------------------------------------------
# Approval gate (Secao 7 do manual — Plano de Voo)
# ---------------------------------------------------------------------------

def _confirm(flight_md: str, yes: bool) -> bool:
    print(flight_md)
    if yes:
        return True
    if not sys.stdin.isatty():
        print(
            "[ABORTADO] Confirmacao necessaria mas stdin nao e interativo. "
            "Rode novamente com --yes para aprovar o Plano de Voo."
        )
        return False
    try:
        resposta = input(
            "[ENTER/'s'] Confirmar e iniciar  |  ['c'] Cancelar\nSua escolha: "
        ).strip().lower()
    except EOFError:
        print(
            "\n[ABORTADO] Nao foi possivel ler confirmacao (EOF em stdin). "
            "Rode novamente com --yes para aprovar o Plano de Voo."
        )
        return False
    if resposta in ("", "s", "sim", "y", "yes"):
        return True
    print("[CANCELADO] Orquestracao nao iniciada.")
    return False


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def executar_orquestracao(
    plan_dir: str | Path,
    profiles_path: str | Path,
    harness: str = "mimo",
    *,
    harness_map: dict[str, str] | None = None,
    repo_path: str | Path | None = None,
    resume: bool = False,
    yes: bool = False,
    stream: bool = False,
    interactive: bool = False,
    circuit_breaker_config: CircuitBreakerConfig | None = None,
) -> int:
    """Execute the real ORCA ADE multi-front orchestration.

    Returns 0 if every front ended MERGED, 1 if any front is FAILED /
    quarantined, 2 if the user declined (or could not be asked) to confirm
    the Flight Plan.
    """
    breaker_config = circuit_breaker_config or CircuitBreakerConfig()
    plan_dir = Path(plan_dir)
    resolved_repo = Path(repo_path).resolve() if repo_path else _repo_root(plan_dir)

    flight = gerar_plano_de_voo(
        plan_dir, profiles_path, harness=harness, harness_map=harness_map, interactive=interactive
    )
    flight_md = renderizar_plano_de_voo(flight)

    if not _confirm(flight_md, yes):
        return 2

    orca = _orca_dir(resolved_repo)
    state_path = orca / ".orca_state.json"
    front_names = [f["name"] for f in flight["fronts"]]

    if resume:
        if not state_path.exists():
            print(f"[ERRO] --resume pedido mas {state_path} nao existe.")
            return 1
        state = load_state(state_path)
        for name in front_names:
            if name not in state["fronts"]:
                state["fronts"][name] = {
                    "state": FrontState.PENDING.value,
                    "branch": None,
                    "commit_sha": None,
                    "pid": None,
                    "updated_at": time.time(),
                }
        save_state(state, state_path)
    else:
        if state_path.exists():
            print(
                f"[ERRO] {state_path} ja existe (execucao em andamento ou anterior). "
                "Use --resume ou limpe .orca/ manualmente."
            )
            return 1
        state = create_initial_state(front_names)
        save_state(state, state_path)

    _write_atomic(orca / "memory.md", render_memory_md(state))

    base_sha = _capture_base_sha(resolved_repo)
    merge_lock = threading.Lock()
    state_lock = threading.Lock()
    results: dict[str, str] = {}
    threads: list[threading.Thread] = []

    classifications = {c.front_name: c for c in classify_resume(state)} if resume else {}

    for front in flight["fronts"]:
        name = front["name"]
        action = classifications[name].action if name in classifications else ResumeAction.NO_ACTION

        if resume and action == ResumeAction.IGNORE:
            results[name] = FrontState.MERGED.value
            continue

        if resume and action == ResumeAction.READY_TO_MERGE:
            if interactive:
                _merge_and_finalize(name, resolved_repo, state_path, merge_lock, state_lock, results)
            else:
                threads.append(threading.Thread(
                    target=_merge_and_finalize,
                    args=(name, resolved_repo, state_path, merge_lock, state_lock, results),
                ))
            continue

        if resume and action in (ResumeAction.RETRY, ResumeAction.RESUME_RUNNING):
            stale_pid = state["fronts"][name].get("pid")
            purge_ok, detail = _quarantine_purge_if_stale(name, resolved_repo, stale_pid)
            if not purge_ok:
                print(
                    f"[ERRO] Frente '{name}': {detail}. Nao sera relancada nesta "
                    "execucao — limpe a worktree residual manualmente e rode "
                    "--resume novamente."
                )
                _set_front_state(state_path, state_lock, name, FrontState.FAILED)
                results[name] = f"FAILED(stale_purge:{detail})"
                continue

        if interactive:
            # Em modo interativo, executa sequencialmente para controle direto do usuario no terminal
            _dispatch_front(
                front, resolved_repo, state_path, state_lock, base_sha, merge_lock, breaker_config, results, stream=True, interactive=True
            )
        else:
            threads.append(threading.Thread(
                target=_dispatch_front,
                args=(front, resolved_repo, state_path, state_lock, base_sha, merge_lock, breaker_config, results, stream, False),
            ))

    if not interactive:
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    all_merged = all(v == FrontState.MERGED.value for v in results.values())
    return 0 if all_merged else 1
