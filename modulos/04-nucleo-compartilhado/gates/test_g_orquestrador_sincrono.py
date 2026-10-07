# -*- coding: utf-8 -*-
"""
Testes do gate G_ORQUESTRADOR_SINCRONO.
Valida aprovação no estado íntegro e reprovação categórica (exit 1) quando
qualquer um dos pilares de handoff ou orquestração síncrona é violado.
"""

import os
import sys
from pathlib import Path
import pytest

from pathlib import Path as _Path
ROOT_DIR = str(next((p.parent for p in _Path(__file__).resolve().parents if p.name == "modulos"), _Path(__file__).resolve().parent.parent))  # raiz: pai de modulos/ (VSA) ou de gates/ (árvore sintética)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import G_ORQUESTRADOR_SINCRONO as gate
from G_ORQUESTRADOR_SINCRONO import auditar


def test_gate_orquestrador_sincrono_passa():
    """No repositório íntegro, o gate deve aprovar com exit 0."""
    assert auditar() == 0


def test_gate_reprova_se_script_orquestrador_ausente(tmp_path, monkeypatch):
    """Lei #13: Prova que o gate morde (exit 1) se scripts/orquestrador_sincrono.py sumir."""
    monkeypatch.setattr(gate, "ROOT_DIR", Path(tmp_path))
    codigo = auditar()
    assert codigo == 1


def test_gate_reprova_se_schema_handoff_corrompido(tmp_path, monkeypatch):
    """Lei #13: Prova que o gate morde (exit 1) se schema de handoff for JSON inválido."""
    # Monta estrutura parcial
    specs_dir = tmp_path / "componentes" / "compartilhado" / "specs"
    specs_dir.mkdir(parents=True)
    corrupted_schema = specs_dir / "handoff-planner-to-engine.schema.json"
    corrupted_schema.write_text("{ json invalido sem fechar", encoding="utf-8")

    monkeypatch.setattr(gate, "SPECS_DIR", specs_dir)
    codigo = auditar()
    assert codigo == 1
