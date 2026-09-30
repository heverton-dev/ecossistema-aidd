import json
import os
import sys
import subprocess
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent

def test_tdd_cli_iniciar_cria_sessao(tmp_path):
    sys.path.insert(0, str(ROOT / ".agents" / "skills" / "aidd-tdd" / "scripts"))
    import cli

    destino = tmp_path / "docs" / "tdd" / "teste_slug"
    destino.mkdir(parents=True, exist_ok=True)
    sessao_file = destino / "sessao.json"

    res = cli.main([
        "iniciar",
        "--alvo", "src/auth.py",
        "--seam", "login_seam",
        "--output", str(sessao_file)
    ])
    assert res == 0
    assert sessao_file.exists()

    with open(sessao_file, "r", encoding="utf-8") as f:
        dados = json.load(f)
    assert dados["alvo"] == "src/auth.py"
    assert dados["seam"] == "login_seam"
    assert dados["fase_atual"] == "SEAM_ACORDADO"

def test_tdd_cli_transicao_fases(tmp_path):
    sys.path.insert(0, str(ROOT / ".agents" / "skills" / "aidd-tdd" / "scripts"))
    import cli

    sessao_file = tmp_path / "sessao.json"
    cli.main(["iniciar", "--alvo", "src/core.py", "--seam", "core_seam", "--output", str(sessao_file)])

    # Avanco para red
    res_red = cli.main(["red", "--sessao", str(sessao_file), "--teste", "tests/test_core.py"])
    assert res_red == 0

    with open(sessao_file, "r", encoding="utf-8") as f:
        dados = json.load(f)
    assert dados["fase_atual"] == "RED"

    # Avanco para green
    res_green = cli.main(["green", "--sessao", str(sessao_file)])
    assert res_green == 0

    with open(sessao_file, "r", encoding="utf-8") as f:
        dados = json.load(f)
    assert dados["fase_atual"] == "GREEN"

def test_tdd_cli_ecossistema_integracao(tmp_path):
    sessao_file = tmp_path / "sessao_e2e.json"
    cmd = [
        sys.executable,
        str(ROOT / "ecossistema.py"),
        "tdd",
        "iniciar",
        "--alvo", "src/teste.py",
        "--seam", "seam_e2e",
        "--output", str(sessao_file)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert sessao_file.exists()

