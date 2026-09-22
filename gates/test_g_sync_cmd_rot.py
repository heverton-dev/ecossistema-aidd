#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_g_sync_cmd_rot.py - Prova que o gate G_SYNC_CMD_ROT morde (Lei #13).
"""

import os
import shutil
from pathlib import Path

from _gate_test_utils import rodar_gate

GATE_DIR = os.path.dirname(os.path.abspath(__file__))
GATE_PATH = os.path.join(GATE_DIR, "G_SYNC_CMD_ROT.py")
ROOT_DIR = os.path.dirname(GATE_DIR)


def test_g_sync_cmd_rot_passa_no_repositorio():
    """Repo limpo (docs + aliases) => exit 0."""
    proc = rodar_gate(GATE_PATH, cwd=ROOT_DIR)
    assert proc.returncode == 0, f"G_SYNC_CMD_ROT reprovou:\n{proc.stdout}\n{proc.stderr}"
    assert "OK" in proc.stdout


def test_g_sync_cmd_rot_failing_path_doc_incompleto(tmp_path):
    """Doc vivo com `components sync` sem --tipo => exit 1 (Lei #13)."""
    fake_gates = tmp_path / "gates"
    fake_gates.mkdir()
    shutil.copy2(GATE_PATH, fake_gates / "G_SYNC_CMD_ROT.py")

    (tmp_path / "docs" / "protocolos").mkdir(parents=True)
    (tmp_path / "MEMORY.md").write_text(
        "# Mem\n\nRode `python ecossistema.py components sync`.\n",
        encoding="utf-8",
    )
    # aliases minimos para isolar a violacao de doc
    (tmp_path / "ecossistema.py").write_text(
        'dispatch = {"sync": cmd_sync}\nflag = "--tipos"\n',
        encoding="utf-8",
    )
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "gestor_componentes.py").write_text(
        'p.add_argument("--tipos")\n',
        encoding="utf-8",
    )

    proc = rodar_gate(str(fake_gates / "G_SYNC_CMD_ROT.py"), cwd=str(tmp_path))
    assert proc.returncode == 1, proc.stdout
    assert "G_SYNC_CMD_ROT" in proc.stdout
    assert "forma incompleta" in proc.stdout
    assert "MEMORY.md" in proc.stdout


def test_g_sync_cmd_rot_failing_path_alias_desmapeado(tmp_path):
    """Parser sem alias `sync`/`--tipos` => exit 1 (Lei #13)."""
    fake_gates = tmp_path / "gates"
    fake_gates.mkdir()
    shutil.copy2(GATE_PATH, fake_gates / "G_SYNC_CMD_ROT.py")

    (tmp_path / "MEMORY.md").write_text(
        "# Mem\n\n`python ecossistema.py components sync --tipo todos`\n",
        encoding="utf-8",
    )
    (tmp_path / "ecossistema.py").write_text(
        'dispatch = {"components": cmd_components}\n',
        encoding="utf-8",
    )
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "gestor_componentes.py").write_text(
        'p.add_argument("--tipo")\n',
        encoding="utf-8",
    )

    proc = rodar_gate(str(fake_gates / "G_SYNC_CMD_ROT.py"), cwd=str(tmp_path))
    assert proc.returncode == 1, proc.stdout
    assert "nao mapeado" in proc.stdout or "ausente" in proc.stdout


def test_g_sync_cmd_rot_aceita_forma_canonica(tmp_path):
    """Linha com --tipo (ex.: --tipo skills) nao reprova."""
    fake_gates = tmp_path / "gates"
    fake_gates.mkdir()
    shutil.copy2(GATE_PATH, fake_gates / "G_SYNC_CMD_ROT.py")

    (tmp_path / "MEMORY.md").write_text(
        "# Mem\n\n`python ecossistema.py components sync --tipo todos`\n"
        "`python ecossistema.py components sync --tipo skills`\n",
        encoding="utf-8",
    )
    (tmp_path / "ecossistema.py").write_text(
        'dispatch = {"sync": cmd_sync}\nflag = "--tipos"\n',
        encoding="utf-8",
    )
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "gestor_componentes.py").write_text(
        'p.add_argument("--tipos")\n',
        encoding="utf-8",
    )

    proc = rodar_gate(str(fake_gates / "G_SYNC_CMD_ROT.py"), cwd=str(tmp_path))
    assert proc.returncode == 0, proc.stdout
