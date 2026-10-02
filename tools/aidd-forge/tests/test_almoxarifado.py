from __future__ import annotations

import hashlib
from pathlib import Path
import pytest
from click.testing import CliRunner

from aidd_forge.cli import cli
from aidd_forge.core.almoxarifado import caminho_peca, obter_peca


def _sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    h.update(caminho.read_bytes())
    return h.hexdigest()


def test_caminho_peca_retorna_caminho_existente() -> None:
    path = caminho_peca("moldes/infra/Dockerfile")
    assert path.is_file()
    assert path.name == "Dockerfile"


def test_obter_peca_copia_para_projeto_e_confere_sha256(tmp_path: Path) -> None:
    projeto_dir = tmp_path / "meu_projeto"
    projeto_dir.mkdir(parents=True, exist_ok=True)

    destino_arquivo = obter_peca("moldes/infra/Dockerfile", destino=projeto_dir)

    assert destino_arquivo.is_file()
    assert destino_arquivo.parent == projeto_dir
    assert destino_arquivo.name == "Dockerfile"

    origem = caminho_peca("moldes/infra/Dockerfile")
    assert _sha256(destino_arquivo) == _sha256(origem)


def test_obter_peca_recusa_destino_dentro_de_tools(tmp_path: Path) -> None:
    tools_dir = tmp_path / "tools" / "aidd-pure"
    tools_dir.mkdir(parents=True, exist_ok=True)

    with pytest.raises(ValueError, match="tools"):
        obter_peca("moldes/infra/Dockerfile", destino=tools_dir)


def test_obter_peca_peca_desconhecida_lanca_erro_claro(tmp_path: Path) -> None:
    projeto_dir = tmp_path / "meu_projeto"
    projeto_dir.mkdir(parents=True, exist_ok=True)

    with pytest.raises(ValueError, match="não encontrada"):
        caminho_peca("peca_inexistente_qualquer.xyz")

    with pytest.raises(ValueError, match="não encontrada"):
        obter_peca("peca_inexistente_qualquer.xyz", destino=projeto_dir)


def test_cli_forge_fornecer(tmp_path: Path) -> None:
    runner = CliRunner()
    projeto_dir = tmp_path / "cli_projeto"
    projeto_dir.mkdir(parents=True, exist_ok=True)

    result = runner.invoke(
        cli,
        ["fornecer", "moldes/infra/Dockerfile", "--destino", str(projeto_dir)],
    )

    assert result.exit_code == 0
    assert (projeto_dir / "Dockerfile").is_file()


def test_ecossistema_cli_forge_fornecer(tmp_path: Path) -> None:
    import subprocess
    import sys

    projeto_dir = tmp_path / "e2e_projeto"
    projeto_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "ecossistema.py",
        "forge",
        "fornecer",
        "moldes/infra/Dockerfile",
        "--destino",
        str(projeto_dir),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"Falha CLI ecossistema.py: {res.stderr}\n{res.stdout}"
    assert (projeto_dir / "Dockerfile").is_file()

