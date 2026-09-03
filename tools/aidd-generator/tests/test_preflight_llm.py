# -*- coding: utf-8 -*-
"""
Testes para o pré-voo LLM (verificar_llm_pronto) em preflight_llm.py.

Cenários cobertos:
  1. LLM_MODEL ausente → falha com mensagem orientativa
  2. LLM_MODEL presente mas credencial do provedor ausente → falha
  3. LLM_MODEL presente com credencial → sucesso
  4. LLM_MODEL com prefixo desconhecido (sem mapeamento) → sucesso (sem checar chave)
  5. Pipeline inteiro recusa rodar sem LLM (main exit code 1)
"""

import sys
import importlib
from pathlib import Path

import pytest

# prelight_llm.py é leve — não carrega phases, seguro para importar direto
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / 'scripts'
sys.path.insert(0, str(_SCRIPTS_DIR))

import preflight_llm  # noqa: E402


def _reload():
    """Recarrega o módulo para testes isolados."""
    return importlib.reload(preflight_llm)


# =============================================================================
# 1. LLM_MODEL ausente → falha
# =============================================================================
def test_sem_llm_model_falha(monkeypatch):
    monkeypatch.delenv('LLM_MODEL', raising=False)
    for key in ('GROQ_API_KEY', 'NVIDIA_NIM_API_KEY', 'OPENROUTER_API_KEY',
                'TOGETHERAI_API_KEY', 'OPENAI_API_KEY'):
        monkeypatch.delenv(key, raising=False)

    ok, msg = preflight_llm.verificar_llm_pronto()

    assert ok is False
    assert 'Nenhuma IA configurada' in msg
    assert 'LLM_MODEL' in msg
    assert '.env' in msg


# =============================================================================
# 2. LLM_MODEL presente, credencial ausente → falha
# =============================================================================
@pytest.mark.parametrize("modelo,chave_requerida", [
    ('groq/llama-3.3-70b-versatile',       'GROQ_API_KEY'),
    ('nvidia_nim/meta/llama-3.3-70b',      'NVIDIA_NIM_API_KEY'),
    ('openrouter/meta-llama/llama-3.3-70b', 'OPENROUTER_API_KEY'),
    ('together_ai/meta-llama/Llama-3.3',    'TOGETHERAI_API_KEY'),
    ('openai/gpt-4o',                        'OPENAI_API_KEY'),
])
def test_modelo_presente_credencial_ausente_falha(monkeypatch, modelo, chave_requerida):
    monkeypatch.setenv('LLM_MODEL', modelo)
    for key in ('GROQ_API_KEY', 'NVIDIA_NIM_API_KEY', 'OPENROUTER_API_KEY',
                'TOGETHERAI_API_KEY', 'OPENAI_API_KEY'):
        monkeypatch.delenv(key, raising=False)

    ok, msg = preflight_llm.verificar_llm_pronto()

    assert ok is False
    assert chave_requerida in msg
    assert modelo in msg


# =============================================================================
# 3. LLM_MODEL + credencial → sucesso
# =============================================================================
@pytest.mark.parametrize("modelo,chave_env,chave_valor", [
    ('groq/llama-3.3-70b-versatile',       'GROQ_API_KEY',       'gsk_test123'),
    ('nvidia_nim/meta/llama-3.3-70b',      'NVIDIA_NIM_API_KEY', 'nvapi-test'),
    ('openrouter/meta-llama/llama-3.3-70b', 'OPENROUTER_API_KEY', 'or-test'),
    ('together_ai/meta-llama/Llama-3.3',    'TOGETHERAI_API_KEY', 'tai-test'),
    ('openai/gpt-4o',                        'OPENAI_API_KEY',     'sk-test'),
])
def test_modelo_com_credencial_sucesso(monkeypatch, modelo, chave_env, chave_valor):
    monkeypatch.setenv('LLM_MODEL', modelo)
    monkeypatch.setenv(chave_env, chave_valor)
    for key in ('GROQ_API_KEY', 'NVIDIA_NIM_API_KEY', 'OPENROUTER_API_KEY',
                'TOGETHERAI_API_KEY', 'OPENAI_API_KEY'):
        if key != chave_env:
            monkeypatch.delenv(key, raising=False)

    ok, msg = preflight_llm.verificar_llm_pronto()

    assert ok is True
    assert modelo in msg


# =============================================================================
# 4. Prefixo desconhecido (ex: modelo local) → sucesso sem checar chave
# =============================================================================
def test_modelo_prefixo_desconhecido_sucesso(monkeypatch):
    monkeypatch.setenv('LLM_MODEL', 'ollama/llama3.2')
    for key in ('GROQ_API_KEY', 'NVIDIA_NIM_API_KEY', 'OPENROUTER_API_KEY',
                'TOGETHERAI_API_KEY', 'OPENAI_API_KEY'):
        monkeypatch.delenv(key, raising=False)

    ok, msg = preflight_llm.verificar_llm_pronto()

    assert ok is True
    assert 'ollama/llama3.2' in msg


# =============================================================================
# 5. Pipeline main() recusa rodar sem LLM (exit code 1)
# =============================================================================
def test_pipeline_main_exit_code_1_sem_llm(monkeypatch):
    monkeypatch.delenv('LLM_MODEL', raising=False)
    for key in ('GROQ_API_KEY', 'NVIDIA_NIM_API_KEY', 'OPENROUTER_API_KEY',
                'TOGETHERAI_API_KEY', 'OPENAI_API_KEY'):
        monkeypatch.delenv(key, raising=False)

    # Carrega pipeline_completo via importlib (mantém isolamento)
    pipeline_path = Path(__file__).resolve().parent.parent / 'scripts' / 'pipeline_completo.py'
    spec = importlib.util.spec_from_file_location('pipeline_completo', pipeline_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    monkeypatch.setattr(sys, 'argv', [
        'pipeline_completo.py', 'ideia teste', '--pasta', '/tmp/nao-importa'
    ])

    with pytest.raises(SystemExit) as exc_info:
        mod.main()

    assert exc_info.value.code == 1
