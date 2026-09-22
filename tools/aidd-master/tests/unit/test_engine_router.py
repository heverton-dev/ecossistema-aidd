# -*- coding: utf-8 -*-
"""
Testes Unitários: Roteador Especialista de Engines da Tríade (ISSUE-MESO-0005)
"""
import json
import os
import sys
from pathlib import Path
import pytest

MASTER_DIR = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = MASTER_DIR / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from engine_router import despachar_fatia, injetar_quarteto_sine_qua_non


def test_roteador_fluxo_01_generator_cria_arquivos_e_quarteto(tmp_path):
    """Fluxo 01 (Pure): Gera VSA completo (models, service, router, test) com Quarteto Sine Qua Non."""
    slice_info = {
        "slice_id": "slice_usuarios",
        "modulo_ddd": "GestaoUsuarios",
        "dependencias": [],
        "isolamento": "git-worktree",
        "arquivos_esperados": ["src/slices/usuarios/router.py"],
        "barreira_validacao": {
            "comandos_teste": ["pytest tests/slices/test_usuarios.py"],
            "quality_gates": ["python gates/G_SAIDA_BINARIA.py"]
        }
    }

    sucesso = despachar_fatia(
        slice_info=slice_info,
        fluxo="fluxo_01_generator",
        worktree_path=tmp_path,
        dry_run=False,
        verbose=False,
    )
    assert sucesso is True

    slice_dir = tmp_path / "src" / "slices" / "usuarios"
    assert (slice_dir / "models.py").is_file()
    assert (slice_dir / "service.py").is_file()
    assert (slice_dir / "router.py").is_file()
    assert (tmp_path / "tests" / "slices" / "test_usuarios.py").is_file()

    # Verifica os 4 pilares do Quarteto Sine Qua Non (Lei #10)
    assert (slice_dir / "docs" / "openapi.json").is_file()
    assert (slice_dir / "webhooks.json").is_file()
    assert (slice_dir / "mcp_tools.json").is_file()
    assert (slice_dir / "docs" / "guia" / "README.md").is_file()

    # Valida conteúdo do OpenAPI
    with open(slice_dir / "docs" / "openapi.json", "r", encoding="utf-8") as f:
        openapi_spec = json.load(f)
    assert openapi_spec["openapi"] == "3.1.0"
    assert "/usuarios" in openapi_spec["paths"]


def test_roteador_fluxo_02_factory_cria_integracao_e_quarteto(tmp_path):
    """Fluxo 02 (Open): Gera rotas de integração, reverse proxy e Quarteto."""
    slice_info = {
        "slice_id": "slice_notificacoes",
        "modulo_ddd": "Notificacoes",
        "dependencias": [],
        "isolamento": "git-worktree",
        "arquivos_esperados": ["src/slices/notificacoes/router.py"],
        "barreira_validacao": {
            "comandos_teste": ["pytest tests/slices/test_notificacoes.py"],
            "quality_gates": ["python gates/G_SAIDA_BINARIA.py"]
        }
    }

    sucesso = despachar_fatia(
        slice_info=slice_info,
        fluxo="fluxo_02_factory",
        worktree_path=tmp_path,
        dry_run=False,
        verbose=False,
    )
    assert sucesso is True

    slice_dir = tmp_path / "src" / "slices" / "notificacoes"
    assert (slice_dir / "adapter.py").is_file()
    assert (slice_dir / "router.py").is_file()
    assert (slice_dir / "webhooks.json").is_file()
    assert (slice_dir / "mcp_tools.json").is_file()
    assert (slice_dir / "docs" / "guia" / "README.md").is_file()


def test_roteador_fluxo_03_bridge_cria_desacoplamento_e_quarteto(tmp_path):
    """Fluxo 03 (Freedom): Gera desacoplamento soberano low-code e Quarteto."""
    slice_info = {
        "slice_id": "slice_faturamento",
        "modulo_ddd": "Faturamento",
        "dependencias": [],
        "isolamento": "git-worktree",
        "arquivos_esperados": ["src/slices/faturamento/router.py"],
        "barreira_validacao": {
            "comandos_teste": ["pytest tests/slices/test_faturamento.py"],
            "quality_gates": ["python gates/G_SAIDA_BINARIA.py"]
        }
    }

    sucesso = despachar_fatia(
        slice_info=slice_info,
        fluxo="fluxo_03_bridge",
        worktree_path=tmp_path,
        dry_run=False,
        verbose=False,
    )
    assert sucesso is True

    slice_dir = tmp_path / "src" / "slices" / "faturamento"
    assert (slice_dir / "repository.py").is_file()
    assert (slice_dir / "router.py").is_file()
    assert (slice_dir / "docs" / "openapi.json").is_file()
    assert (slice_dir / "webhooks.json").is_file()


def test_roteador_rejeita_fluxo_invalido(tmp_path):
    """Rejeita fluxos fora da Tríade Canônica com retorno False."""
    slice_info = {"slice_id": "slice_invalido", "modulo_ddd": "Invalido"}
    sucesso = despachar_fatia(
        slice_info=slice_info,
        fluxo="fluxo_desconhecido_xyz",
        worktree_path=tmp_path,
        dry_run=False,
        verbose=False,
    )
    assert sucesso is False


def test_despachar_fatia_dry_run(tmp_path):
    """Em modo dry-run, retorna True sem escrever arquivos em disco."""
    slice_info = {"slice_id": "slice_dryrun", "modulo_ddd": "DryRun"}
    sucesso = despachar_fatia(
        slice_info=slice_info,
        fluxo="fluxo_01_generator",
        worktree_path=tmp_path,
        dry_run=True,
        verbose=False,
    )
    assert sucesso is True
    assert not (tmp_path / "src" / "slices" / "dryrun").exists()
