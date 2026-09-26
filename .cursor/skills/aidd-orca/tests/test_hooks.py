"""Unit tests for hooks.py — pre-hook and post-hook logic."""

from __future__ import annotations

import json

import pytest

from scripts.hooks import executar_post_hook, executar_pre_hook
from scripts.state_engine import FrontState, create_initial_state, save_state


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_state_file(state_path, front_names):
    state = create_initial_state(front_names)
    save_state(state, state_path)
    return state


# ---------------------------------------------------------------------------
# executar_pre_hook
# ---------------------------------------------------------------------------

class TestPreHook:
    def test_raises_when_worktree_missing(self, tmp_path):
        state_path = tmp_path / ".orca_state.json"
        _make_state_file(state_path, ["front-a"])
        with pytest.raises(FileNotFoundError):
            executar_pre_hook("front-a", tmp_path / "no_such_dir", state_path)

    def test_transitions_to_running(self, tmp_path):
        wt = tmp_path / "worktree"
        wt.mkdir()
        state_path = tmp_path / ".orca_state.json"
        _make_state_file(state_path, ["f1"])

        result = executar_pre_hook("f1", wt, state_path)

        assert result["status"] == "RUNNING"
        assert result["front"] == "f1"
        assert isinstance(result["timestamp"], float)

        # persisted state reflects RUNNING
        with open(state_path) as f:
            saved = json.load(f)
        assert saved["fronts"]["f1"]["state"] == "RUNNING"

    def test_memory_md_written(self, tmp_path):
        wt = tmp_path / "worktree"
        wt.mkdir()
        state_path = tmp_path / ".orca_state.json"
        _make_state_file(state_path, ["f1"])

        executar_pre_hook("f1", wt, state_path)

        memory = state_path.parent / "memory.md"
        assert memory.exists()
        content = memory.read_text(encoding="utf-8")
        assert "f1" in content
        assert "RUNNING" in content


# ---------------------------------------------------------------------------
# executar_post_hook
# ---------------------------------------------------------------------------

class TestPostHook:
    def test_failed_on_nonzero_exit(self, tmp_path):
        wt = tmp_path / "worktree"
        wt.mkdir()
        state_path = tmp_path / ".orca_state.json"
        _make_state_file(state_path, ["f1"])

        # pre-hook first so state is RUNNING
        executar_pre_hook("f1", wt, state_path)

        result = executar_post_hook("f1", wt, state_path, agent_exit_code=1, touched_paths=[])

        assert result["state"] == "FAILED"
        assert result["front"] == "f1"

    def test_gate_passed_when_audit_approves(self, tmp_path):
        wt = tmp_path / "worktree"
        wt.mkdir()
        state_path = tmp_path / ".orca_state.json"
        _make_state_file(state_path, ["f1"])
        executar_pre_hook("f1", wt, state_path)

        # Touch a path under tools/aidd-forge — audit_front will try to
        # run pytest there.  In the test worktree no such dir exists, so
        # the verdict.commands list is empty → approved=False → FAILED.
        # We therefore monkeypatch audit_front to return approved=True.
        from unittest.mock import patch

        from scripts.gate_auditor import AuditVerdict

        fake_verdict = AuditVerdict(front_id="f1")
        fake_verdict.commands = []  # empty + we override .approved

        class _ApprovedVerdict:
            approved = True

        with patch("scripts.hooks.audit_front", return_value=_ApprovedVerdict()):
            result = executar_post_hook("f1", wt, state_path, agent_exit_code=0, touched_paths=["x.py"])

        assert result["state"] == "GATE_PASSED"

    def test_gate_failed_when_audit_rejects(self, tmp_path):
        wt = tmp_path / "worktree"
        wt.mkdir()
        state_path = tmp_path / ".orca_state.json"
        _make_state_file(state_path, ["f1"])
        executar_pre_hook("f1", wt, state_path)

        from unittest.mock import patch

        class _RejectedVerdict:
            approved = False

        with patch("scripts.hooks.audit_front", return_value=_RejectedVerdict()):
            result = executar_post_hook("f1", wt, state_path, agent_exit_code=0, touched_paths=["x.py"])

        assert result["state"] == "FAILED"

    def test_event_file_created(self, tmp_path):
        wt = tmp_path / "worktree"
        wt.mkdir()
        state_path = tmp_path / ".orca_state.json"
        _make_state_file(state_path, ["f1"])
        executar_pre_hook("f1", wt, state_path)

        from unittest.mock import patch

        class _ApprovedVerdict:
            approved = True

        with patch("scripts.hooks.audit_front", return_value=_ApprovedVerdict()):
            result = executar_post_hook("f1", wt, state_path, agent_exit_code=0, touched_paths=[])

        event_path = wt / ".orca" / "events" / "f1.done"
        assert event_path.exists()
        assert event_path.read_text(encoding="utf-8") == "GATE_PASSED"
        assert result["event_file"] == str(event_path)

    def test_memory_md_updated_after_post(self, tmp_path):
        wt = tmp_path / "worktree"
        wt.mkdir()
        state_path = tmp_path / ".orca_state.json"
        _make_state_file(state_path, ["f1"])
        executar_pre_hook("f1", wt, state_path)

        from unittest.mock import patch

        class _ApprovedVerdict:
            approved = True

        with patch("scripts.hooks.audit_front", return_value=_ApprovedVerdict()):
            executar_post_hook("f1", wt, state_path, agent_exit_code=0, touched_paths=[])

        memory = state_path.parent / "memory.md"
        content = memory.read_text(encoding="utf-8")
        assert "GATE_PASSED" in content
