# -*- coding: utf-8 -*-
"""
Testes do gate G_SEGREDOS — valida a delegação ao detect-secrets (Yelp)
executando o gate real, via subprocess, contra repositórios git sintéticos
isolados. O baseline usado em cada cenário é gerado pelo próprio
detect-secrets (nunca fabricado à mão), reproduzindo o fluxo real de
scan -> baseline -> gate.
"""

import os
import shutil
import subprocess
import sys

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


def _gerar_baseline_real(root_dir):
    """Roda o detect-secrets de verdade contra o repositorio sintetico e grava o baseline."""
    resultado = subprocess.run(
        [sys.executable, "-m", "detect_secrets", "scan"],
        cwd=root_dir,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    baseline_path = os.path.join(root_dir, ".secrets.baseline")
    with open(baseline_path, "w", encoding="utf-8") as f:
        f.write(resultado.stdout)
    return baseline_path


def test_repo_limpo_aprova(tmp_path):
    gate_path = _init_repo_sintetico(tmp_path)
    arquivo_ok = tmp_path / "README.md"
    arquivo_ok.write_text("# Repositorio Limpo\nNenhum segredo aqui.", encoding="utf-8")
    _comitar_tudo(tmp_path)

    res = rodar_gate(gate_path, tmp_path)
    assert res.returncode == 0
    assert "Quality Gate G_SEGREDOS APROVADO (100% OK)!" in res.stdout


def test_falha_com_segredo_novo_nao_catalogado(tmp_path):
    gate_path = _init_repo_sintetico(tmp_path)

    aws_file = tmp_path / "aws_credentials.txt"
    aws_file.write_text("aws_key=AKIAIOSFODNN7EXAMPLE\n", encoding="utf-8")
    gh_file = tmp_path / "github_token.txt"
    gh_file.write_text("ghp_1234567890abcdefghijklmnopqrstuvwxyz\n", encoding="utf-8")
    _comitar_tudo(tmp_path)

    # Sem baseline: tolerancia zero, qualquer achado do detect-secrets reprova.
    res = rodar_gate(gate_path, tmp_path)
    assert res.returncode == 1
    assert "Quality Gate REPROVADO" in res.stdout
    assert "AWS Access Key" in res.stdout


def test_baseline_autoriza_segredo_ja_catalogado(tmp_path):
    gate_path = _init_repo_sintetico(tmp_path)

    aws_file = tmp_path / "aws_credentials.txt"
    aws_file.write_text("aws_key=AKIAIOSFODNN7EXAMPLE\n", encoding="utf-8")
    _comitar_tudo(tmp_path)

    # Gera o baseline real (fluxo: scan -> baseline) catalogando o achado acima.
    _gerar_baseline_real(tmp_path)
    _comitar_tudo(tmp_path, msg="Adiciona baseline")

    res = rodar_gate(gate_path, tmp_path)
    assert res.returncode == 0
    assert "Quality Gate G_SEGREDOS APROVADO (100% OK)!" in res.stdout


def test_baseline_nao_esconde_segredo_novo_fora_do_baseline(tmp_path):
    gate_path = _init_repo_sintetico(tmp_path)

    aws_file = tmp_path / "aws_credentials.txt"
    aws_file.write_text("aws_key=AKIAIOSFODNN7EXAMPLE\n", encoding="utf-8")
    _comitar_tudo(tmp_path)
    _gerar_baseline_real(tmp_path)
    _comitar_tudo(tmp_path, msg="Adiciona baseline")

    # Introduz um segredo novo, de tipo diferente, que o baseline nao cobre.
    gh_file = tmp_path / "github_token.txt"
    gh_file.write_text("ghp_1234567890abcdefghijklmnopqrstuvwxyz\n", encoding="utf-8")
    _comitar_tudo(tmp_path, msg="Segredo novo nao catalogado")

    res = rodar_gate(gate_path, tmp_path)
    assert res.returncode == 1
    assert "Quality Gate REPROVADO" in res.stdout
