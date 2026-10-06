#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_g_livro_evidencia.py - Testes determinísticos do gate G_LIVRO_EVIDENCIA.
Valida aprovação com livro-texto com rastreabilidade completa e reprovação estrita (exit 1)
sob citações de arquivos inexistentes ou marcadores de trabalho inacabado (TODO/FIXME).
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
import pytest

GATE_DIR = os.path.dirname(os.path.abspath(__file__))
GATE_PATH = os.path.join(GATE_DIR, "G_LIVRO_EVIDENCIA.py")


def _montar_projeto_sintetico_com_livro(tmp_path, conteudo_extra=""):
    proj = tmp_path / "projeto"
    proj.mkdir()
    (proj / "codigo_real.py").write_text("# codigo real\n", encoding="utf-8")

    livro = proj / "livro"
    livro.mkdir()
    partes = livro / "partes"
    partes.mkdir()

    manifesto = {
        "titulo": "Livro Teste",
        "partes": ["01-intro.md"],
        "artefatos_lidos": ["codigo_real.py"],
        "artefatos_ausentes": []
    }
    (livro / "livro.json").write_text(json.dumps(manifesto), encoding="utf-8")

    texto_intro = (
        "# Introducao\n\n"
        "## Rastreabilidade\n"
        "Fontes consultadas: `codigo_real.py`.\n"
        "Este e o sistema oficial.\n"
        f"{conteudo_extra}\n"
    )
    (partes / "01-intro.md").write_text(texto_intro, encoding="utf-8")
    return proj, livro


def test_g_livro_evidencia_passa_com_livro_integro(tmp_path):
    """Valida que G_LIVRO_EVIDENCIA aprova (exit 0) com livro íntegro."""
    proj, livro = _montar_projeto_sintetico_com_livro(tmp_path)

    proc = subprocess.run(
        [sys.executable, GATE_PATH, "--projeto", str(proj)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    assert proc.returncode == 0, f"Falhou inesperadamente:\n{proc.stdout}\n{proc.stderr}"
    assert "Quality Gate G_LIVRO_EVIDENCIA APROVADO" in proc.stdout


def test_g_livro_evidencia_reprova_fonte_inexistente(tmp_path):
    """Valida que G_LIVRO_EVIDENCIA reprova (exit 1) quando o texto cita arquivo inexistente."""
    proj, livro = _montar_projeto_sintetico_com_livro(
        tmp_path,
        conteudo_extra="Referencia a fonte inexistente: `modulo_fantasma.py`."
    )

    proc = subprocess.run(
        [sys.executable, GATE_PATH, "--projeto", str(proj)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    assert proc.returncode == 1, f"Deveria ter retornado 1, retornou {proc.returncode}"
    assert "Quality Gate G_LIVRO_EVIDENCIA FALHOU" in proc.stdout
    assert "modulo_fantasma.py" in proc.stdout


def test_g_livro_evidencia_reprova_marcador_proibido(tmp_path):
    """Valida que G_LIVRO_EVIDENCIA reprova (exit 1) quando há marcadores de trabalho inacabado."""
    proj, livro = _montar_projeto_sintetico_com_livro(
        tmp_path,
        conteudo_extra="TODO: finalizar este capitulo antes do lancamento."
    )

    proc = subprocess.run(
        [sys.executable, GATE_PATH, "--projeto", str(proj)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    assert proc.returncode == 1, f"Deveria ter retornado 1, retornou {proc.returncode}"
    assert "Quality Gate G_LIVRO_EVIDENCIA FALHOU" in proc.stdout
    assert "marcador de trabalho inacabado" in proc.stdout
