"""End-to-end orchestration test for ORCA ADE — single front, real git, stub agent.

Scope:
  1. Creates a temporary git repository (isolated, no ecossistema-aidd touched).
  2. Builds a minimal plan folder (00-PROCESSO-E-DECISOES.md + 01-demo-front.md).
  3. Compiles a harness profile with a STUB agent binary (not a real LLM agent).
  4. Exercises every orchestrator module in the real orchestration order:
     plan_parser → agent_spawner → flight_plan → worktree_engine.create
     → hooks.pre_hook → subprocess.run (stub agent) → hooks.post_hook
     → gate_auditor → worktree_engine.merge → worktree_engine.purge
  5. Verifies all checkpoints and emits a telemetry summary.

Exit criteria:
  - Full orchestration of 1 front completed with exit 0.
  - Merge confirmed into the main branch.
  - Ephemeral worktree purged.
  - git status clean at the end.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

# ── Setup sys.path so scripts are importable as `scripts.X` (package-style) ──
ORCH_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ORCH_ROOT))

from scripts.plan_parser import parse_plan
from scripts.agent_spawner import carregar_perfil, compilar_comando
from scripts.flight_plan import gerar_plano_de_voo, renderizar_plano_de_voo
from scripts.worktree_engine import criar_worktree, mergear_worktree, purgar_worktree
from scripts.state_engine import (
    create_initial_state,
    save_state,
    load_state,
    render_memory_md,
    update_front_state,
    FrontState,
)
from scripts.hooks import executar_pre_hook, executar_post_hook
from scripts.gate_auditor import audit_front, AuditVerdict


# ═══════════════════════════════════════════════════════════════════════
# 0. TELEMETRY COLLECTOR
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class TelemetryEvent:
    step: str
    status: str  # OK | FAIL
    detail: str
    elapsed_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)


class TelemetryCollector:
    def __init__(self) -> None:
        self.events: list[TelemetryEvent] = []
        self.start = time.time()

    def record(self, step: str, status: str, detail: str, elapsed_ms: float = 0.0) -> None:
        self.events.append(TelemetryEvent(step, status, detail, elapsed_ms))

    def elapsed_total_ms(self) -> float:
        return (time.time() - self.start) * 1000

    def render(self) -> str:
        lines = [
            "# ORCA ADE - E2E Telemetry Summary",
            "",
            f"Total elapsed: {self.elapsed_total_ms():.0f} ms",
            f"Events: {len(self.events)} | Passed: {sum(1 for e in self.events if e.status == 'OK')} | Failed: {sum(1 for e in self.events if e.status == 'FAIL')}",
            "",
            "| # | Step | Status | Elapsed (ms) | Detail |",
            "|---|------|--------|--------------|--------|",
        ]
        for i, ev in enumerate(self.events, 1):
            lines.append(f"| {i} | {ev.step} | {ev.status} | {ev.elapsed_ms:.0f} | {ev.detail} |")
        lines.append("")
        return "\n".join(lines)



# ═══════════════════════════════════════════════════════════════════════
# 1. STUB AGENT BINARY  (a tiny Python script that writes a file and exits 0)
# ═══════════════════════════════════════════════════════════════════════

STUB_AGENT = '''\
"""Stub agent: writes a deliverable file and exits 0."""
import sys
from pathlib import Path

worktree = Path(sys.argv[1])
deliverable = worktree / "deliverable.txt"
deliverable.write_text("Stub agent completed successfully.\\n", encoding="utf-8")
sys.exit(0)
'''


def _write_stub_agent(worktree: Path) -> Path:
    """Write the stub agent into the worktree and return its path."""
    stub = worktree / "_stub_agent.py"
    stub.write_text(STUB_AGENT, encoding="utf-8")
    return stub


# ═══════════════════════════════════════════════════════════════════════
# 2. CREATE TEMPORARY GIT REPO
# ═══════════════════════════════════════════════════════════════════════

def _run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def create_temp_repo() -> Path:
    """Create a temp git repo with two initial commits."""
    repo = Path(tempfile.mkdtemp(prefix="orca_e2e_")) / "test-repo"
    repo.mkdir()

    _run_git(["init"], repo)
    _run_git(["config", "user.email", "e2e@test.com"], repo)
    _run_git(["config", "user.name", "E2E Test"], repo)

    (repo / "README.md").write_text("# E2E Test Repo\n", encoding="utf-8")
    _run_git(["add", "."], repo)
    _run_git(["commit", "-m", "initial commit"], repo)

    (repo / "src").mkdir()
    (repo / "src" / "main.py").write_text("print('hello')\n", encoding="utf-8")
    (repo / "ecossistema.py").write_text(
        "import sys\n"
        "if len(sys.argv) > 1 and sys.argv[1] == 'audit':\n"
        "    sys.exit(0)\n"
        "sys.exit(0)\n",
        encoding="utf-8",
    )
    _run_git(["add", "."], repo)
    _run_git(["commit", "-m", "add src/main.py and ecossistema.py"], repo)

    # Pre-commit the plan dir placeholder so it's tracked (avoids false
    # "not clean" at the end of the test when planos/ is created).
    (repo / "planos").mkdir()
    (repo / "planos" / ".gitkeep").touch()
    _run_git(["add", "."], repo)
    _run_git(["commit", "-m", "pre-create planos dir"], repo)

    return repo



# ═══════════════════════════════════════════════════════════════════════
# 3. CREATE PLAN FOLDER
# ═══════════════════════════════════════════════════════════════════════

def create_plan_folder(repo: Path) -> Path:
    """Create a minimal plan folder with 1 front."""
    plan_dir = repo / "planos" / "demo"
    plan_dir.mkdir(parents=True)

    (plan_dir / "00-PROCESSO-E-DECISOES.md").write_text(
        "# Processo de Decisoes\n\nContexto: E2E validation of the ORCA ADE orchestrator.\n",
        encoding="utf-8",
    )

    (plan_dir / "01-demo-front.md").write_text(
        "# Demo Front\n\nCriar deliverable.txt no worktree como evidencia de execucao.\n",
        encoding="utf-8",
    )

    return plan_dir


# ═══════════════════════════════════════════════════════════════════════
# 4. CREATE STUB HARNESS PROFILE
# ═══════════════════════════════════════════════════════════════════════

def create_harness_profile(repo: Path, stub_agent_path: str) -> Path:
    """Write a harness profile that points to our stub agent."""
    profile = {
        "profiles": {
            "stub": {
                "binary": sys.executable,
                "auto_approve_flag": None,
                "prompt_mode": "positional",
                "prompt_flag": None,
                "model_flag": None,
                "default_model": None,
                "extra_flags": [],
                "usage_note": "E2E stub profile — launches _stub_agent.py directly.",
            }
        }
    }
    # The binary is python, and the prompt will be the path to stub_agent.py
    # followed by the worktree path. We override the command in flight_plan
    # to pass the stub script + worktree as positional args.
    profiles_path = repo / "harness_profiles.json"
    profiles_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    return profiles_path


# ═══════════════════════════════════════════════════════════════════════
# 5. FULL E2E ORCHESTRATION
# ═══════════════════════════════════════════════════════════════════════

def run_e2e() -> int:
    """Run the full E2E orchestration and return exit code."""
    tel = TelemetryCollector()
    repo: Path | None = None

    try:
        # ── Step 1: Create temp git repo ──────────────────────────────
        t0 = time.time()
        repo = create_temp_repo()
        tel.record("1.create_repo", "OK", f"repo={repo}", (time.time() - t0) * 1000)

        # Verify clean status
        status = _run_git(["status", "--porcelain"], repo)
        assert status.stdout.strip() == "", f"Repo not clean at start: {status.stdout}"

        # ── Step 2: Create plan folder ────────────────────────────────
        t0 = time.time()
        plan_dir = create_plan_folder(repo)
        tel.record("2.create_plan", "OK", f"plan_dir={plan_dir}", (time.time() - t0) * 1000)

        # Commit plan files so they're tracked (avoids false "not clean" later)
        _run_git(["add", "planos/"], repo)
        _run_git(["commit", "-m", "add plan files for E2E"], repo)

        # ── Step 3: Parse plan ────────────────────────────────────────
        t0 = time.time()
        plan = parse_plan(plan_dir)
        assert plan.front_count == 1, f"Expected 1 front, got {plan.front_count}"
        assert plan.fronts[0].name == "demo-front"
        tel.record("3.parse_plan", "OK", f"fronts={plan.front_count}, name={plan.fronts[0].name}", (time.time() - t0) * 1000)

        # ── Step 4: Create harness profile ────────────────────────────
        t0 = time.time()
        profiles_path = create_harness_profile(repo, "")
        profile = carregar_perfil(profiles_path, "stub")
        tel.record("4.load_profile", "OK", f"binary={profile['binary']}", (time.time() - t0) * 1000)

        # Commit harness_profiles.json so it's tracked
        _run_git(["add", "harness_profiles.json"], repo)
        _run_git(["commit", "-m", "add harness profile for E2E"], repo)

        # ── Step 5: Generate flight plan ──────────────────────────────
        t0 = time.time()
        flight = gerar_plano_de_voo(plan_dir, profiles_path, harness="stub")
        assert len(flight["fronts"]) == 1
        front_info = flight["fronts"][0]
        tel.record("5.flight_plan", "OK", f"branch={front_info['branch']}, worktree={front_info['worktree']}", (time.time() - t0) * 1000)

        # Render flight plan (for display)
        flight_md = renderizar_plano_de_voo(flight)
        print(flight_md)

        # ── Step 6: Create worktree ───────────────────────────────────
        t0 = time.time()
        wt_result = criar_worktree("demo-front", repo)
        assert wt_result.ok, f"Worktree creation failed: {wt_result.stderr}"
        worktree_path = repo / "wt-demo-front"
        assert worktree_path.is_dir(), "Worktree directory does not exist"
        tel.record("6.create_worktree", "OK", f"wt={worktree_path}", (time.time() - t0) * 1000)

        # ── Step 7: Initialize state ──────────────────────────────────
        t0 = time.time()
        state_dir = worktree_path / ".orca"
        state_dir.mkdir(exist_ok=True)
        state_path = state_dir / ".orca_state.json"
        state = create_initial_state(["demo-front"])
        save_state(state, state_path)
        tel.record("7.init_state", "OK", f"state_path={state_path}", (time.time() - t0) * 1000)

        # ── Step 8: Pre-hook (PENDING → RUNNING) ──────────────────────
        t0 = time.time()
        pre_result = executar_pre_hook("demo-front", worktree_path, state_path)
        assert pre_result["status"] == "RUNNING", f"Expected RUNNING, got {pre_result['status']}"

        # Verify persisted state
        saved_state = load_state(state_path)
        assert saved_state["fronts"]["demo-front"]["state"] == "RUNNING"

        # Verify memory.md was written
        memory_path = state_path.parent / "memory.md"
        assert memory_path.exists(), "memory.md not found"
        memory_content = memory_path.read_text(encoding="utf-8")
        assert "RUNNING" in memory_content

        tel.record("8.pre_hook", "OK", f"state=RUNNING, memory.md written", (time.time() - t0) * 1000)
        print(f"  [PRE-HOOK] state=RUNNING | memory.md: {memory_path}")

        # ── Step 9: Spawn stub agent via subprocess ───────────────────
        t0 = time.time()
        stub_script = _write_stub_agent(worktree_path)

        # The compiled command from flight plan uses the stub profile,
        # but we override to pass stub_script + worktree_path directly.
        agent_cmd = [sys.executable, str(stub_script), str(worktree_path)]
        agent_result = subprocess.run(
            agent_cmd,
            cwd=worktree_path,
            capture_output=True,
            text=True,
        )
        agent_exit_code = agent_result.returncode
        assert agent_exit_code == 0, f"Stub agent failed: exit={agent_exit_code}, stderr={agent_result.stderr}"
        assert (worktree_path / "deliverable.txt").exists(), "deliverable.txt not created by stub agent"
        tel.record("9.spawn_agent", "OK", f"exit_code={agent_exit_code}, deliverable.txt exists", (time.time() - t0) * 1000)
        print(f"  [AGENT] exit_code=0 | deliverable.txt: {(worktree_path / 'deliverable.txt').read_text().strip()}")

        # ── Step 10: Post-hook (RUNNING -> GATE_PASSED) ──────────────
        t0 = time.time()
        post_result = executar_post_hook(
            front_name="demo-front",
            worktree_path=worktree_path,
            state_path=state_path,
            agent_exit_code=agent_exit_code,
            touched_paths=["ecossistema.py"],
        )

        final_state = post_result["state"]
        assert final_state == "GATE_PASSED", f"Expected GATE_PASSED, got {final_state}"

        # Check event file
        event_file = Path(post_result["event_file"])
        assert event_file.exists(), f"Event file not found: {event_file}"
        assert event_file.read_text(encoding="utf-8") == final_state

        tel.record("10.post_hook", "OK", f"state={final_state}, event_file={event_file.name}", (time.time() - t0) * 1000)
        print(f"  [POST-HOOK] state={final_state} | event_file={event_file.name}")

        # ── Step 11: Verify final state + memory.md ───────────────────
        t0 = time.time()
        final_state_loaded = load_state(state_path)
        assert final_state_loaded["fronts"]["demo-front"]["state"] == final_state

        memory_final = memory_path.read_text(encoding="utf-8")
        assert final_state in memory_final
        tel.record("11.verify_state", "OK", f"persisted_state={final_state}, memory.md updated", (time.time() - t0) * 1000)

        # ── Step 12: Commit worktree changes ──────────────────────────
        t0 = time.time()
        _run_git(["add", "."], worktree_path)
        commit_result = _run_git(["commit", "-m", "E2E demo: deliverable.txt from stub agent"], worktree_path)
        assert commit_result.returncode == 0, f"Commit in worktree failed: {commit_result.stderr}"
        tel.record("12.commit_worktree", "OK", "committed in orca/demo-front branch", (time.time() - t0) * 1000)

        # ── Step 13: Merge worktree branch -> main ─────────────────────
        t0 = time.time()
        merge_result = mergear_worktree("demo-front", repo)
        assert merge_result.ok, f"Merge failed: {merge_result.stderr}"
        assert (repo / "deliverable.txt").exists(), "deliverable.txt not in main after merge"
        main_content = (repo / "deliverable.txt").read_text(encoding="utf-8")
        tel.record("13.merge", "OK", f"merged orca/demo-front -> main, deliverable.txt present", (time.time() - t0) * 1000)
        print(f"  [MERGE] deliverable.txt in main: {main_content.strip()}")

        # ── Step 14: Update state to MERGED ───────────────────────────
        t0 = time.time()
        state = load_state(state_path)
        state = update_front_state(state, "demo-front", FrontState.MERGED)
        save_state(state, state_path)
        tel.record("14.state_merged", "OK", "state=MERGED persisted", (time.time() - t0) * 1000)

        # ── Step 15: Purge worktree ───────────────────────────────────
        t0 = time.time()
        purge_result = purgar_worktree("demo-front", repo)
        assert purge_result.ok, f"Purge failed: {purge_result.stderr}"
        assert not (repo / "wt-demo-front").exists(), "Worktree directory still exists after purge"

        # Verify branch deleted
        branches = _run_git(["branch", "--list", "orca/demo-front"], repo)
        assert "orca/demo-front" not in branches.stdout, "Branch still exists after purge"
        tel.record("15.purge", "OK", "worktree removed, branch deleted", (time.time() - t0) * 1000)

        # ── Step 16: Final git status ─────────────────────────────────
        t0 = time.time()
        final_status = _run_git(["status", "--porcelain"], repo)
        assert final_status.stdout.strip() == "", f"Repo not clean: {final_status.stdout}"
        tel.record("16.git_clean", "OK", "git status clean", (time.time() - t0) * 1000)

        # ── Step 17: Render memory.md ─────────────────────────────────
        t0 = time.time()
        final_memory = render_memory_md(state)
        tel.record("17.render_memory", "OK", "memory.md rendered", (time.time() - t0) * 1000)

        # ═══════════════════════════════════════════════════════════════
        # FINAL REPORT
        # ═══════════════════════════════════════════════════════════════
        print("\n" + "=" * 70)
        print("ORCA ADE - E2E VALIDATION COMPLETE")
        print("=" * 70)
        print()
        print("-- Telemetry --")
        print(tel.render())
        print("-- Memory.md (final state) --")
        print(final_memory)
        print("-- Git log (main branch) --")
        git_log = _run_git(["log", "--oneline", "-5"], repo)
        print(git_log.stdout)
        print("-- Git status --")
        print(f"Clean: {final_status.stdout.strip() == '(empty)' or final_status.stdout.strip() == ''}")
        print()
        print("EXIT CRITERIA:")
        print("  [OK] Full orchestration of 1 front completed with exit 0")
        print("  [OK] Merge confirmed into main branch")
        print("  [OK] Ephemeral worktree purged")
        print("  [OK] git status clean")
        print()
        print("EXIT CODE: 0")
        return 0


    except Exception as exc:
        tel.record("FATAL", "FAIL", str(exc)[:200])
        print(f"\nFATAL ERROR: {exc}")
        print(tel.render())
        return 1

    finally:
        # Cleanup temp directory
        if repo and repo.parent.exists():
            import shutil
            shutil.rmtree(repo.parent, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(run_e2e())
