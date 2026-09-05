#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes de cobertura CLI para pipeline_completo.py (main())

Cobre o shell da CLI:
- Argparse e validação de argumentos obrigatórios
- Preflight LLM e interrupção limpa antes de chamadas caras
- Tratamento de LLMNaoConfiguradoException sem vazamento de stack trace
- Fluxo de sucesso com código de saída 0 e exibição de métricas/score
- Fluxo de falha com código de saída 1 e identificação da fase que falhou
"""

import sys
import importlib.util
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PIPELINE_PATH = PROJECT_ROOT / 'scripts' / 'pipeline_completo.py'
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))


@pytest.fixture
def pipeline_mod():
    """Carrega o módulo pipeline_completo.py."""
    spec = importlib.util.spec_from_file_location('pipeline_completo', PIPELINE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_cli_argparse_sem_pasta_rejeita(pipeline_mod, monkeypatch):
    """1.1: Valida que a omissão de --pasta causa SystemExit com código não-zero pelo argparse."""
    monkeypatch.setattr(sys, 'argv', ['pipeline_completo.py', 'Minha ideia de app'])
    with pytest.raises(SystemExit) as exc_info:
        pipeline_mod.main()
    assert exc_info.value.code != 0


def test_cli_preflight_falha_nao_chama_executar_pipeline(pipeline_mod, monkeypatch, capsys, tmp_path):
    """1.2: Preflight reprovado encerra com exit 1 e NUNCA invoca executar_pipeline."""
    monkeypatch.setattr(pipeline_mod, 'verificar_llm_pronto', lambda: (False, "test reason"))

    def fake_executar(*args, **kwargs):
        raise AssertionError("executar_pipeline NUNCA deveria ter sido chamada quando o preflight falha!")

    monkeypatch.setattr(pipeline_mod, 'executar_pipeline', fake_executar)
    monkeypatch.setattr(sys, 'argv', ['pipeline_completo.py', 'Ideia Teste', '--pasta', str(tmp_path)])

    with pytest.raises(SystemExit) as exc_info:
        pipeline_mod.main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    saida = captured.out + captured.err
    assert "PREFLIGHT FALHOU — test reason" in saida


def test_cli_trata_llm_nao_configurado_exception(pipeline_mod, monkeypatch, capsys, tmp_path):
    """1.3: LLMNaoConfiguradoException resulta em exit 1 com mensagem amigável e sem stack trace cru."""
    monkeypatch.setattr(pipeline_mod, 'verificar_llm_pronto', lambda: (True, "ok"))

    def fake_executar(*args, **kwargs):
        raise pipeline_mod.LLMNaoConfiguradoException("test friendly message", "technical detail")

    monkeypatch.setattr(pipeline_mod, 'executar_pipeline', fake_executar)
    monkeypatch.setattr(sys, 'argv', ['pipeline_completo.py', 'Ideia Teste', '--pasta', str(tmp_path)])

    with pytest.raises(SystemExit) as exc_info:
        pipeline_mod.main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    saida = captured.out + captured.err
    assert "test friendly message" in saida
    assert "Traceback" not in saida
    assert "technical detail" not in saida


def test_cli_sucesso_status_completo(pipeline_mod, monkeypatch, capsys, tmp_path):
    """1.4: Pipeline com status COMPLETO sai com código 0 e exibe o score final."""
    monkeypatch.setattr(pipeline_mod, 'verificar_llm_pronto', lambda: (True, "ok"))

    resultado_mock = {
        'status': 'COMPLETO',
        'score_final': 92,
        'fleet': {'modo': 'x', 'total_detectados': 1},
        'context_purge': {},
        'duracao_segundos': 1.0,
    }
    monkeypatch.setattr(pipeline_mod, 'executar_pipeline', lambda *args, **kwargs: resultado_mock)
    monkeypatch.setattr(sys, 'argv', ['pipeline_completo.py', 'Ideia Teste', '--pasta', str(tmp_path)])

    with pytest.raises(SystemExit) as exc_info:
        pipeline_mod.main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    saida = captured.out + captured.err
    assert "PIPELINE COMPLETO — score final: 92/100" in saida


def test_cli_falha_fase_especifica(pipeline_mod, monkeypatch, capsys, tmp_path):
    """1.5: Pipeline com falha em fase sai com código 1 e identifica a fase que falhou."""
    monkeypatch.setattr(pipeline_mod, 'verificar_llm_pronto', lambda: (True, "ok"))

    resultado_mock = {
        'status': 'FALHOU',
        'fase_que_falhou': 'phase_02_analysis',
        'fleet': {},
        'context_purge': {},
        'duracao_segundos': 1.0,
    }
    monkeypatch.setattr(pipeline_mod, 'executar_pipeline', lambda *args, **kwargs: resultado_mock)
    monkeypatch.setattr(sys, 'argv', ['pipeline_completo.py', 'Ideia Teste', '--pasta', str(tmp_path)])

    with pytest.raises(SystemExit) as exc_info:
        pipeline_mod.main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    saida = captured.out + captured.err
    assert "PIPELINE FALHOU na phase_02_analysis" in saida
