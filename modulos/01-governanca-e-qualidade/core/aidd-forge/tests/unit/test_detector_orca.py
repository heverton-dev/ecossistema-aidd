import json
from pathlib import Path

import pytest

from aidd_forge.core import orca_bridge
from aidd_forge.core.detector import HostReport, KNOWN_TOOLS, detect_fleet, detect_host, detect_orca, detect_os
from aidd_forge.core.orca_bridge import (
    MODE_MULTI_AGENT,
    MODE_OVERRIDE,
    MODE_SINGLE_AGENT,
    MODE_UNCONFIGURED,
    build_inventory,
    build_routing_rules,
    resolve_default_harness,
    write_orca_config,
)


def _which_only(*present: str):
    def fake_which(name: str) -> str | None:
        return f"/usr/bin/{name}" if name in present else None

    return fake_which


# --- detector.py ---------------------------------------------------------


def test_detect_os_returns_known_value() -> None:
    assert detect_os() in {"windows", "darwin", "linux"}


def test_detect_fleet_returns_only_present_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("aidd_forge.core.detector.shutil.which", _which_only("claude", "cursor"))

    fleet = detect_fleet()

    assert fleet == ("claude", "cursor")


def test_detect_fleet_returns_empty_when_nothing_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("aidd_forge.core.detector.shutil.which", _which_only())

    assert detect_fleet() == ()


def test_detect_orca_true_when_binary_present(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("aidd_forge.core.detector.shutil.which", _which_only("orca"))

    assert detect_orca() is True


def test_detect_orca_false_when_binary_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("aidd_forge.core.detector.shutil.which", _which_only())

    assert detect_orca() is False


def test_detect_host_aggregates_os_fleet_and_orca(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("aidd_forge.core.detector.shutil.which", _which_only("claude", "orca"))

    report = detect_host()

    assert report.available_tools == ("claude",)
    assert report.orca_present is True
    assert report.os_name in {"windows", "darwin", "linux"}


def test_host_report_single_and_no_agent_flags() -> None:
    single = HostReport(os_name="linux", available_tools=("claude",), orca_present=False)
    none_ = HostReport(os_name="linux", available_tools=(), orca_present=False)
    multi = HostReport(os_name="linux", available_tools=("claude", "codex"), orca_present=False)

    assert single.has_single_agent is True
    assert single.has_no_agent is False

    assert none_.has_no_agent is True
    assert none_.has_single_agent is False

    assert multi.has_single_agent is False
    assert multi.has_no_agent is False


def test_known_tools_includes_expected_agents() -> None:
    assert set(KNOWN_TOOLS) == {"claude", "codex", "agy", "cursor", "ollama"}


# --- orca_bridge.py: inventory -------------------------------------------


def test_build_inventory_contains_only_detected_tools() -> None:
    host = HostReport(os_name="windows", available_tools=("claude", "codex"), orca_present=True)

    inventory = build_inventory(host)

    assert inventory == {
        "os": "windows",
        "orca_present": True,
        "harnesses": ["claude", "codex"],
        "harness_count": 2,
    }


def test_build_inventory_empty_fleet_does_not_error() -> None:
    host = HostReport(os_name="linux", available_tools=(), orca_present=False)

    inventory = build_inventory(host)

    assert inventory["harnesses"] == []
    assert inventory["harness_count"] == 0


# --- orca_bridge.py: routing rules cascade --------------------------------


def test_routing_multi_agent_specializes_by_role() -> None:
    host = HostReport(os_name="linux", available_tools=("claude", "codex"), orca_present=False)

    routing = build_routing_rules(host)

    assert routing["mode"] == MODE_MULTI_AGENT
    assert routing["default_harness_override"] is None
    assert routing["roles"]["architect"] == {"harness": "claude", "worktree_isolated": True}
    assert routing["roles"]["database"] == {"harness": "codex", "worktree_isolated": True}


def test_routing_single_agent_isolates_all_workers_without_error() -> None:
    host = HostReport(os_name="linux", available_tools=("agy",), orca_present=False)

    routing = build_routing_rules(host)

    assert routing["mode"] == MODE_SINGLE_AGENT
    for role_config in routing["roles"].values():
        assert role_config == {"harness": "agy", "worktree_isolated": True}


def test_routing_no_agent_is_unconfigured_without_crashing() -> None:
    host = HostReport(os_name="linux", available_tools=(), orca_present=False)

    routing = build_routing_rules(host)

    assert routing["mode"] == MODE_UNCONFIGURED
    for role_config in routing["roles"].values():
        assert role_config == {"harness": None, "worktree_isolated": True}


def test_routing_env_override_forces_single_harness(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ORCA_DEFAULT_HARNESS", "antigravity")
    host = HostReport(os_name="linux", available_tools=("claude", "codex"), orca_present=False)

    routing = build_routing_rules(host)

    assert routing["mode"] == MODE_OVERRIDE
    assert routing["default_harness_override"] == "antigravity"
    for role_config in routing["roles"].values():
        assert role_config == {"harness": "antigravity", "worktree_isolated": True}


def test_routing_explicit_default_harness_wins_over_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ORCA_DEFAULT_HARNESS", "from-env")
    host = HostReport(os_name="linux", available_tools=("claude",), orca_present=False)

    routing = build_routing_rules(host, default_harness="from-param")

    assert routing["default_harness_override"] == "from-param"


def test_resolve_default_harness_prefers_explicit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ORCA_DEFAULT_HARNESS", "from-env")

    assert resolve_default_harness("from-param") == "from-param"


def test_resolve_default_harness_falls_back_to_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ORCA_DEFAULT_HARNESS", "from-env")

    assert resolve_default_harness() == "from-env"


def test_resolve_default_harness_none_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ORCA_DEFAULT_HARNESS", raising=False)

    assert resolve_default_harness() is None


# --- orca_bridge.py: write_orca_config ------------------------------------


def test_write_orca_config_writes_both_files(tmp_path: Path) -> None:
    host = HostReport(os_name="linux", available_tools=("claude",), orca_present=True)

    result = write_orca_config(host, tmp_path)

    assert result.inventory_path == tmp_path / orca_bridge.INVENTORY_FILENAME
    assert result.routing_path == tmp_path / orca_bridge.ROUTING_FILENAME
    assert json.loads(result.inventory_path.read_text(encoding="utf-8")) == result.inventory
    assert json.loads(result.routing_path.read_text(encoding="utf-8")) == result.routing
    assert result.routing["mode"] == MODE_SINGLE_AGENT


def test_write_orca_config_creates_output_dir(tmp_path: Path) -> None:
    host = HostReport(os_name="linux", available_tools=(), orca_present=False)
    output_dir = tmp_path / "nested" / "orca"

    write_orca_config(host, output_dir)

    assert (output_dir / orca_bridge.INVENTORY_FILENAME).exists()
    assert (output_dir / orca_bridge.ROUTING_FILENAME).exists()
