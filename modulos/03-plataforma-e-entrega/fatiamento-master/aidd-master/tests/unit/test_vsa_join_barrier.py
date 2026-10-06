# -*- coding: utf-8 -*-
"""
Testes Unitários: Barreira de Validação e Convergência Master (ISSUE-MESO-0006)
"""
import json
import os
import subprocess
import sys
from pathlib import Path
import pytest

MASTER_DIR = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = MASTER_DIR / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from vsa_join_barrier import (
    executar_barreira_fatia,
    executar_convergencia_master,
    validar_fronteiras_fatia,
    _calcular_sha256,
)


def test_barreira_fatia_aprova_fatia_conforme(tmp_path):
    """Caminho feliz: fatia com testes e gates válidos passa na barreira."""
    # Inicializa repo git dummy para suportar git status
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(tmp_path), check=True)

    # Cria arquivo dentro da fronteira autorizada
    slice_dir = tmp_path / "src" / "slices" / "auth"
    slice_dir.mkdir(parents=True, exist_ok=True)
    (slice_dir / "router.py").write_text("# ok", encoding="utf-8")

    slice_info = {
        "slice_id": "slice_auth",
        "modulo_ddd": "Autenticacao",
        "barreira_validacao": {
            "comandos_teste": [f'"{sys.executable}" -c "print(\'teste ok\')"'],
            "quality_gates": [f'"{sys.executable}" -c "print(\'gate ok\')"'],
        }
    }

    aprovado, erros = executar_barreira_fatia(
        worktree_path=tmp_path,
        slice_info=slice_info,
        dry_run=False,
        verbose=False,
    )
    assert aprovado is True, f"Erros retornados: {erros}"
    assert len(erros) == 0


def test_barreira_fatia_bloqueia_violacao_de_fronteira(tmp_path):
    """Lei #13: Fatia que tenta escrever fora de src/slices/<id> é bloqueada."""
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True, check=True)

    # Cria arquivo PROIBIDO fora da fronteira da fatia
    pasta_proibida = tmp_path / "src" / "core"
    pasta_proibida.mkdir(parents=True, exist_ok=True)
    (pasta_proibida / "config_central.py").write_text("# invasao", encoding="utf-8")

    slice_info = {
        "slice_id": "slice_pagamentos",
        "modulo_ddd": "Pagamentos",
        "barreira_validacao": {
            "comandos_teste": [],
            "quality_gates": [],
        }
    }

    aprovado, erros = executar_barreira_fatia(
        worktree_path=tmp_path,
        slice_info=slice_info,
        dry_run=False,
        verbose=False,
    )
    assert aprovado is False
    assert any("Violação de fronteira" in e for e in erros)


def test_barreira_fatia_bloqueia_teste_falho(tmp_path):
    """Lei #2: Comando de teste com retorno diferente de 0 reprova a fatia."""
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True, check=True)

    slice_info = {
        "slice_id": "slice_pedidos",
        "modulo_ddd": "Pedidos",
        "barreira_validacao": {
            "comandos_teste": [f"{sys.executable} -c 'import sys; sys.exit(1)'"],
            "quality_gates": [],
        }
    }

    aprovado, erros = executar_barreira_fatia(
        worktree_path=tmp_path,
        slice_info=slice_info,
        dry_run=False,
        verbose=False,
    )
    assert aprovado is False
    assert any("Falha no teste" in e for e in erros)


def test_convergencia_master_agrega_roteadores_e_manifesto_enterprise(tmp_path):
    """Convergência Master gera router_registry.py e handoff_enterprise.json com SHA-256."""
    # Cria fatias simuladas
    slice_auth = tmp_path / "src" / "slices" / "auth"
    slice_auth.mkdir(parents=True, exist_ok=True)
    (slice_auth / "router.py").write_text("# router auth", encoding="utf-8")

    slice_pedidos = tmp_path / "src" / "slices" / "pedidos"
    slice_pedidos.mkdir(parents=True, exist_ok=True)
    (slice_pedidos / "router.py").write_text("# router pedidos", encoding="utf-8")

    slices_aprovadas = [
        {"slice_id": "slice_auth", "modulo_ddd": "Auth"},
        {"slice_id": "slice_pedidos", "modulo_ddd": "Pedidos"},
    ]

    sucesso, erros = executar_convergencia_master(
        target_repo=tmp_path,
        slices_aprovadas=slices_aprovadas,
        target_branch="main",
        dry_run=False,
        verbose=False,
    )
    assert sucesso is True
    assert len(erros) == 0

    # 1. Verifica agregação no Monólito Modular
    registry_file = tmp_path / "src" / "core" / "router_registry.py"
    assert registry_file.is_file()
    conteudo_reg = registry_file.read_text(encoding="utf-8")
    assert '"auth": auth_router' in conteudo_reg
    assert '"pedidos": pedidos_router' in conteudo_reg

    # 2. Verifica manifesto enterprise com SHA-256
    manifesto_ent = tmp_path / ".aidd" / "enterprise" / "handoff_enterprise.json"
    assert manifesto_ent.is_file()
    with open(manifesto_ent, "r", encoding="utf-8") as f:
        dados_ent = json.load(f)

    assert dados_ent["destino"] == "aidd-enterprise"
    assert dados_ent["total_fatias_integradas"] == 2
    assert len(dados_ent["fatias"][0]["artefatos"]) >= 1
    assert "sha256" in dados_ent["fatias"][0]["artefatos"][0]
