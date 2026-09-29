# -*- coding: utf-8 -*-
"""
Hardening tests do PLANO-EVOLUCAO ciclo-02 (aidd-bridge):
- Ticket 2 (D11): falha de import de gate não pode ser silenciada (return 1).
- Ticket 3 (D12): bridge-manifest.json registra pipeline_telemetry por fase.
- Ticket 4 (D15): bridge-handoff.json canônico (sucesso e falha).
"""

import json
import os
import sys
import tempfile
import types

import pytest

BRIDGE_DIR = os.path.dirname(os.path.dirname(__file__))
GATES_DIR = os.path.join(BRIDGE_DIR, "gates")
sys.path.insert(0, BRIDGE_DIR)
sys.path.insert(0, GATES_DIR)

from aidd_bridge.pipeline_bridge import BridgePipeline
import G_BRIDGE_VENDOR_LOCKIN


def _make_minimal_project(src_dir: str) -> None:
    pages = os.path.join(src_dir, "src", "pages")
    os.makedirs(pages, exist_ok=True)
    with open(os.path.join(pages, "Index.tsx"), "w", encoding="utf-8") as f:
        f.write("export default function Index() { return <div>Home</div>; }")
    with open(os.path.join(src_dir, "package.json"), "w", encoding="utf-8") as f:
        f.write('{"name": "mock-lovable-app", "dependencies": {"react": "^18.0.0"}}')


def _run_pipeline(src_dir: str, out_dir: str) -> int:
    return BridgePipeline(src_dir, output_dir=out_dir, domain="app.empresa.com").run()


def test_pipeline_retorna_1_quando_import_de_gate_falha(monkeypatch):
    """Ticket 2 (D11): import de gate inacessível deve retornar 1, nunca
    ser engolido por `except Exception: print(AVISO)` com exit 0."""
    # Quebra o import do gate: módulo presente em sys.modules mas sem o símbolo
    stub = types.ModuleType("G_BRIDGE_VENDOR_LOCKIN")
    monkeypatch.setitem(sys.modules, "G_BRIDGE_VENDOR_LOCKIN", stub)

    with tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as out_dir:
        _make_minimal_project(src_dir)
        status = _run_pipeline(src_dir, out_dir)

    assert status == 1


def test_manifest_registra_telemetria_por_fase():
    """Ticket 3 (D12): bridge-manifest.json precisa expor pipeline_telemetry
    com started_at/finished_at/total_duration_s e phase_timings das 6 fases."""
    with tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as out_dir:
        _make_minimal_project(src_dir)
        assert _run_pipeline(src_dir, out_dir) == 0

        with open(os.path.join(out_dir, "bridge-manifest.json"), "r", encoding="utf-8") as f:
            manifest = json.load(f)

        telemetry = manifest["pipeline_telemetry"]
        assert telemetry["started_at"]
        assert telemetry["finished_at"]
        assert telemetry["total_duration_s"] >= 0
        for fase in ("scan", "db", "frontend", "devops", "vsa", "gates"):
            assert fase in telemetry["phase_timings"], f"fase {fase} sem timing"
            assert telemetry["phase_timings"][fase] >= 0


def test_handoff_canonico_gerado_com_sucesso():
    """Ticket 4 (D15): exit 0 grava bridge-handoff.json canônico."""
    with tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as out_dir:
        _make_minimal_project(src_dir)
        assert _run_pipeline(src_dir, out_dir) == 0

        handoff_path = os.path.join(out_dir, "bridge-handoff.json")
        with open(handoff_path, "r", encoding="utf-8") as f:
            handoff = json.load(f)

        assert handoff["tool"] == "aidd-bridge"
        assert handoff["status"] == "succeeded"
        assert handoff["next_tool"] == "aidd-master"
        assert handoff["pipeline_id"].startswith("bridge-")
        assert isinstance(handoff["artifacts"], list) and handoff["artifacts"]
        assert handoff["gate_results"]["G_BRIDGE_VENDOR_LOCKIN"] == 0
        assert handoff["pipeline_telemetry"]["phase_timings"]


def test_handoff_canonico_registra_falha_de_gate(monkeypatch):
    """Ticket 4 (D15): exit 1 grava bridge-handoff.json com status failed
    e error_phase apontando a fase que falhou."""
    monkeypatch.setattr(
        G_BRIDGE_VENDOR_LOCKIN, "audit_vendor_lockin", lambda target_dir: 1
    )

    with tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as out_dir:
        _make_minimal_project(src_dir)
        assert _run_pipeline(src_dir, out_dir) == 1

        with open(os.path.join(out_dir, "bridge-handoff.json"), "r", encoding="utf-8") as f:
            handoff = json.load(f)

        assert handoff["status"] == "failed"
        assert handoff["error_phase"]
        assert handoff["gate_results"]["G_BRIDGE_VENDOR_LOCKIN"] == 1
