# -*- coding: utf-8 -*-
"""
Testes unitários e de integração do Orquestrador Síncrono da Tríade Canônica.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from scripts.orquestrador_sincrono import OrquestradorSincrono


def test_orquestrador_valida_fluxo_invalido():
    with pytest.raises(ValueError, match="Fluxo inválido"):
        OrquestradorSincrono(
            fluxo=4,
            nome="Teste",
            slug="teste",
            dominio="geral",
            pasta="testes/tmp"
        )


def test_orquestrador_dry_run_fluxo_1(tmp_path):
    orq = OrquestradorSincrono(
        fluxo=1,
        nome="Gestao Tarefas",
        slug="gestao-tarefas",
        dominio="produtividade",
        pasta=str(tmp_path / "projeto-teste"),
        dry_run=True
    )
    sucesso = orq.executar_fluxo_completo()
    assert sucesso is True
    assert orq.nome_fluxo == "aidd-pure"


def test_orquestrador_aceita_nomes_canonicos_pure_open_freedom_bridge(tmp_path):
    orq_pure = OrquestradorSincrono(fluxo="pure", nome="P", slug="p", dominio="d", pasta=str(tmp_path/"p"), dry_run=True)
    assert orq_pure.fluxo == 1
    assert orq_pure.nome_fluxo == "aidd-pure"

    orq_open = OrquestradorSincrono(fluxo="open", nome="O", slug="o", dominio="d", pasta=str(tmp_path/"o"), dry_run=True)
    assert orq_open.fluxo == 2
    assert orq_open.nome_fluxo == "aidd-open"

    orq_freedom = OrquestradorSincrono(fluxo="freedom", nome="F", slug="f", dominio="d", pasta=str(tmp_path/"f"), dry_run=True)
    assert orq_freedom.fluxo == 3
    assert orq_freedom.nome_fluxo == "aidd-freedom"

    orq_bridge = OrquestradorSincrono(fluxo="bridge", nome="B", slug="b", dominio="d", pasta=str(tmp_path/"b"), dry_run=True)
    assert orq_bridge.fluxo == 3
    assert orq_bridge.nome_fluxo == "aidd-freedom"



def test_orquestrador_dry_run_fluxo_2(tmp_path):
    orq = OrquestradorSincrono(
        fluxo=2,
        nome="Hub Open Source",
        slug="hub-oss",
        dominio="clinicas",
        pasta=str(tmp_path / "projeto-oss"),
        dry_run=True
    )
    sucesso = orq.executar_fluxo_completo()
    assert sucesso is True


def test_orquestrador_dry_run_fluxo_3(tmp_path):
    orq = OrquestradorSincrono(
        fluxo=3,
        nome="App Lovable Desacoplada",
        slug="app-lovable",
        dominio="saas",
        pasta=str(tmp_path / "projeto-bridge"),
        origem_export=str(tmp_path / "export-lovable"),
        dry_run=True
    )
    sucesso = orq.executar_fluxo_completo()
    assert sucesso is True


def test_orquestrador_aborta_imediatamente_se_etapa_falhar(tmp_path):
    orq = OrquestradorSincrono(
        fluxo=1,
        nome="Falha Teste",
        slug="falha-teste",
        dominio="teste",
        pasta=str(tmp_path / "projeto-falha"),
        dry_run=False
    )
    with patch.object(orq, "_executar_comando", return_value=1):
        sucesso = orq.executar_fluxo_completo()
        assert sucesso is False


def test_orquestrador_valida_schema_handoff(tmp_path):
    orq = OrquestradorSincrono(
        fluxo=1,
        nome="Teste Schema",
        slug="teste-schema",
        dominio="geral",
        pasta=str(tmp_path / "projeto-schema"),
        dry_run=True
    )
    # Schema válido
    valido = orq._validar_schema(
        {
            "versao_schema": "1.0.0",
            "fluxo_alvo": 1,
            "metadados_projeto": {
                "nome": "Teste",
                "slug": "teste",
                "dominio": "geral",
                "descricao": "Descricao longa para validacao de schema"
            },
            "quarteto_sine_qua_non": {
                "swagger": True,
                "webhooks": True,
                "mcp": True,
                "documentacao": True
            },
            "arquitetura_alvo": {
                "padrao_frontend": "nextjs_typescript_tailwind",
                "padrao_backend": "fastapi_modular_vsa",
                "persistencia": "sqlite_wal"
            },
            "modulos_funcionais": [
                {
                    "nome": "Teste",
                    "slug": "teste",
                    "entidades": [
                        {
                            "nome": "Entidade",
                            "campos": [{"nome": "id", "tipo": "integer", "obrigatorio": True}]
                        }
                    ],
                    "regras_negocio": [
                        {"id": "RN01", "descricao": "Regra 1", "criterio_aceitacao": "Critério"}
                    ]
                }
            ]
        },
        "handoff-planner-to-engine.schema.json"
    )
    assert valido is True
