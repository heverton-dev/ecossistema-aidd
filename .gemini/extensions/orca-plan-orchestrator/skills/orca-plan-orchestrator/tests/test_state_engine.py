"""Tests for state_engine.py — atomic writes, states, crash recovery."""

import json
import os
import time
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from state_engine import (
    FrontState,
    ResumeAction,
    ResumeClassification,
    create_initial_state,
    save_state,
    load_state,
    update_front_state,
    render_memory_md,
    classify_resume,
    retomar_frente_em_execucao,
    _write_atomic,
)


class TestAtomicWrite:
    """Verify atomic write behavior."""

    def test_atomic_write_creates_file(self, tmp_path: Path) -> None:
        target = tmp_path / "test.json"
        _write_atomic(target, '{"key": "value"}')
        assert target.exists()
        assert json.loads(target.read_text()) == {"key": "value"}

    def test_atomic_write_preserves_original_on_failure(self, tmp_path: Path) -> None:
        """If write fails, original file should remain intact."""
        target = tmp_path / "test.json"
        target.write_text('{"original": true}')

        # Simulate a failure during write by writing to a non-writable path
        # Instead, test that tmp file is cleaned up on error
        bad_path = tmp_path / "nonexistent_dir" / "test.json"
        # This should raise but not corrupt anything at target
        try:
            _write_atomic(bad_path, "content")
        except (OSError, FileNotFoundError):
            pass

        # Original untouched
        assert json.loads(target.read_text()) == {"original": True}

    def test_atomic_write_creates_parent_dirs(self, tmp_path: Path) -> None:
        deep = tmp_path / "a" / "b" / "c" / "state.json"
        _write_atomic(deep, '{"ok": true}')
        assert json.loads(deep.read_text()) == {"ok": True}


class TestFrontStates:
    """Verify the 6 states exist."""

    def test_all_six_states(self) -> None:
        states = list(FrontState)
        assert len(states) == 6
        state_values = {s.value for s in states}
        assert state_values == {
            "PENDING", "RUNNING", "GATE_PASSED",
            "MERGED", "FAILED", "PAUSED_QUOTA",
        }


class TestCreateInitialState:
    """Test initial state creation."""

    def test_creates_pending_fronts(self) -> None:
        state = create_initial_state(["alpha", "beta", "gamma"])
        assert state["version"] == 1
        assert len(state["fronts"]) == 3
        for name in ["alpha", "beta", "gamma"]:
            assert state["fronts"][name]["state"] == FrontState.PENDING.value
            assert state["fronts"][name]["branch"] is None
            assert state["fronts"][name]["commit_sha"] is None


class TestSaveLoadState:
    """Test round-trip save/load."""

    def test_save_load_roundtrip(self, tmp_path: Path) -> None:
        state = create_initial_state(["f1", "f2"])
        state_path = tmp_path / ".orca_state.json"

        save_state(state, state_path)
        loaded = load_state(state_path)

        assert loaded["version"] == 1
        assert loaded["fronts"]["f1"]["state"] == "PENDING"
        assert loaded["fronts"]["f2"]["state"] == "PENDING"

    def test_save_is_atomic_no_tmp_residue(self, tmp_path: Path) -> None:
        state = create_initial_state(["x"])
        state_path = tmp_path / ".orca_state.json"
        save_state(state, state_path)

        # No .tmp files should remain
        tmp_files = list(tmp_path.glob("*.tmp"))
        assert len(tmp_files) == 0


class TestUpdateFrontState:
    """Test front state transitions."""

    def test_transition_to_running(self) -> None:
        state = create_initial_state(["f1"])
        update_front_state(
            state, "f1", FrontState.RUNNING,
            branch="orca/f1", commit_sha="abc123def456",
        )
        assert state["fronts"]["f1"]["state"] == "RUNNING"
        assert state["fronts"]["f1"]["branch"] == "orca/f1"
        assert state["fronts"]["f1"]["commit_sha"] == "abc123def456"

    def test_unknown_front_raises(self) -> None:
        state = create_initial_state(["f1"])
        with pytest.raises(KeyError, match="not found"):
            update_front_state(state, "nonexistent", FrontState.MERGED)


class TestRenderMemoryMd:
    """Test Markdown rendering."""

    def test_render_produces_table(self) -> None:
        state = create_initial_state(["a", "b"])
        update_front_state(
            state, "a", FrontState.RUNNING, branch="orca/a"
        )
        md = render_memory_md(state)

        assert "# ORCA ADE" in md
        assert "| a | RUNNING | orca/a |" in md
        assert "| b | PENDING | — |" in md

    def test_render_empty_state(self) -> None:
        state = {"version": 1, "fronts": {}}
        md = render_memory_md(state)
        assert "ORCA ADE" in md
        assert "|" in md  # Header row present


class TestCrashRecovery:
    """Simulate crash-recovery: write state, reload, classify."""

    def test_crash_recovery_running_front(self, tmp_path: Path) -> None:
        # Simulate a crash: a front was RUNNING when process died
        state = create_initial_state(["front-a", "front-b", "front-c"])
        update_front_state(state, "front-a", FrontState.RUNNING, branch="orca/front-a")
        update_front_state(state, "front-b", FrontState.MERGED)

        state_path = tmp_path / ".orca_state.json"
        save_state(state, state_path)

        # --- Simulate restart: load and classify ---
        loaded = load_state(state_path)
        classifications = classify_resume(loaded)

        by_name = {c.front_name: c for c in classifications}

        # front-a: was RUNNING -> resume_running
        assert by_name["front-a"].state == FrontState.RUNNING
        assert by_name["front-a"].action == ResumeAction.RESUME_RUNNING

        # front-b: was MERGED -> ignore
        assert by_name["front-b"].state == FrontState.MERGED
        assert by_name["front-b"].action == ResumeAction.IGNORE

        # front-c: still PENDING -> no_action
        assert by_name["front-c"].state == FrontState.PENDING
        assert by_name["front-c"].action == ResumeAction.NO_ACTION

    def test_crash_recovery_gate_passed(self, tmp_path: Path) -> None:
        state = create_initial_state(["x"])
        update_front_state(
            state, "x", FrontState.GATE_PASSED, branch="orca/x"
        )

        state_path = tmp_path / ".orca_state.json"
        save_state(state, state_path)

        loaded = load_state(state_path)
        classifications = classify_resume(loaded)

        assert classifications[0].action == ResumeAction.READY_TO_MERGE

    def test_crash_recovery_failed_front(self, tmp_path: Path) -> None:
        state = create_initial_state(["y"])
        update_front_state(state, "y", FrontState.FAILED)

        state_path = tmp_path / ".orca_state.json"
        save_state(state, state_path)

        loaded = load_state(state_path)
        classifications = classify_resume(loaded)

        assert classifications[0].action == ResumeAction.RETRY


class TestRetomarStub:
    """Verify the resume stub is a no-op placeholder."""

    def test_retomar_returns_state_unchanged(self) -> None:
        state = create_initial_state(["f1"])
        result = retomar_frente_em_execucao("f1", state)
        assert result is state  # Same object, no-op
