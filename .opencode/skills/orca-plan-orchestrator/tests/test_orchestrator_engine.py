"""Real, non-mocked integration tests for orchestrator_engine.py.

Every test creates a real temporary git repository, runs the real
`executar_orquestracao` against a deterministic stub agent binary (never
a real LLM), and asserts on real git/filesystem state — no mocked git,
no mocked subprocess, no fabricated verdicts.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

ORCH_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ORCH_ROOT))

from scripts.orchestrator_engine import executar_orquestracao
from scripts.state_engine import (
    FrontState,
    create_initial_state,
    load_state,
    save_state,
)
from scripts.circuit_breaker import CircuitBreakerConfig


# ---------------------------------------------------------------------------
# Stub agent — deterministic test double driven by markers in the front's
# markdown content (which becomes the agent's prompt, exactly like a real
# harness invocation).
# ---------------------------------------------------------------------------

STUB_AGENT = '''\
import sys
import time
from pathlib import Path

prompt = sys.argv[1] if len(sys.argv) > 1 else ""
cwd = Path.cwd()

if "ORCA_TEST_FAIL" in prompt:
    sys.exit(1)

if "ORCA_TEST_SLEEP" in prompt:
    time.sleep(60)
    sys.exit(0)

env_seen = "yes" if (cwd / ".env").exists() else "no"
(cwd / "env_seen.txt").write_text(env_seen, encoding="utf-8")
(cwd / "deliverable.txt").write_text("front ok\\n", encoding="utf-8")
sys.exit(0)
'''

ECOSSISTEMA_STUB = (
    "import sys\n"
    "if len(sys.argv) > 1 and sys.argv[1] == 'audit':\n"
    "    sys.exit(0)\n"
    "sys.exit(0)\n"
)


def _run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)


@pytest.fixture
def orca_repo(tmp_path: Path) -> Path:
    """A real git repo with a stub agent + stub ecossistema.py audit gate."""
    repo = tmp_path / "repo"
    repo.mkdir()

    _run_git(["init"], repo)
    _run_git(["config", "user.email", "test@orca.local"], repo)
    _run_git(["config", "user.name", "ORCA Test"], repo)

    (repo / "README.md").write_text("# test repo\n", encoding="utf-8")
    (repo / "_stub_agent.py").write_text(STUB_AGENT, encoding="utf-8")
    (repo / "ecossistema.py").write_text(ECOSSISTEMA_STUB, encoding="utf-8")
    _run_git(["add", "."], repo)
    _run_git(["commit", "-m", "initial commit"], repo)

    return repo


def _make_profile(repo: Path) -> Path:
    profile = {
        "profiles": {
            "test-stub": {
                "binary": sys.executable,
                "auto_approve_flag": None,
                "prompt_mode": "positional",
                "prompt_flag": None,
                "model_flag": None,
                "default_model": None,
                "extra_flags": ["_stub_agent.py"],
            }
        }
    }
    path = repo / "harness_profiles.json"
    path.write_text(json.dumps(profile), encoding="utf-8")
    return path


def _make_plan(repo: Path, plan_name: str, fronts: dict[str, str]) -> Path:
    """fronts: {front_name: markdown_content}."""
    plan_dir = repo / "planos" / plan_name
    plan_dir.mkdir(parents=True)
    (plan_dir / "00-PROCESSO-E-DECISOES.md").write_text(
        f"# Processo\n\nPlano de teste: {plan_name}.\n", encoding="utf-8"
    )
    for i, (name, content) in enumerate(fronts.items(), start=1):
        (plan_dir / f"{i:02d}-{name}.md").write_text(content, encoding="utf-8")
    return plan_dir


def _run(repo, plan_dir, profiles_path, **kwargs):
    kwargs.setdefault("yes", True)
    return executar_orquestracao(
        plan_dir, profiles_path, harness="test-stub", repo_path=repo, **kwargs
    )


# ---------------------------------------------------------------------------
# 1. Happy path — 2 fronts in parallel, both merged
# ---------------------------------------------------------------------------

def test_happy_path_two_fronts_merge_in_parallel(orca_repo: Path) -> None:
    profiles = _make_profile(orca_repo)
    plan_dir = _make_plan(orca_repo, "demo", {
        "front-a": "# Front A\n\nEscreva deliverable.txt.\n",
        "front-b": "# Front B\n\nEscreva deliverable.txt tambem.\n",
    })

    exit_code = _run(orca_repo, plan_dir, profiles)

    assert exit_code == 0
    assert not (orca_repo / "wt-front-a").exists()
    assert not (orca_repo / "wt-front-b").exists()

    state = load_state(orca_repo / ".orca" / ".orca_state.json")
    assert state["fronts"]["front-a"]["state"] == "MERGED"
    assert state["fronts"]["front-b"]["state"] == "MERGED"

    for name in ("front-a", "front-b"):
        assert (orca_repo / ".orca" / "logs" / f"{name}.log").exists()
        report = json.loads((orca_repo / ".orca" / "reports" / f"{name}.json").read_text())
        assert report["state"] == "GATE_PASSED"

    branches = _run_git(["branch", "--list"], orca_repo).stdout
    assert "orca/front-a" not in branches
    assert "orca/front-b" not in branches

    status = _run_git(["status", "--porcelain"], orca_repo)
    assert status.returncode == 0


# ---------------------------------------------------------------------------
# 2. Agent failure — front quarantined, main untouched
# ---------------------------------------------------------------------------

def test_agent_failure_quarantines_worktree(orca_repo: Path) -> None:
    profiles = _make_profile(orca_repo)
    plan_dir = _make_plan(orca_repo, "demo", {
        "front-fail": "# Front Fail\n\nORCA_TEST_FAIL marker forces exit 1.\n",
    })

    exit_code = _run(orca_repo, plan_dir, profiles)

    assert exit_code == 1
    assert (orca_repo / "wt-front-fail").is_dir(), "quarantined worktree must survive"

    branches = _run_git(["branch", "--list", "orca/front-fail"], orca_repo).stdout
    assert "orca/front-fail" in branches

    assert not (orca_repo / "deliverable.txt").exists()

    state = load_state(orca_repo / ".orca" / ".orca_state.json")
    assert state["fronts"]["front-fail"]["state"] == "FAILED"


# ---------------------------------------------------------------------------
# 3. Resume — MERGED front is skipped, GATE_PASSED front is merged without
#    re-running the agent
# ---------------------------------------------------------------------------

def test_resume_skips_merged_and_merges_gate_passed(orca_repo: Path) -> None:
    profiles = _make_profile(orca_repo)
    plan_dir = _make_plan(orca_repo, "demo", {
        "already-merged": "# Already merged\n",
        "ready-to-merge": "# Ready to merge\n",
    })

    orca_dir = orca_repo / ".orca"
    orca_dir.mkdir()
    state_path = orca_dir / ".orca_state.json"
    state = create_initial_state(["already-merged", "ready-to-merge"])
    state["fronts"]["already-merged"]["state"] = FrontState.MERGED.value
    save_state(state, state_path)

    # ready-to-merge: real worktree with a real committed deliverable,
    # state says GATE_PASSED (simulating a crash between gate-pass and merge).
    wt_result = _run_git(
        ["worktree", "add", str(orca_repo / "wt-ready-to-merge"), "-b", "orca/ready-to-merge"],
        orca_repo,
    )
    assert wt_result.returncode == 0
    wt = orca_repo / "wt-ready-to-merge"
    (wt / "deliverable.txt").write_text("pre-merged content\n", encoding="utf-8")
    _run_git(["add", "."], wt)
    _run_git(["commit", "-m", "pre-existing gate-passed commit"], wt)

    state = load_state(state_path)
    state["fronts"]["ready-to-merge"]["state"] = FrontState.GATE_PASSED.value
    save_state(state, state_path)

    exit_code = _run(orca_repo, plan_dir, profiles, resume=True)

    assert exit_code == 0
    # already-merged: zero-cost skip, no worktree ever touched
    assert not (orca_repo / "wt-already-merged").exists()
    # ready-to-merge: merged for real, worktree purged
    assert (orca_repo / "deliverable.txt").read_text(encoding="utf-8") == "pre-merged content\n"
    assert not (orca_repo / "wt-ready-to-merge").exists()

    final_state = load_state(state_path)
    assert final_state["fronts"]["already-merged"]["state"] == "MERGED"
    assert final_state["fronts"]["ready-to-merge"]["state"] == "MERGED"


# ---------------------------------------------------------------------------
# 4. Circuit breaker kills a runaway agent without blocking the other front
# ---------------------------------------------------------------------------

def test_circuit_breaker_kills_runaway_front(orca_repo: Path) -> None:
    profiles = _make_profile(orca_repo)
    plan_dir = _make_plan(orca_repo, "demo", {
        "front-runaway": "# Runaway\n\nORCA_TEST_SLEEP marker sleeps 60s.\n",
        "front-ok": "# OK\n\nWrites deliverable normally.\n",
    })

    t0 = time.time()
    exit_code = _run(
        orca_repo, plan_dir, profiles,
        circuit_breaker_config=CircuitBreakerConfig(
            max_execution_time_seconds=3.0, idle_heartbeat_seconds=3.0,
        ),
    )
    elapsed = time.time() - t0

    assert exit_code == 1
    assert elapsed < 30, "circuit breaker must kill the runaway process quickly"

    state = load_state(orca_repo / ".orca" / ".orca_state.json")
    assert state["fronts"]["front-runaway"]["state"] == "FAILED"
    assert state["fronts"]["front-ok"]["state"] == "MERGED"

    report = json.loads((orca_repo / ".orca" / "reports" / "front-runaway.json").read_text())
    assert report["circuit_breaker"] in ("TIMEOUT_TOTAL", "TIMEOUT_IDLE")


# ---------------------------------------------------------------------------
# 5. .env propagation into the worktree + git-exclude, never merged into main
# ---------------------------------------------------------------------------

def test_env_propagation_and_exclusion(orca_repo: Path) -> None:
    (orca_repo / ".env").write_text("SECRET=shh\n", encoding="utf-8")

    profiles = _make_profile(orca_repo)
    plan_dir = _make_plan(orca_repo, "demo", {
        "front-env": "# Env front\n\nChecks .env visibility.\n",
    })

    exit_code = _run(orca_repo, plan_dir, profiles)
    assert exit_code == 0

    # Merged content proves the agent SAW .env inside its worktree.
    assert (orca_repo / "env_seen.txt").read_text(encoding="utf-8").strip() == "yes"
    # .env itself must never reach main.
    assert not (orca_repo / "wt-front-env").exists()
    show = _run_git(["show", "HEAD:.env"], orca_repo)
    assert show.returncode != 0, ".env must never be committed/merged"


# ---------------------------------------------------------------------------
# 6. Approval gate refuses without --yes when stdin is not a TTY (pytest)
# ---------------------------------------------------------------------------

def test_confirmation_required_without_yes_aborts_cleanly(orca_repo: Path) -> None:
    profiles = _make_profile(orca_repo)
    plan_dir = _make_plan(orca_repo, "demo", {
        "front-a": "# Front A\n",
    })

    before = _run_git(["worktree", "list"], orca_repo).stdout

    exit_code = executar_orquestracao(
        plan_dir, profiles, harness="test-stub", repo_path=orca_repo, yes=False,
    )

    assert exit_code == 2
    after = _run_git(["worktree", "list"], orca_repo).stdout
    assert before == after, "no worktree may be created when confirmation is refused"
    assert not (orca_repo / ".orca" / ".orca_state.json").exists()


# ---------------------------------------------------------------------------
# 7. Hardened resume: a real orphaned agent process is killed before the
#    stale worktree is purged and the front is re-dispatched from scratch.
# ---------------------------------------------------------------------------

def test_resume_running_kills_orphan_pid_before_retry(orca_repo: Path) -> None:
    profiles = _make_profile(orca_repo)
    plan_dir = _make_plan(orca_repo, "demo", {
        "front-orphan": "# Front orphan\n\nWrites deliverable normally.\n",
    })

    orca_dir = orca_repo / ".orca"
    orca_dir.mkdir()
    state_path = orca_dir / ".orca_state.json"
    state = create_initial_state(["front-orphan"])
    save_state(state, state_path)

    wt_result = _run_git(
        ["worktree", "add", str(orca_repo / "wt-front-orphan"), "-b", "orca/front-orphan"],
        orca_repo,
    )
    assert wt_result.returncode == 0
    wt = orca_repo / "wt-front-orphan"

    # A REAL orphan process, as if the orchestrator had crashed while this
    # front's harness subprocess kept running (Popen ties nothing to parent
    # lifetime). Its pid is recorded in state exactly like _dispatch_front
    # would have done right after spawning it.
    orphan = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"], cwd=wt)

    state = load_state(state_path)
    state["fronts"]["front-orphan"]["state"] = FrontState.RUNNING.value
    state["fronts"]["front-orphan"]["pid"] = orphan.pid
    save_state(state, state_path)

    try:
        exit_code = _run(orca_repo, plan_dir, profiles, resume=True)

        assert orphan.poll() is not None, "orphan process must be killed before retry, not left running"
        assert exit_code == 0

        final_state = load_state(state_path)
        assert final_state["fronts"]["front-orphan"]["state"] == "MERGED"
        assert not (orca_repo / "wt-front-orphan").exists()
    finally:
        if orphan.poll() is None:
            orphan.kill()
            orphan.wait(timeout=10)


# ---------------------------------------------------------------------------
# 8. Hardened resume: when the stale worktree genuinely can't be purged
#    (still locked), the front is marked FAILED with a clear reason instead
#    of being silently re-dispatched into a confusing worktree-exists error.
# ---------------------------------------------------------------------------

def test_stale_purge_failure_marks_failed_without_confusing_retry(orca_repo: Path) -> None:
    profiles = _make_profile(orca_repo)
    plan_dir = _make_plan(orca_repo, "demo", {
        "front-locked": "# Front locked\n",
    })

    orca_dir = orca_repo / ".orca"
    orca_dir.mkdir()
    state_path = orca_dir / ".orca_state.json"
    state = create_initial_state(["front-locked"])
    state["fronts"]["front-locked"]["state"] = FrontState.FAILED.value
    save_state(state, state_path)

    wt_result = _run_git(
        ["worktree", "add", str(orca_repo / "wt-front-locked"), "-b", "orca/front-locked"],
        orca_repo,
    )
    assert wt_result.returncode == 0

    # git's own mechanism for "this worktree must not be removed right now" —
    # a single --force (what purgar_worktree issues) must not override a lock.
    lock_result = _run_git(["worktree", "lock", str(orca_repo / "wt-front-locked")], orca_repo)
    assert lock_result.returncode == 0

    exit_code = _run(orca_repo, plan_dir, profiles, resume=True)

    assert exit_code == 1
    final_state = load_state(state_path)
    assert final_state["fronts"]["front-locked"]["state"] == "FAILED"
    # Left in place for manual inspection — not blindly re-created.
    assert (orca_repo / "wt-front-locked").exists()

    # Cleanup for a tidy tmp_path teardown.
    _run_git(["worktree", "unlock", str(orca_repo / "wt-front-locked")], orca_repo)
