# -*- coding: utf-8 -*-
"""
Testes unitários e de integridade dos scripts utilitários do ecossistema AIDD.
Garante que gerador_relatorio_evolucao_planos, gerador_templates_gates e gerar_chave_manifesto
sejam executáveis e possuam cobertura de testes factuais.
"""

import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT_DIR / "scripts"


def test_gerador_relatorio_evolucao_planos_import():
    script = SCRIPTS_DIR / "gerador_relatorio_evolucao_planos.py"
    assert script.is_file()
    res = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True)
    assert res.returncode == 0 or "usage" in res.stdout.lower() or "help" in res.stdout.lower() or "evolucao" in res.stdout.lower()


def test_gerador_templates_gates_import():
    script = SCRIPTS_DIR / "gerador_templates_gates.py"
    assert script.is_file()
    res = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True)
    assert res.returncode == 0 or "usage" in res.stdout.lower() or "help" in res.stdout.lower() or "gate" in res.stdout.lower()


def test_gerar_chave_manifesto_import():
    script = SCRIPTS_DIR / "gerar_chave_manifesto.py"
    assert script.is_file()
    res = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True)
    assert res.returncode == 0 or "usage" in res.stdout.lower() or "help" in res.stdout.lower() or "chave" in res.stdout.lower()
