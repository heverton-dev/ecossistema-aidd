# -*- coding: utf-8 -*-
"""
Validação formal do Schema Canônico de Contrato de Handoff de Execução.
Conforme: docs/issues/pipeline-orquestracao-triade/01-schema-contrato-handoff-execucao.md
"""

import json
from pathlib import Path
import jsonschema
import pytest

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "componentes" / "compartilhado" / "specs" / "handoff-execucao.schema.json"


@pytest.fixture(scope="module")
def schema():
    assert SCHEMA_PATH.exists(), f"Schema não encontrado em: {SCHEMA_PATH}"
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_data = json.load(f)
    jsonschema.Draft7Validator.check_schema(schema_data)
    return schema_data


@pytest.fixture(scope="module")
def validator(schema):
    return jsonschema.Draft7Validator(schema)


def test_schema_syntax_and_draft7_compliance(schema):
    """Verifica se o schema cumpre estritamente Draft7Validator."""
    jsonschema.Draft7Validator.check_schema(schema)
    assert schema["title"] == "HandoffExecucaoSchema"
    assert "versao_schema" in schema["required"]


def test_positive_fixture_ptbr(validator):
    """Manifesto positivo usando nomenclatura canônica em PT-BR (conforme issue)."""
    manifesto = {
        "versao_schema": "1.0.0",
        "origem_plano": "evolucao",
        "fluxo_alvo": "evolution",
        "meta": {
            "nome_projeto": "Evolucao Orquestrador",
            "repositorio_alvo": "ecossistema-aidd",
            "timestamp_execucao": "2026-09-21T10:00:00Z",
            "iniciativa_id": "PLAN-0001",
            "descricao": "Migracao e unificacao do pipeline de execucao"
        },
        "fase_paralela_assincrona": [
            {
                "id": "TICKET-01",
                "titulo": "Implementar parser isolado de tickets",
                "arquivos_alvo": ["scripts/parser.py", "tests/test_parser.py"],
                "comando_validacao": "pytest tests/test_parser.py -q",
                "isolamento": "git-worktree"
            }
        ],
        "barreira_sincronizacao": [
            "python ecossistema.py audit"
        ],
        "fase_sequencial_sincrona": [
            {
                "id": "TICKET-02",
                "titulo": "Registrar comando unificado no CLI",
                "arquivos_alvo": ["ecossistema.py"],
                "comando_validacao": "python ecossistema.py --help",
                "isolamento": "nenhum",
                "blocked_by": ["TICKET-01"]
            }
        ]
    }
    validator.validate(manifesto)


def test_positive_fixture_en_prompt(validator):
    """Manifesto positivo usando nomenclatura alternativa conforme prompt."""
    manifesto = {
        "versao_schema": "1.0.0",
        "origem_plano": "criacao",
        "fluxo_alvo": "pure",
        "meta": {
            "nome_projeto": "Novo Monolito VSA",
            "repositorio_alvo": "app-pure",
            "timestamp_execucao": "2026-09-21",
            "descricao": "Construcao de nova aplicacao do zero puro"
        },
        "parallel_async_steps": [
            {
                "id": "SLICE-01",
                "title": "Gerar modulo de autenticacao",
                "target_files": ["src/auth/service.py", "tests/test_auth.py"],
                "command_red": "pytest tests/test_auth.py",
                "command_green": "pytest tests/test_auth.py",
                "validation_gate": "pytest tests/test_auth.py -v"
            }
        ],
        "join_barrier": [
            "gates/G_SAIDA_BINARIA.py"
        ],
        "sequential_sync_steps": [
            {
                "id": "SLICE-02",
                "title": "Configurar rotas e quarteto sine qua non",
                "target_files": ["src/main.py"],
                "validation_gate": "python -m unittest discover tests"
            }
        ]
    }
    validator.validate(manifesto)


def test_negative_rejects_missing_required_root_keys(validator):
    """Rejeita ausência de chaves raiz obrigatórias."""
    manifesto = {
        "origem_plano": "evolucao",
        "meta": {
            "nome_projeto": "Teste",
            "repositorio_alvo": "repo",
            "timestamp_execucao": "2026-09-21"
        }
    }
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(manifesto)


def test_negative_rejects_invalid_fluxo_alvo(validator):
    """Rejeita fluxo_alvo fora do catálogo permitido."""
    manifesto = {
        "versao_schema": "1.0.0",
        "origem_plano": "evolucao",
        "fluxo_alvo": "fluxo_inexistente",
        "meta": {
            "nome_projeto": "Teste",
            "repositorio_alvo": "repo",
            "timestamp_execucao": "2026-09-21"
        },
        "fase_sequencial_sincrona": [
            {
                "id": "TICKET-01",
                "titulo": "Ajuste real",
                "arquivos_alvo": ["file.py"],
                "comando_validacao": "pytest tests"
            }
        ]
    }
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(manifesto)


def test_negative_rejects_empty_phases_zero_stubs(validator):
    """Zero stubs: rejeita se ambas as fases de execução estiverem ausentes ou vazias."""
    manifesto = {
        "versao_schema": "1.0.0",
        "origem_plano": "evolucao",
        "fluxo_alvo": "evolution",
        "meta": {
            "nome_projeto": "Teste",
            "repositorio_alvo": "repo",
            "timestamp_execucao": "2026-09-21"
        },
        "fase_paralela_assincrona": [],
        "fase_sequencial_sincrona": []
    }
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(manifesto)


def test_negative_rejects_ticket_stubs_and_placeholders(validator):
    """Zero stubs: rejeita tickets com TODO, FIXME, PLACEHOLDER ou sem comando de validação."""
    manifesto_com_placeholder = {
        "versao_schema": "1.0.0",
        "origem_plano": "evolucao",
        "fluxo_alvo": "evolution",
        "meta": {
            "nome_projeto": "Teste",
            "repositorio_alvo": "repo",
            "timestamp_execucao": "2026-09-21"
        },
        "fase_sequencial_sincrona": [
            {
                "id": "TICKET-01",
                "titulo": "TODO: implementar depois",
                "arquivos_alvo": ["src/app.py"],
                "comando_validacao": "pytest tests"
            }
        ]
    }
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(manifesto_com_placeholder)


def test_negative_rejects_ticket_without_validation_command(validator):
    """Rejeita tickets sem comando de validação determinístico."""
    manifesto_sem_validacao = {
        "versao_schema": "1.0.0",
        "origem_plano": "evolucao",
        "fluxo_alvo": "evolution",
        "meta": {
            "nome_projeto": "Teste",
            "repositorio_alvo": "repo",
            "timestamp_execucao": "2026-09-21"
        },
        "fase_sequencial_sincrona": [
            {
                "id": "TICKET-01",
                "titulo": "Ajustar configuracao",
                "arquivos_alvo": ["src/config.py"]
            }
        ]
    }
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(manifesto_sem_validacao)


def test_negative_rejects_ticket_empty_target_files(validator):
    """Rejeita tickets com lista de arquivos vazia."""
    manifesto_sem_arquivos = {
        "versao_schema": "1.0.0",
        "origem_plano": "evolucao",
        "fluxo_alvo": "evolution",
        "meta": {
            "nome_projeto": "Teste",
            "repositorio_alvo": "repo",
            "timestamp_execucao": "2026-09-21"
        },
        "fase_sequencial_sincrona": [
            {
                "id": "TICKET-01",
                "titulo": "Ajustar configuracao",
                "arquivos_alvo": [],
                "comando_validacao": "pytest"
            }
        ]
    }
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(manifesto_sem_arquivos)
