#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Testes determinísticos que provam que o gate G_TEMPLATE_FORGE_ROT morde (Lei #13)."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
GATE_SCRIPT = ROOT_DIR / "gates" / "G_TEMPLATE_FORGE_ROT.py"
REAL_TEMPLATES_DIR = ROOT_DIR / "tools" / "aidd-forge" / "aidd_forge" / "templates"


def test_template_forge_rot_passa_no_estado_real_integro() -> None:
    """Verifica que o estado real atual dos templates do forge passa com exit 0."""
    res = subprocess.run(
        [sys.executable, str(GATE_SCRIPT), str(REAL_TEMPLATES_DIR)],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stdout + res.stderr
    assert "Templates do aidd-forge 100% em conformidade" in res.stdout


def test_template_forge_rot_morde_se_remover_lei_obrigatoria(tmp_path: Path) -> None:
    """Prova que o portão morde (exit 1) se uma das 13 leis canônicas for omitida."""
    fake_templates = tmp_path / "templates"
    shutil.copytree(REAL_TEMPLATES_DIR, fake_templates)

    agents_file = fake_templates / "governance" / "AGENTS.md"
    conteudo = agents_file.read_text(encoding="utf-8")
    conteudo_corrompido = conteudo.replace("Quarteto Sine Qua Non", "Quarteto Opcional")
    agents_file.write_text(conteudo_corrompido, encoding="utf-8")

    res = subprocess.run(
        [sys.executable, str(GATE_SCRIPT), str(fake_templates)],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1
    assert "Quarteto Sine Qua Non" in res.stderr or "Quarteto Sine Qua Non" in res.stdout


def test_template_forge_rot_morde_se_faltar_skill_canonica(tmp_path: Path) -> None:
    """Prova que o portão morde (exit 1) se uma skill procedural da Tríade for excluída."""
    fake_templates = tmp_path / "templates"
    shutil.copytree(REAL_TEMPLATES_DIR, fake_templates)

    shutil.rmtree(fake_templates / "skills" / "aidd-grill")

    res = subprocess.run(
        [sys.executable, str(GATE_SCRIPT), str(fake_templates)],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1
    assert "aidd-grill" in res.stderr or "aidd-grill" in res.stdout


def test_template_forge_rot_morde_se_faltar_gate_canonico(tmp_path: Path) -> None:
    """Prova que o portão morde (exit 1) se um quality gate essencial for omitido."""
    fake_templates = tmp_path / "templates"
    shutil.copytree(REAL_TEMPLATES_DIR, fake_templates)

    (fake_templates / "gates" / "G_QUARTETO_SINE_QUA_NON.py").unlink()

    res = subprocess.run(
        [sys.executable, str(GATE_SCRIPT), str(fake_templates)],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1
    assert "G_QUARTETO_SINE_QUA_NON.py" in res.stderr or "G_QUARTETO_SINE_QUA_NON.py" in res.stdout
