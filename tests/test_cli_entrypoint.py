# -*- coding: utf-8 -*-
"""
Testes automatizados do CLI universal AIDD (scripts/cli_entrypoint.py).
Garante conformidade com Lei #5 (Testes Reais / Zero Mocks) e Lei #1 (Determinismo).
"""

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


def test_cli_help():
    """Verifica se o comando exibe a ajuda com sucesso e código de saída 0."""
    cmd = [sys.executable, str(ROOT_DIR / "scripts" / "cli_entrypoint.py"), "--help"]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT_DIR))
    assert res.returncode == 0
    assert "aidd" in res.stdout
    assert "pure" in res.stdout
    assert "open" in res.stdout
    assert "freedom" in res.stdout
    assert "full" in res.stdout


def test_cli_version():
    """Verifica se o comando exibe a versão correta."""
    cmd = [sys.executable, str(ROOT_DIR / "scripts" / "cli_entrypoint.py"), "--version"]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT_DIR))
    assert res.returncode == 0
    assert "AIDD CLI v5.1.0" in res.stdout


def test_cli_pure_quick(tmp_path):
    """Verifica a geração completa de um projeto no modo pure --quick."""
    app_dir = tmp_path / "app-pure-teste"
    cmd = [
        sys.executable,
        str(ROOT_DIR / "scripts" / "cli_entrypoint.py"),
        "pure",
        "app-pure-teste",
        "--quick",
        "--destino",
        str(app_dir),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT_DIR))
    assert res.returncode == 0, f"Falha na execução: {res.stderr}\nSTDOUT: {res.stdout}"

    # Verificações de estrutura
    assert (app_dir / "PLANNER.json").is_file()
    assert (app_dir / "DESIGN-SYSTEM.json").is_file()
    assert (app_dir / "iniciar.ps1").is_file()
    assert (app_dir / "iniciar.sh").is_file()
    assert (app_dir / "src" / "server.py").is_file()
    assert (app_dir / "frontend" / "package.json").is_file()

    # Validação do PLANNER.json gerado
    with open(app_dir / "PLANNER.json", "r", encoding="utf-8") as f:
        plano = json.load(f)
    assert plano["meta"]["fluxo_alvo"] == "fluxo_01_generator"
    assert plano["meta"]["projeto_nome"] == "app-pure-teste"


def test_cli_open_quick(tmp_path):
    """Verifica a geração completa de um projeto no modo open --quick."""
    app_dir = tmp_path / "app-open-teste"
    cmd = [
        sys.executable,
        str(ROOT_DIR / "scripts" / "cli_entrypoint.py"),
        "open",
        "app-open-teste",
        "--quick",
        "--destino",
        str(app_dir),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT_DIR))
    assert res.returncode == 0, f"Falha na execução: {res.stderr}\nSTDOUT: {res.stdout}"

    assert (app_dir / "PLANNER.json").is_file()
    with open(app_dir / "PLANNER.json", "r", encoding="utf-8") as f:
        plano = json.load(f)
    assert plano["meta"]["fluxo_alvo"] == "fluxo_02_factory"


def test_cli_freedom_origem_invalida(tmp_path):
    """Verifica se o modo freedom rejeita caminhos inexistentes."""
    caminho_inexistente = tmp_path / "inexistente_12345"
    cmd = [
        sys.executable,
        str(ROOT_DIR / "scripts" / "cli_entrypoint.py"),
        "freedom",
        str(caminho_inexistente),
        "app-teste",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT_DIR))
    assert res.returncode != 0
    assert "não encontrado" in res.stdout.lower() or "não encontrado" in res.stderr.lower() or res.returncode == 1
