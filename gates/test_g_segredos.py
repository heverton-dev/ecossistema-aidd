# -*- coding: utf-8 -*-
"""
Testes do gate G_SEGREDOS — valida deteccao de credenciais hardcoded
executando o gate contra repositorios git sinteticos isolados via subprocess.
"""

import json
import os
import shutil
import subprocess

from _gate_test_utils import rodar_gate

GATE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "G_SEGREDOS.py"
)


def _init_repo_sintetico(root_dir):
    """Inicializa um repositorio git valido no diretorio sintetico com G_SEGREDOS copiado."""
    subprocess.run(["git", "init"], cwd=root_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=root_dir,
        check=True,
        capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test Runner"],
        cwd=root_dir,
        check=True,
        capture_output=True
    )

    gdir = os.path.join(root_dir, "gates")
    os.makedirs(gdir, exist_ok=True)
    gate_copy = os.path.join(gdir, "G_SEGREDOS.py")
    shutil.copyfile(GATE_PATH, gate_copy)

    return gate_copy


def _comitar_tudo(root_dir, msg="Commit teste"):
    """Adiciona todos os arquivos e comita no repositorio sintetico."""
    subprocess.run(["git", "add", "."], cwd=root_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.email=test@example.com", "-c", "user.name=Test Runner", "commit", "-m", msg],
        cwd=root_dir,
        check=True,
        capture_output=True
    )


def test_repo_limpo_aprova(tmp_path):
    gate_path = _init_repo_sintetico(tmp_path)
    # Criar arquivo normal rastreado
    arquivo_ok = tmp_path / "README.md"
    arquivo_ok.write_text("# Repositorio Limpo\nNenhum segredo aqui.", encoding="utf-8")
    _comitar_tudo(tmp_path)

    res = rodar_gate(gate_path, tmp_path)
    assert res.returncode == 0
    assert "Quality Gate G_SEGREDOS APROVADO (100% OK)!" in res.stdout


def test_falha_com_dois_padroes_de_segredos_diferentes(tmp_path):
    gate_path = _init_repo_sintetico(tmp_path)

    # Padrao 1: AWS Access Key ID (AKIA...)
    aws_file = tmp_path / "aws_credentials.txt"
    aws_file.write_text("aws_key=AKIAIOSFODNN7EXAMPLE\n", encoding="utf-8")

    # Padrao 2: GitHub Personal Access Token (ghp_...)
    gh_file = tmp_path / "github_token.txt"
    gh_file.write_text("ghp_1234567890abcdefghijklmnopqrstuvwxyz\n", encoding="utf-8")

    _comitar_tudo(tmp_path)

    res = rodar_gate(gate_path, tmp_path)
    assert res.returncode == 1
    assert "Quality Gate REPROVADO" in res.stdout
    assert "aws_credentials.txt: AWS Access Key ID (AKIA...)" in res.stdout
    assert "github_token.txt: GitHub Personal Access Token (ghp_...)" in res.stdout


def test_allowlist_autoriza_segredos_conhecidos(tmp_path):
    gate_path = _init_repo_sintetico(tmp_path)

    # Mesmos segredos do teste anterior
    aws_file = tmp_path / "aws_credentials.txt"
    aws_file.write_text("aws_key=AKIAIOSFODNN7EXAMPLE\n", encoding="utf-8")

    gh_file = tmp_path / "github_token.txt"
    gh_file.write_text("ghp_1234567890abcdefghijklmnopqrstuvwxyz\n", encoding="utf-8")

    # Allowlist no repositorio sintetico catalogando os 2 arquivos
    allowlist_content = {
        "arquivos": {
            "aws_credentials.txt": {
                "motivo": "Fixture sintetico de teste",
                "tipo": "AWS Key"
            },
            "github_token.txt": {
                "motivo": "Fixture sintetico de teste",
                "tipo": "GitHub Token"
            }
        }
    }
    allowlist_path = tmp_path / "gates" / "allowlist_segredos.json"
    allowlist_path.write_text(json.dumps(allowlist_content, indent=2), encoding="utf-8")

    _comitar_tudo(tmp_path)

    res = rodar_gate(gate_path, tmp_path)
    assert res.returncode == 0
    assert "Quality Gate G_SEGREDOS APROVADO (100% OK)!" in res.stdout
    assert "2 achado(s) já catalogado(s) em allowlist_segredos.json" in res.stdout
