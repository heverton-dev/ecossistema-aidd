#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prova que G_ANT_LOCKIN_LEGADO morde (Lei #13) — ISSUE-USA-0008."""

import os
import shutil
import sys
from pathlib import Path

from _gate_test_utils import rodar_gate

GATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "G_ANT_LOCKIN_LEGADO.py")
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from core.anti_lockin import possui_sujeira, varredura  # noqa: E402


def test_varredura_detecta_supabase_e_lovable(tmp_path):
    (tmp_path / "package.json").write_text('{"dependencies":{"@supabase/supabase-js":"2"}}\n', encoding="utf-8")
    (tmp_path / ".lovable").mkdir()
    r = varredura(tmp_path)
    assert possui_sujeira(r)
    assert any("supabase" in h.lower() for h in r["hits"])
    assert any(".lovable" in d for d in r["dirs"])


def test_varredura_allowlist_libera_intencional(tmp_path):
    (tmp_path / "supabase").mkdir()
    (tmp_path / "lockin-allowlist.txt").write_text("supabase # self-hosted intencional\n", encoding="utf-8")
    r = varredura(tmp_path)
    assert not possui_sujeira(r)
    assert r["permitidos"]


def test_varredura_limpa_exit0(tmp_path):
    (tmp_path / "package.json").write_text('{"name":"app"}\n', encoding="utf-8")
    r = varredura(tmp_path)
    assert not possui_sujeira(r)


def test_g_ant_lockin_failing_path_fixture_suja(tmp_path):
    """Repo sintético com sujeira + módulo => exit 1 (Lei #13)."""
    gates = tmp_path / "gates"
    gates.mkdir()
    shutil.copy2(GATE_PATH, gates / "G_ANT_LOCKIN_LEGADO.py")
    (tmp_path / "core").mkdir()
    shutil.copy2(Path(ROOT_DIR) / "core" / "anti_lockin.py", tmp_path / "core" / "anti_lockin.py")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "orquestrador_sincrono.py").write_text(
        "from core.anti_lockin import varredura\n",
        encoding="utf-8",
    )
    # entrega com sujeira
    entrega = tmp_path / "meu-app"
    entrega.mkdir()
    (entrega / "README-USUARIO.md").write_text("# App\n", encoding="utf-8")
    (entrega / "package.json").write_text('{"dependencies":{"supabase":"1"}}\n', encoding="utf-8")

    proc = rodar_gate(str(gates / "G_ANT_LOCKIN_LEGADO.py"), cwd=str(tmp_path))
    assert proc.returncode == 1, proc.stdout
    assert "ANT_LOCKIN" in proc.stdout or "lock-in" in proc.stdout


def test_g_ant_lockin_passa_no_repositorio():
    proc = rodar_gate(GATE_PATH, cwd=ROOT_DIR)
    assert proc.returncode == 0, f"reprovou:\n{proc.stdout}\n{proc.stderr}"
