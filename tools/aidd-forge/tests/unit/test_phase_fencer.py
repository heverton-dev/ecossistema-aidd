import json
from pathlib import Path

import pytest

from aidd_forge.core.phase_fencer import PhaseFencer

REAL_TEMPLATES_ROOT = Path(__file__).resolve().parents[2] / "aidd_forge" / "templates"

EXPECTED_PHASES = (
    "phase_00_bootstrap",
    "phase_01_requirements",
    "phase_02_architecture",
    "phase_03_implementation",
    "phase_04_audit_security",
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_phase(templates_root: Path, phase: str, agents: str = "regra", mcp: str = "{}") -> None:
    _write(templates_root / "pipeline_phases" / phase / "AGENTS.md", agents)
    _write(templates_root / "pipeline_phases" / phase / "mcp_config.json", mcp)


def test_run_provisions_real_five_phases(tmp_path: Path) -> None:
    target = tmp_path / "project"
    result = PhaseFencer(REAL_TEMPLATES_ROOT, target).run()

    assert result.phases == EXPECTED_PHASES
    for phase in EXPECTED_PHASES:
        phase_dir = target / ".aidd" / "pipeline" / phase
        assert (phase_dir / "AGENTS.md").exists()
        assert (phase_dir / "mcp_config.json").exists()


def test_real_mcp_configs_are_valid_json_scoped_per_phase(tmp_path: Path) -> None:
    target = tmp_path / "project"
    PhaseFencer(REAL_TEMPLATES_ROOT, target).run()

    expected_servers = {
        "phase_00_bootstrap": set(),
        "phase_01_requirements": {"filesystem"},
        "phase_02_architecture": {"schemas"},
        "phase_03_implementation": {"database"},
        "phase_04_audit_security": {"filesystem"},
    }

    for phase, servers in expected_servers.items():
        config_path = target / ".aidd" / "pipeline" / phase / "mcp_config.json"
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        assert set(payload["mcpServers"].keys()) == servers


def test_run_raises_when_pipeline_phases_dir_missing(tmp_path: Path) -> None:
    templates = tmp_path / "templates"
    templates.mkdir()

    with pytest.raises(FileNotFoundError):
        PhaseFencer(templates, tmp_path / "project").run()


def test_run_raises_when_phase_missing_mcp_config(tmp_path: Path) -> None:
    templates = tmp_path / "templates"
    _write(templates / "pipeline_phases" / "phase_00_bootstrap" / "AGENTS.md", "regra")

    with pytest.raises(FileNotFoundError):
        PhaseFencer(templates, tmp_path / "project").run()


def test_run_is_idempotent_without_force(tmp_path: Path) -> None:
    templates = tmp_path / "templates"
    _write_phase(templates, "phase_00_bootstrap")

    target = tmp_path / "project"
    fencer = PhaseFencer(templates, target)
    fencer.run()

    result = fencer.run()

    assert not result.injection.created
    assert result.injection.skipped


def test_run_overwrites_with_force(tmp_path: Path) -> None:
    templates = tmp_path / "templates"
    _write_phase(templates, "phase_00_bootstrap", agents="v2")

    target = tmp_path / "project"
    _write(target / ".aidd" / "pipeline" / "phase_00_bootstrap" / "AGENTS.md", "v1")
    _write(target / ".aidd" / "pipeline" / "phase_00_bootstrap" / "mcp_config.json", "{}")

    result = PhaseFencer(templates, target, force=True).run()

    agents_path = target / ".aidd" / "pipeline" / "phase_00_bootstrap" / "AGENTS.md"
    assert agents_path.read_text(encoding="utf-8") == "v2"
    assert result.injection.overwritten
