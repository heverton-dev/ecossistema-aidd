# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — TESTE DE PROVA QUE MORDE: test_gate_pipeline_handoff.py
=============================================================================
Validação estrita em runtime (Lei #1, #2, #5, #13 / ISSUE-PIPE-0002):
  1. Caminho feliz: manifesto conforme atinge exit 0.
  2. Cenários deliberados de falha comprovando que o portão morde (exit 1):
     - Manifesto inexistente.
     - JSON corrompido/malformado.
     - Violação de schema (campos obrigatórios ausentes).
     - Presença de stubs/placeholders (TODO/FIXME/PLACEHOLDER).
     - Alvos inresolvíveis (diretório pai inexistente).
     - Gates inexistentes na barreira de sincronização.
     - Comandos de validação triviais (stubs tipo 'exit 0').
=============================================================================
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
GATE_SCRIPT = ROOT_DIR / "gates" / "G_PIPELINE_HANDOFF.py"


def executar_gate(manifesto_path: Path | None = None) -> subprocess.CompletedProcess:
    """Executa o gate G_PIPELINE_HANDOFF via subprocess real."""
    cmd = [sys.executable, str(GATE_SCRIPT)]
    if manifesto_path:
        cmd.extend(["--manifesto", str(manifesto_path)])

    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(ROOT_DIR),
        encoding="utf-8",
        errors="replace",
    )


def test_aprova_manifesto_valido_conforme(tmp_path):
    """Caminho feliz: manifesto válido com arquivo alvo e gate existentes retorna exit 0."""
    arquivo_teste = ROOT_DIR / "tests" / "test_gate_pipeline_handoff.py"
    manifesto = {
        "versao_schema": "1.0.0",
        "origem_plano": "evolucao",
        "fluxo_alvo": "evolution",
        "meta": {
            "nome_projeto": "Validacao Pipeline",
            "repositorio_alvo": "ecossistema-aidd",
            "timestamp_execucao": "2026-09-21T10:00:00Z",
            "iniciativa_id": "ISSUE-PIPE-0002",
            "descricao": "Execucao de testes do quality gate de pipeline"
        },
        "barreira_sincronizacao": [
            "gates/G_SAIDA_BINARIA.py"
        ],
        "fase_sequencial_sincrona": [
            {
                "id": "STEP-01",
                "titulo": "Executar validacao dos gates",
                "arquivos_alvo": [str(arquivo_teste.relative_to(ROOT_DIR))],
                "comando_validacao": "pytest tests/test_gate_pipeline_handoff.py",
                "isolamento": "processo-isolado"
            }
        ]
    }

    manifesto_file = tmp_path / "manifesto_valido.json"
    manifesto_file.write_text(json.dumps(manifesto, indent=2), encoding="utf-8")

    res = executar_gate(manifesto_file)
    assert res.returncode == 0, f"Deveria aprovar com exit 0, mas falhou:\n{res.stdout}\n{res.stderr}"
    assert "100% conforme" in res.stdout


def test_reprova_manifesto_inexistente():
    """Prova que o portão morde: arquivo inexistente retorna exit 1."""
    manifesto_fantasma = ROOT_DIR / "caminho_inexistente" / "inexistente.json"
    res = executar_gate(manifesto_fantasma)
    assert res.returncode == 1, f"Deveria falhar com exit 1, retornou {res.returncode}"
    assert "não encontrado" in res.stdout or "não encontrado" in res.stderr


def test_reprova_json_corrompido(tmp_path):
    """Prova que o portão morde: arquivo com sintaxe JSON inválida retorna exit 1."""
    manifesto_quebrado = tmp_path / "quebrado.json"
    manifesto_quebrado.write_text("{ versao_schema: INVALID_JSON ", encoding="utf-8")

    res = executar_gate(manifesto_quebrado)
    assert res.returncode == 1, f"Deveria falhar com exit 1, retornou {res.returncode}"
    assert "malformado" in res.stdout or "JSONDecodeError" in res.stdout


def test_reprova_campos_obrigatorios_ausentes(tmp_path):
    """Prova que o portão morde: schema violation (falta versao_schema e meta) retorna exit 1."""
    manifesto_incompleto = {
        "origem_plano": "evolucao",
        "fluxo_alvo": "evolution"
    }
    manifesto_file = tmp_path / "incompleto.json"
    manifesto_file.write_text(json.dumps(manifesto_incompleto), encoding="utf-8")

    res = executar_gate(manifesto_file)
    assert res.returncode == 1, f"Deveria falhar com exit 1, retornou {res.returncode}"
    assert "Erro no schema" in res.stdout


def test_reprova_stubs_e_placeholders(tmp_path):
    """Prova que o portão morde: TODO/FIXME/PLACEHOLDER em tickets retorna exit 1."""
    manifesto_stub = {
        "versao_schema": "1.0.0",
        "origem_plano": "evolucao",
        "fluxo_alvo": "evolution",
        "meta": {
            "nome_projeto": "Projeto Stub",
            "repositorio_alvo": "ecossistema-aidd",
            "timestamp_execucao": "2026-09-21T10:00:00Z",
            "descricao": "Descricao valida sem stubs"
        },
        "fase_sequencial_sincrona": [
            {
                "id": "STEP-01",
                "titulo": "TODO: implementar depois",
                "arquivos_alvo": ["gates/G_PIPELINE_HANDOFF.py"],
                "comando_validacao": "pytest tests"
            }
        ]
    }
    manifesto_file = tmp_path / "com_stubs.json"
    manifesto_file.write_text(json.dumps(manifesto_stub), encoding="utf-8")

    res = executar_gate(manifesto_file)
    assert res.returncode == 1, f"Deveria falhar com exit 1, retornou {res.returncode}"
    assert "Stub ou placeholder proibido" in res.stdout or "TODO" in res.stdout


def test_reprova_alvo_com_diretorio_pai_inexistente(tmp_path):
    """Prova que o portão morde: target_file em diretório inexistente/inresolvível retorna exit 1."""
    manifesto_alvo_invalido = {
        "versao_schema": "1.0.0",
        "origem_plano": "evolucao",
        "fluxo_alvo": "evolution",
        "meta": {
            "nome_projeto": "Projeto Alvo Invalido",
            "repositorio_alvo": "ecossistema-aidd",
            "timestamp_execucao": "2026-09-21T10:00:00Z",
            "descricao": "Descricao valida"
        },
        "fase_sequencial_sincrona": [
            {
                "id": "STEP-01",
                "titulo": "Criar arquivo em arvore inexistente",
                "arquivos_alvo": ["pasta_totalmente_inexistente_123/subpasta_456/novo_arquivo.py"],
                "comando_validacao": "pytest tests"
            }
        ]
    }
    manifesto_file = tmp_path / "alvo_invalido.json"
    manifesto_file.write_text(json.dumps(manifesto_alvo_invalido), encoding="utf-8")

    res = executar_gate(manifesto_file)
    assert res.returncode == 1, f"Deveria falhar com exit 1, retornou {res.returncode}"
    assert "não é resolvível/existente" in res.stdout


def test_reprova_gate_inexistente_na_barreira(tmp_path):
    """Prova que o portão morde: gate ausente na barreira de sincronização retorna exit 1."""
    manifesto_gate_fantasma = {
        "versao_schema": "1.0.0",
        "origem_plano": "evolucao",
        "fluxo_alvo": "evolution",
        "meta": {
            "nome_projeto": "Projeto Gate Fantasma",
            "repositorio_alvo": "ecossistema-aidd",
            "timestamp_execucao": "2026-09-21T10:00:00Z",
            "descricao": "Descricao valida"
        },
        "barreira_sincronizacao": [
            "gates/G_INEXISTENTE_TOTALMENTE_FANTASMA.py"
        ],
        "fase_sequencial_sincrona": [
            {
                "id": "STEP-01",
                "titulo": "Ticket valido com arquivo existente",
                "arquivos_alvo": ["gates/G_PIPELINE_HANDOFF.py"],
                "comando_validacao": "pytest tests"
            }
        ]
    }
    manifesto_file = tmp_path / "gate_fantasma.json"
    manifesto_file.write_text(json.dumps(manifesto_gate_fantasma), encoding="utf-8")

    res = executar_gate(manifesto_file)
    assert res.returncode == 1, f"Deveria falhar com exit 1, retornou {res.returncode}"
    assert "Gate ou script referenciado na barreira não foi encontrado" in res.stdout


def test_reprova_comando_validacao_trivial(tmp_path):
    """Prova que o portão morde: comando stub tipo 'exit 0' retorna exit 1."""
    manifesto_cmd_trivial = {
        "versao_schema": "1.0.0",
        "origem_plano": "evolucao",
        "fluxo_alvo": "evolution",
        "meta": {
            "nome_projeto": "Projeto Cmd Trivial",
            "repositorio_alvo": "ecossistema-aidd",
            "timestamp_execucao": "2026-09-21T10:00:00Z",
            "descricao": "Descricao valida"
        },
        "fase_sequencial_sincrona": [
            {
                "id": "STEP-01",
                "titulo": "Ticket com comando trivial",
                "arquivos_alvo": ["gates/G_PIPELINE_HANDOFF.py"],
                "comando_validacao": "exit 0"
            }
        ]
    }
    manifesto_file = tmp_path / "cmd_trivial.json"
    manifesto_file.write_text(json.dumps(manifesto_cmd_trivial), encoding="utf-8")

    res = executar_gate(manifesto_file)
    assert res.returncode == 1, f"Deveria falhar com exit 1, retornou {res.returncode}"
    assert "Comando de validação trivial proibido" in res.stdout or "exit 0" in res.stdout
