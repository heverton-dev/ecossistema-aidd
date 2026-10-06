#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prova que G_PACOTE_CORE morde (Lei #13) — ISSUE-USA-0006."""

import os
import shutil
from pathlib import Path

from _gate_test_utils import rodar_gate

GATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "G_PACOTE_CORE.py")
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _montar(tmp_path, com_sujeira: bool, com_export: bool = True):
    gates = tmp_path / "gates"
    gates.mkdir()
    shutil.copy2(GATE_PATH, gates / "G_PACOTE_CORE.py")
    (tmp_path / "ecossistema.py").write_text("#\n", encoding="utf-8")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "package_usuario.py").write_text("#\n", encoding="utf-8")
    (tmp_path / "docs" / "protocolos").mkdir(parents=True)
    if com_export:
        (tmp_path / ".gitattributes").write_text("*.db export-ignore\n", encoding="utf-8")
    else:
        (tmp_path / ".gitattributes").write_text("* text=auto\n", encoding="utf-8")
    if com_sujeira:
        (tmp_path / "gates" / "junk.db").write_bytes(b"x")
        (tmp_path / "scripts" / "requirements-dev.txt").write_text("x\n", encoding="utf-8")


def test_g_pacote_core_passa_no_repositorio():
    proc = rodar_gate(GATE_PATH, cwd=ROOT_DIR)
    assert proc.returncode == 0, f"reprovou:\n{proc.stdout}\n{proc.stderr}"


def test_g_pacote_core_failing_path_db_e_devreq(tmp_path):
    _montar(tmp_path, com_sujeira=True)
    proc = rodar_gate(str(tmp_path / "gates" / "G_PACOTE_CORE.py"), cwd=str(tmp_path))
    assert proc.returncode == 1, proc.stdout
    assert "G_PACOTE_CORE" in proc.stdout
    assert ".db" in proc.stdout


def test_g_pacote_core_failing_path_sem_export_ignore(tmp_path):
    _montar(tmp_path, com_sujeira=False, com_export=False)
    proc = rodar_gate(str(tmp_path / "gates" / "G_PACOTE_CORE.py"), cwd=str(tmp_path))
    assert proc.returncode == 1, proc.stdout
    assert "export-ignore" in proc.stdout


def test_g_pacote_core_aceita_pacote_limpo(tmp_path):
    _montar(tmp_path, com_sujeira=False)
    proc = rodar_gate(str(tmp_path / "gates" / "G_PACOTE_CORE.py"), cwd=str(tmp_path))
    assert proc.returncode == 0, proc.stdout
