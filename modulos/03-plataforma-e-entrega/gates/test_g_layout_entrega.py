#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prova que G_LAYOUT_ENTREGA morde (Lei #13) e resolve_pasta_entrega cumpre o contrato."""

import os
import shutil
import sys
from pathlib import Path

import pytest

from _gate_test_utils import rodar_gate

GATE_DIR = os.path.dirname(os.path.abspath(__file__))
GATE_PATH = os.path.join(GATE_DIR, "G_LAYOUT_ENTREGA.py")
ROOT_DIR = os.path.dirname(GATE_DIR)

sys.path.insert(0, ROOT_DIR)
from core.resolve_pasta_entrega import resolve_pasta_entrega  # noqa: E402


# --- helper: contrato -------------------------------------------------------

def test_explicit_pasta_wins(tmp_path):
    r = resolve_pasta_entrega(tmp_path, "meu-app", pasta_arg=str(tmp_path / "outro"))
    assert r.ok
    assert r.caminho == (tmp_path / "outro").resolve()


def test_legacy_sibling_forces_workspace_root(tmp_path):
    """Legado irmao => entrega na raiz do workspace, nunca em projetos/ (ISSUE-USA-0002)."""
    workspace = tmp_path / "workspace"
    clone = workspace / "ecossistema-aidd"
    legado = workspace / "proj_app"
    (clone / "gates").mkdir(parents=True)
    (clone / "componentes").mkdir()
    (clone / "ecossistema.py").write_text("# tool\n", encoding="utf-8")
    (legado / "src").mkdir(parents=True)
    (legado / "package.json").write_text("{}", encoding="utf-8")

    r = resolve_pasta_entrega(clone, "logistica-frotas")
    assert r.ok, r.como_dict()
    assert r.caminho == workspace / "logistica-frotas"
    assert "projetos" not in r.caminho.parts


def test_ecosystem_only_uses_projetos(tmp_path):
    clone = tmp_path / "ecossistema-aidd"
    (clone / "gates").mkdir(parents=True)
    (clone / "componentes").mkdir()
    (clone / "ecossistema.py").write_text("# tool\n", encoding="utf-8")

    r = resolve_pasta_entrega(clone, "meu-app")
    assert r.ok
    assert r.caminho == clone / "projetos" / "meu-app"


def test_ambiguity_returns_structured_error_zero_writes(tmp_path):
    """2 candidatos legados (cwd e pai) => erro estruturado, sem escrita (Lei #7)."""
    pai = tmp_path / "nivel1"
    cwd = pai / "nivel2"
    (cwd / "src").mkdir(parents=True)
    (cwd / "package.json").write_text("{}", encoding="utf-8")
    (pai / "proj_legado" / "src").mkdir(parents=True)
    (pai / "proj_legado" / "package.json").write_text("{}", encoding="utf-8")

    antes = set(pai.rglob("*"))
    r = resolve_pasta_entrega(cwd, "app")
    depois = set(pai.rglob("*"))
    assert not r.ok
    assert r.erro == "pasta_entrega_ambigua"
    assert r.opcoes and len(r.opcoes) >= 2
    assert antes == depois  # zero disk writes


# --- gate: prova de mordida -------------------------------------------------

def test_g_layout_entrega_passa_no_repositorio():
    proc = rodar_gate(GATE_PATH, cwd=ROOT_DIR)
    assert proc.returncode == 0, f"G_LAYOUT_ENTREGA reprovou:\n{proc.stdout}\n{proc.stderr}"


def test_g_layout_entrega_failing_path_helper_desmapeado(tmp_path):
    """Orquestrador sem resolve_pasta_entrega => exit 1 (Lei #13)."""
    fake_gates = tmp_path / "gates"
    fake_gates.mkdir()
    shutil.copy2(GATE_PATH, fake_gates / "G_LAYOUT_ENTREGA.py")
    (tmp_path / "core").mkdir()
    (tmp_path / "core" / "resolve_pasta_entrega.py").write_text(
        "def resolve_pasta_entrega(cwd, nome_projeto, pasta_arg=None):\n    pass\n",
        encoding="utf-8",
    )
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "orquestrador_sincrono.py").write_text(
        'pasta = f"./projetos/{slug}"\n',
        encoding="utf-8",
    )
    (tmp_path / "docs" / "livros" / "partes").mkdir(parents=True)
    (tmp_path / "docs" / "livros" / "partes" / "02-fluxos.md").write_text(
        "clone dentro de projeto existente\n",
        encoding="utf-8",
    )

    proc = rodar_gate(str(fake_gates / "G_LAYOUT_ENTREGA.py"), cwd=str(tmp_path))
    assert proc.returncode == 1, proc.stdout
    assert "G_LAYOUT_ENTREGA" in proc.stdout


def test_g_layout_entrega_failing_path_layout_aninhado(tmp_path):
    """projetos/ preenchido com legado irmao => exit 1 (Lei #13)."""
    fake_gates = tmp_path / "gates"
    fake_gates.mkdir()
    shutil.copy2(GATE_PATH, fake_gates / "G_LAYOUT_ENTREGA.py")
    (tmp_path / "core").mkdir()
    (tmp_path / "core" / "resolve_pasta_entrega.py").write_text(
        "def resolve_pasta_entrega(cwd, nome_projeto, pasta_arg=None):\n    pass\n",
        encoding="utf-8",
    )
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "orquestrador_sincrono.py").write_text(
        "from core.resolve_pasta_entrega import resolve_pasta_entrega\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "livros" / "partes").mkdir(parents=True)
    (tmp_path / "docs" / "livros" / "partes" / "02-fluxos.md").write_text(
        "clone dentro de projeto existente\n",
        encoding="utf-8",
    )
    # legado irmao do "clone" (tmp_path é o pai)
    (tmp_path / "proj_app" / "src").mkdir(parents=True)
    # entrega aninhada proibida
    (tmp_path / "projetos" / "app-x").mkdir(parents=True)

    proc = rodar_gate(str(fake_gates / "G_LAYOUT_ENTREGA.py"), cwd=str(tmp_path))
    assert proc.returncode == 1, proc.stdout
    assert "projetos/" in proc.stdout or "aninhado" in proc.stdout
