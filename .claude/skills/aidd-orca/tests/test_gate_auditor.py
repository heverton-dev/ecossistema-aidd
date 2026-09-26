# -*- coding: utf-8 -*-
"""Tests for gate_auditor.py — real verification commands in self-contained repos.

Each scenario creates a minimal directory structure that mirrors the
ecossistema-aidd layout, so gate_auditor can resolve and execute real
subprocess commands without symlinks (Windows-compatible, no admin needed).

Scenario A (pass): minimal ecossistema.py audit exits 0, tool pytest exits 0.
Scenario B (fail): deliberately broken pytest test detected by gate_auditor.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from gate_auditor import audit_front, resolve_commands, AuditVerdict


# ---------------------------------------------------------------------------
# Minimal ecossistema.py that the test repos will use (always exit 0)
# ---------------------------------------------------------------------------
_MINIMAL_ECOSSISTEMA = '''\
"""Minimal ecossistema.py for gate_auditor tests."""
import sys

def cmd_audit():
    return 0

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "audit":
        sys.exit(cmd_audit())
    sys.exit(0)

if __name__ == "__main__":
    main()
'''

# A gate script that exits 0
_MINIMAL_GATE_PASSING = '''\
"""Minimal passing gate."""
import sys
if __name__ == "__main__":
    sys.exit(0)
'''

# A passing test file
_PASSING_TEST = '''\
def test_always_passes():
    assert 1 + 1 == 2
'''

# A deliberately failing test file
_FAILING_TEST = '''\
def test_this_will_fail():
    assert False, "Deliberate failure for gate_auditor test"
'''


def _make_minimal_repo(base: Path, *, include_failing_test: bool = False) -> Path:
    """Create a minimal self-contained directory structure for gate_auditor.

    Structure:
        <base>/
            ecossistema.py          # always exit 0 on audit
            gates/
                G_MINIMAL.py        # minimal gate
            tools/
                aidd-master/
                    pytest.ini
                    test_sample.py  # passing or failing
    """
    repo = base / "test-repo"
    repo.mkdir(parents=True, exist_ok=True)

    # Root ecossistema.py
    (repo / "ecossistema.py").write_text(_MINIMAL_ECOSSISTEMA)

    # gates/
    gates_dir = repo / "gates"
    gates_dir.mkdir()
    (gates_dir / "G_MINIMAL.py").write_text(_MINIMAL_GATE_PASSING)

    # tools/aidd-master/ with pytest.ini and a test
    tool_dir = repo / "tools" / "aidd-master"
    tool_dir.mkdir(parents=True)
    (tool_dir / "pytest.ini").write_text(
        "[pytest]\n"
        "testpaths = .\n"
        "python_files = test_*.py\n"
        "python_classes = Test*\n"
        "python_functions = test_*\n"
    )
    if include_failing_test:
        (tool_dir / "test_sample.py").write_text(_FAILING_TEST)
    else:
        (tool_dir / "test_sample.py").write_text(_PASSING_TEST)

    return repo


# ---------------------------------------------------------------------------
# Unit: resolve_commands (no filesystem needed)
# ---------------------------------------------------------------------------

class TestResolveCommands:
    def test_tool_paths_resolve(self):
        tools, root = resolve_commands(["tools/aidd-master/src/foo.py"])
        assert tools == {"aidd-master"}
        assert not root

    def test_multiple_tools(self):
        tools, root = resolve_commands([
            "tools/aidd-master/src/foo.py",
            "tools/aidd-forge/src/bar.py",
        ])
        assert tools == {"aidd-master", "aidd-forge"}
        assert not root

    def test_root_scoped_triggers_audit(self):
        tools, root = resolve_commands(["gates/G_SEGREDOS.py"])
        assert not tools
        assert root

    def test_root_file_triggers_audit(self):
        tools, root = resolve_commands(["ecossistema.py"])
        assert not tools
        assert root

    def test_mixed_paths(self):
        tools, root = resolve_commands([
            "tools/aidd-master/src/x.py",
            "gates/G_SEGREDOS.py",
        ])
        assert tools == {"aidd-master"}
        assert root

    def test_no_relevant_paths(self):
        tools, root = resolve_commands(["docs/readme.md"])
        assert not tools
        assert not root

    def test_windows_style_paths(self):
        tools, root = resolve_commands(["tools\\aidd-forge\\src\\bar.py"])
        assert tools == {"aidd-forge"}
        assert not root


# ---------------------------------------------------------------------------
# Integration: Scenario A — pass (all commands exit 0)
# ---------------------------------------------------------------------------

class TestScenarioA_Pass:
    """All verification commands return exit 0."""

    def test_root_audit_passes(self, tmp_path: Path):
        repo = _make_minimal_repo(tmp_path)
        verdict = audit_front(repo, "front-audit-pass", ["gates/G_MINIMAL.py"])

        print(f"\n[Scenario A - Root Audit]")
        for cmd in verdict.commands:
            print(f"  Command: {cmd.command}")
            print(f"  CWD: {cmd.cwd}")
            print(f"  Exit code: {cmd.returncode}")
            print(f"  Passed: {cmd.passed}")
        print(f"  Aggregated verdict: {'APPROVED' if verdict.approved else 'BLOCKED'}")

        assert len(verdict.commands) >= 1, "Should have run at least the root audit"
        assert verdict.commands[0].passed, (
            f"Root audit should pass. stderr: {verdict.commands[0].stderr[:500]}"
        )
        assert verdict.approved

    def test_tool_pytest_passes(self, tmp_path: Path):
        repo = _make_minimal_repo(tmp_path)
        verdict = audit_front(repo, "front-tool-pass", ["tools/aidd-master/src/x.py"])

        print(f"\n[Scenario A - Tool Pytest]")
        for cmd in verdict.commands:
            print(f"  Command: {cmd.command}")
            print(f"  CWD: {cmd.cwd}")
            print(f"  Exit code: {cmd.returncode}")
            print(f"  Passed: {cmd.passed}")
        print(f"  Aggregated verdict: {'APPROVED' if verdict.approved else 'BLOCKED'}")

        assert len(verdict.commands) == 1, "Should have run exactly one pytest"
        assert verdict.commands[0].passed, (
            f"aidd-master pytest should pass. stderr: {verdict.commands[0].stderr[:500]}"
        )
        assert verdict.approved


# ---------------------------------------------------------------------------
# Integration: Scenario B — fail (broken test detected)
# ---------------------------------------------------------------------------

class TestScenarioB_Fail:
    """Deliberately broken test causes gate_auditor to detect failure."""

    def test_broken_pytest_detected(self, tmp_path: Path):
        repo = _make_minimal_repo(tmp_path, include_failing_test=True)
        verdict = audit_front(repo, "front-tool-fail", ["tools/aidd-master/src/x.py"])

        print(f"\n[Scenario B - Broken Pytest]")
        for cmd in verdict.commands:
            print(f"  Command: {cmd.command}")
            print(f"  CWD: {cmd.cwd}")
            print(f"  Exit code: {cmd.returncode}")
            print(f"  Passed: {cmd.passed}")
            if cmd.stderr:
                lines = cmd.stderr.strip().splitlines()
                for line in lines[-5:]:
                    print(f"    stderr: {line}")
        print(f"  Aggregated verdict: {'APPROVED' if verdict.approved else 'BLOCKED'}")

        assert len(verdict.commands) == 1, "Should have run exactly one pytest"
        assert not verdict.commands[0].passed, (
            f"Broken test should cause failure. Exit code: {verdict.commands[0].returncode}"
        )
        assert verdict.commands[0].returncode != 0
        assert not verdict.approved, "Verdict should be BLOCKED"

    def test_multiple_commands_one_fails(self, tmp_path: Path):
        """Front touches root + tool; root passes but tool fails -> BLOCKED."""
        repo = _make_minimal_repo(tmp_path, include_failing_test=True)
        verdict = audit_front(
            repo,
            "front-mixed-fail",
            ["gates/G_MINIMAL.py", "tools/aidd-master/src/x.py"],
        )

        print(f"\n[Scenario B - Mixed: root pass + tool fail]")
        for cmd in verdict.commands:
            print(f"  Command: {cmd.command}")
            print(f"  CWD: {cmd.cwd}")
            print(f"  Exit code: {cmd.returncode}")
            print(f"  Passed: {cmd.passed}")
        print(f"  Aggregated verdict: {'APPROVED' if verdict.approved else 'BLOCKED'}")

        assert len(verdict.commands) == 2, "Should run both root audit and tool pytest"
        assert verdict.commands[0].passed, "Root audit should still pass"
        assert not verdict.commands[1].passed, "Tool pytest should detect broken test"
        assert not verdict.approved
