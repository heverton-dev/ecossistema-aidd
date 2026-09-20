#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — TESTE DE PROVA QUE MORDE: test_g_estrutura_estado.py
=============================================================================
Validação estrita em runtime (Lei #13 / ISSUE-0022):
  1. Caminho feliz: artefato estruturado conforme passa com exit 0.
  2. Cenários de reprovação deliberada (exit 1):
     - flight plan com schema corrompido ou campos ausentes
     - orca_state com estado desconhecido
     - telemetria jsonl com linha corrompida (não-JSON)
"""

import json
import os
import subprocess
import sys
import tempfile
import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATES_DIR = os.path.join(ROOT_DIR, "gates")
GATE_SCRIPT = os.path.join(GATES_DIR, "G_ESTRUTURA_ESTADO.py")


def test_aprova_repositorio_atual():
    """Valida que a auditoria padrão do repositório passa sem erros (exit 0)."""
    res = subprocess.run(
        [sys.executable, GATE_SCRIPT],
        capture_output=True,
        text=True,
        cwd=ROOT_DIR,
        encoding="utf-8",
        errors="replace",
    )
    assert res.returncode == 0, f"Reprovou indevidamente:\n{res.stdout}\n{res.stderr}"
    assert "SUCESSO" in res.stdout
    assert "LIMITE METROLÓGICO" in res.stdout


def test_aprova_flight_plan_valido(tmp_path):
    """Valida aprovação de um flight plan que adere ao schema canônico."""
    fp_path = tmp_path / "flight_plan.json"
    data = {
        "plan_dir": "docs/planos/PLAN-0001",
        "harness": "claude",
        "profile_binary": "claude",
        "fronts": [
            {
                "name": "front-01",
                "rotulo": "f1",
                "branch": "orca/f1",
                "worktree": "f1",
                "command": ["claude", "--print"],
            }
        ],
    }
    fp_path.write_text(json.dumps(data), encoding="utf-8")

    res = subprocess.run(
        [sys.executable, GATE_SCRIPT, "--check-artifact", str(fp_path), "--type", "flight_plan"],
        capture_output=True,
        text=True,
        cwd=ROOT_DIR,
        encoding="utf-8",
        errors="replace",
    )
    assert res.returncode == 0
    assert "SUCESSO" in res.stdout


def test_reprova_quando_flight_plan_corrompido(tmp_path):
    """Prova que o portão morde (exit 1) quando flight plan omite campos obrigatórios."""
    fp_path = tmp_path / "flight_plan.json"
    corrompido = {
        "plan_dir": "docs/planos/PLAN-0001",
        # Ausente: harness e fronts
    }
    fp_path.write_text(json.dumps(corrompido), encoding="utf-8")

    res = subprocess.run(
        [sys.executable, GATE_SCRIPT, "--check-artifact", str(fp_path), "--type", "flight_plan"],
        capture_output=True,
        text=True,
        cwd=ROOT_DIR,
        encoding="utf-8",
        errors="replace",
    )
    assert res.returncode == 1, f"Deveria ter reprovado com exit 1, retornou {res.returncode}"
    assert "FALHA" in res.stdout
    assert "Campo obrigatório 'fronts' ausente" in res.stdout


def test_reprova_quando_telemetria_jsonl_corrompida(tmp_path):
    """Prova que o portão morde (exit 1) quando arquivo .jsonl contém linha não-JSON."""
    jsonl_path = tmp_path / "telemetry.jsonl"
    jsonl_path.write_text('{"event": "start", "timestamp": 123}\nLINHA_CORROMPIDA_NAO_JSON\n', encoding="utf-8")

    res = subprocess.run(
        [sys.executable, GATE_SCRIPT, "--check-artifact", str(jsonl_path), "--type", "telemetry_jsonl"],
        capture_output=True,
        text=True,
        cwd=ROOT_DIR,
        encoding="utf-8",
        errors="replace",
    )
    assert res.returncode == 1, f"Deveria ter reprovado com exit 1, retornou {res.returncode}"
    assert "Linha corrompida (não-JSON)" in res.stdout


def test_reprova_quando_orca_state_com_estado_invalido(tmp_path):
    """Prova que o portão morde (exit 1) quando orca state contém estado fora do enum."""
    state_path = tmp_path / ".orca_state.json"
    data = {
        "version": 1,
        "fronts": {
            "front-01": {
                "state": "VIBE_CODING_INVALIDO",
                "updated_at": 123456,
            }
        },
    }
    state_path.write_text(json.dumps(data), encoding="utf-8")

    res = subprocess.run(
        [sys.executable, GATE_SCRIPT, "--check-artifact", str(state_path), "--type", "orca_state"],
        capture_output=True,
        text=True,
        cwd=ROOT_DIR,
        encoding="utf-8",
        errors="replace",
    )
    assert res.returncode == 1, f"Deveria ter reprovado com exit 1, retornou {res.returncode}"
    assert "tem estado inválido" in res.stdout
