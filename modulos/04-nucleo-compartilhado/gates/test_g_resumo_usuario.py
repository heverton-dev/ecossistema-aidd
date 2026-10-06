#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prova que G_RESUMO_USUARIO morde (Lei #13) — ISSUE-USA-0007."""

import os
import shutil
from pathlib import Path

from _gate_test_utils import rodar_gate

GATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "G_RESUMO_USUARIO.py")
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _montar(tmp_path, *, com_readme=True, com_resumo=True, resumo=None, com_relatorio=True):
    gates = tmp_path / "gates"
    gates.mkdir()
    shutil.copy2(GATE_PATH, gates / "G_RESUMO_USUARIO.py")
    (tmp_path / "core").mkdir()
    (tmp_path / "core" / "entrega_guia.py").write_text(
        "def gerar_resumo_usuario():\n    pass\ndef gerar_relatorio_tecnico():\n    pass\n",
        encoding="utf-8",
    )
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "orquestrador_sincrono.py").write_text(
        "from core.entrega_guia import gerar_resumo_usuario\n",
        encoding="utf-8",
    )
    if com_readme:
        (tmp_path / "README-USUARIO.md").write_text("# App\n\nok\n", encoding="utf-8")
    if com_resumo:
        if resumo is None:
            resumo = (
                "# App — resumo\n\n"
                "## O que mudou?\nFoi criado.\n\n"
                "## Como eu abro?\nmake run\n\n"
                "## Como eu verifico?\nAbra http://localhost:3000\n"
            )
        (tmp_path / "RESUMO-USUARIO.md").write_text(resumo, encoding="utf-8")
    if com_relatorio:
        (tmp_path / "RELATORIO-TECNICO.md").write_text("# Técnico\n- fluxo\n", encoding="utf-8")


def test_g_resumo_usuario_passa_no_repositorio_sem_entrega():
    """Repo sem README-USUARIO na raiz => exit 0 (não cobra entrega)."""
    proc = rodar_gate(GATE_PATH, cwd=ROOT_DIR)
    assert proc.returncode == 0, f"reprovou:\n{proc.stdout}\n{proc.stderr}"


def test_g_resumo_usuario_failing_path_readme_sem_resumo(tmp_path):
    _montar(tmp_path, com_resumo=False, com_relatorio=True)
    proc = rodar_gate(str(tmp_path / "gates" / "G_RESUMO_USUARIO.py"), cwd=str(tmp_path))
    assert proc.returncode == 1, proc.stdout
    assert "RESUMO-USUARIO" in proc.stdout


def test_g_resumo_usuario_failing_path_resumo_sem_perguntas(tmp_path):
    _montar(tmp_path, resumo="# App\n\nAqui mudou alguma coisa.\nsem estrutura\n")
    proc = rodar_gate(str(tmp_path / "gates" / "G_RESUMO_USUARIO.py"), cwd=str(tmp_path))
    assert proc.returncode == 1, proc.stdout
    assert "obrigatória" in proc.stdout or "O que mudou" in proc.stdout


def test_g_resumo_usuario_failing_path_resumo_longo(tmp_path):
    longo = "# App\n" + "\n".join(f"Linha {i}" for i in range(25))
    _montar(tmp_path, resumo=longo + "\n## O que mudou?\nx\n## Como eu abro?\ny\n## Como eu verifico?\nz\n")
    # 25+ linhas de cabecalho + 3 perguntas ainda estouram o limite
    proc = rodar_gate(str(tmp_path / "gates" / "G_RESUMO_USUARIO.py"), cwd=str(tmp_path))
    assert proc.returncode == 1, proc.stdout
    assert "linhas" in proc.stdout


def test_g_resumo_usuario_aceita_template_bem_formado(tmp_path):
    _montar(tmp_path)
    proc = rodar_gate(str(tmp_path / "gates" / "G_RESUMO_USUARIO.py"), cwd=str(tmp_path))
    assert proc.returncode == 0, proc.stdout
