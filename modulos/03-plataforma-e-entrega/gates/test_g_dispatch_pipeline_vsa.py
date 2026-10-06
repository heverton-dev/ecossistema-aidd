# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — TESTE DE PROVA QUE MORDE: test_gate_dispatch_pipeline_vsa.py
=============================================================================
Validação estrita em runtime (Lei #1, #2, #5, #13 / ISSUE-MESO-0003):
  1. Caminho feliz: manifesto conforme atinge exit 0.
  2. Cenários deliberados de violação comprovando que o portão morde (exit 1):
     - Manifesto inexistente.
     - JSON corrompido/malformado.
     - Violação de schema (campos obrigatórios ausentes).
     - Presença de stubs/placeholders (TODO/FIXME/PLACEHOLDER).
     - Comandos de validação triviais (ex: 'exit 0').
     - Dependência referenciada inexistente.
     - Ciclo topológico direto ou indireto.
     - Mecanismo de isolamento divergente de 'git-worktree'.
=============================================================================
"""

import json
import subprocess
import sys
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
GATE_SCRIPT = ROOT_DIR / "gates" / "G_DISPATCH_PIPELINE_VSA.py"


def executar_gate(manifesto_path: Path | None = None) -> subprocess.CompletedProcess:
    """Executa o gate G_DISPATCH_PIPELINE_VSA via subprocess real."""
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


def _gerar_manifesto_valido() -> dict:
    return {
        "versao_schema": "1.0.0",
        "projeto_slug": "app-vsa-conforme",
        "fluxo_alvo": "fluxo_01_generator",
        "grafo_fatias": [
            {
                "slice_id": "slice_auth",
                "modulo_ddd": "Autenticacao",
                "dependencias": [],
                "isolamento": "git-worktree",
                "arquivos_esperados": ["src/slices/auth/router.py"],
                "barreira_validacao": {
                    "comandos_teste": ["pytest tests/slices/test_auth.py"],
                    "quality_gates": ["python gates/G_SAIDA_BINARIA.py"]
                }
            },
            {
                "slice_id": "slice_pedidos",
                "modulo_ddd": "Pedidos",
                "dependencias": ["slice_auth"],
                "isolamento": "git-worktree",
                "arquivos_esperados": ["src/slices/pedidos/router.py"],
                "barreira_validacao": {
                    "comandos_teste": ["pytest tests/slices/test_pedidos.py"],
                    "quality_gates": ["python gates/G_SAIDA_BINARIA.py"]
                }
            }
        ],
        "convergencia_master": {
            "target_branch": "main",
            "merge_strategy": "fast-forward",
            "post_merge_suite": ["python ecossistema.py audit"]
        }
    }


def test_gate_vsa_aprova_manifesto_valido(tmp_path):
    """Caminho feliz: manifesto válido retorna exit 0."""
    manifesto = _gerar_manifesto_valido()
    m_file = tmp_path / "vsa_dispatch.json"
    m_file.write_text(json.dumps(manifesto, indent=2), encoding="utf-8")

    res = executar_gate(m_file)
    assert res.returncode == 0, f"Deveria aprovar manifesto válido: {res.stdout}\n{res.stderr}"
    assert "100% Conforme" in res.stdout


def test_gate_vsa_morde_arquivo_inexistente(tmp_path):
    """Lei #13: Rejeita manifesto inexistente com exit 1."""
    falso = tmp_path / "inexistente_12345.json"
    res = executar_gate(falso)
    assert res.returncode == 1
    assert "Arquivo de manifesto inexistente" in res.stderr


def test_gate_vsa_morde_json_malformado(tmp_path):
    """Lei #13: Rejeita JSON quebrado com exit 1."""
    m_file = tmp_path / "corrompido.json"
    m_file.write_text("{'invalido': True,,}", encoding="utf-8")

    res = executar_gate(m_file)
    assert res.returncode == 1
    assert "JSON malformado" in res.stderr


def test_gate_vsa_morde_violacao_schema_campos_obrigatorios(tmp_path):
    """Lei #13: Rejeita manifesto sem campos obrigatórios com exit 1."""
    manifesto = _gerar_manifesto_valido()
    del manifesto["convergencia_master"]

    m_file = tmp_path / "sem_convergencia.json"
    m_file.write_text(json.dumps(manifesto), encoding="utf-8")

    res = executar_gate(m_file)
    assert res.returncode == 1
    assert "convergencia_master" in res.stderr


def test_gate_vsa_morde_ciclo_topologico(tmp_path):
    """Lei #1 e #13: Detecta ciclo e reprova com exit 1."""
    manifesto = _gerar_manifesto_valido()
    # Cria ciclo direto: slice_auth depende de slice_pedidos
    manifesto["grafo_fatias"][0]["dependencias"] = ["slice_pedidos"]

    m_file = tmp_path / "ciclico.json"
    m_file.write_text(json.dumps(manifesto), encoding="utf-8")

    res = executar_gate(m_file)
    assert res.returncode == 1
    assert "Ciclo de" in res.stderr and "detectado" in res.stderr


def test_gate_vsa_morde_dependencia_inexistente(tmp_path):
    """Lei #13: Rejeita referência a dependência não declarada."""
    manifesto = _gerar_manifesto_valido()
    manifesto["grafo_fatias"][0]["dependencias"] = ["slice_fantasma"]

    m_file = tmp_path / "dep_fantasma.json"
    m_file.write_text(json.dumps(manifesto), encoding="utf-8")

    res = executar_gate(m_file)
    assert res.returncode == 1
    assert "referencia" in res.stderr and "inexistente" in res.stderr


def test_gate_vsa_morde_stub_todo_fixme(tmp_path):
    """Lei #5 e #13: Rejeita qualquer stub textual com exit 1."""
    manifesto = _gerar_manifesto_valido()
    manifesto["grafo_fatias"][0]["modulo_ddd"] = "Modulo TODO Autenticacao"

    m_file = tmp_path / "com_stub.json"
    m_file.write_text(json.dumps(manifesto), encoding="utf-8")

    res = executar_gate(m_file)
    assert res.returncode == 1
    assert "Stub detectado" in res.stderr


def test_gate_vsa_morde_comando_trivial(tmp_path):
    """Lei #5 e #13: Rejeita comandos triviais do tipo 'exit 0'."""
    manifesto = _gerar_manifesto_valido()
    manifesto["grafo_fatias"][0]["barreira_validacao"]["comandos_teste"] = ["exit 0"]

    m_file = tmp_path / "cmd_trivial.json"
    m_file.write_text(json.dumps(manifesto), encoding="utf-8")

    res = executar_gate(m_file)
    assert res.returncode == 1
    assert "Comando trivial detectado" in res.stderr or "Violação de schema" in res.stderr


def test_gate_vsa_morde_isolamento_invalido(tmp_path):
    """Lei #13: Rejeita mecanismo de isolamento diferente de git-worktree."""
    manifesto = _gerar_manifesto_valido()
    manifesto["grafo_fatias"][0]["isolamento"] = "processo-local"

    m_file = tmp_path / "isolamento_errado.json"
    m_file.write_text(json.dumps(manifesto), encoding="utf-8")

    res = executar_gate(m_file)
    assert res.returncode == 1
    assert "isolamento" in res.stderr.lower()


def test_gate_vsa_modo_autodescoberta_exit_0():
    """Valida integridade do gate em modo autodescoberta geral."""
    res = executar_gate()
    assert res.returncode == 0
    assert "APROVADO (Exit 0)" in res.stdout
