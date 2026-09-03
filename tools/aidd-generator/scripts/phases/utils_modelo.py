#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilitário: Detectar modelo do harness automaticamente
aidd-project-generator v2.1

Permite que mocks capturem qual modelo está sendo usado
sem necessidade de configuração manual.
"""

import sys
import os
from typing import Optional

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def detectar_modelo_harness() -> str:
    """
    Detecta qual modelo está rodando no harness do usuário.

    Estratégia (ordem de prioridade):
    1. AIDD_LLM_MODEL / LLM_MODEL — override universal explícito,
       recomendado para QUALQUER harness (Claude Code, Antigravity,
       MimoCode, OpenCode, etc) que queira se auto-identificar com certeza
    2. CLAUDE_MODEL / ANTHROPIC_MODEL — específico de Claude Code
    3. Arquivo ~/.claude/.config — específico de Claude Code
    4. "desconhecido" — NUNCA fabrica um modelo específico como default;
       harness que não se identificou por nenhuma via acima é honesto
       sobre isso (Zero Alucinação)

    Return: Modelo identificado (ex: "claude-opus-5") ou "desconhecido"
    """

    # Estratégia 1: override universal (recomendado para testes multi-harness)
    override = os.getenv('AIDD_LLM_MODEL') or os.getenv('LLM_MODEL')
    if override:
        return override

    # Estratégia 2: Variável de ambiente específica de Claude Code
    env_model = os.getenv('CLAUDE_MODEL')
    if env_model:
        return env_model

    env_model_legacy = os.getenv('ANTHROPIC_MODEL')
    if env_model_legacy:
        return env_model_legacy

    # Estratégia 3: Arquivo .claude/config (se existir)
    config_path = os.path.expanduser('~/.claude/.config')
    if os.path.exists(config_path):
        try:
            import json
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if 'model' in config:
                    return config['model']
        except:
            pass

    # Estratégia 4: honesto — sem dado real, sem fabricar um modelo específico
    return "desconhecido"


def detectar_harness_nome() -> str:
    """
    Detecta o nome do harness em execução. NUNCA assume "Claude Code"
    como default — retorna "desconhecido" se nada for detectado com
    confiança (Zero Alucinação).

    Só existe UM sinal confiável testado neste código: CLAUDECODE=1
    (setado pelo próprio Claude Code, escopo de sessão). Prefixos de
    env var de outros harness (CODEX_HOME, OPENCODE_CONFIG_DIR, etc)
    NÃO são confiáveis como "harness em execução agora" — em ambientes
    como ORCA, que gerenciam múltiplos harness na mesma máquina, essas
    variáveis existem mesmo quando aquele harness não é o que está
    rodando (confirmado empiricamente: CODEX_HOME presente mesmo com
    Claude Code sendo o processo ativo).

    Por isso: para qualquer harness que não seja Claude Code, exporte
    AIDD_HARNESS_NAME explicitamente antes de rodar o pipeline. É a
    única forma confiável de identidade correta em testes comparativos.
    """
    override = os.getenv('AIDD_HARNESS_NAME')
    if override:
        return override

    if os.getenv('CLAUDECODE') == '1':
        return 'Claude Code'

    return 'desconhecido'


def obter_nome_amigavel_modelo(modelo: str) -> str:
    """Converte ID do modelo para nome amigável"""

    mapeamento = {
        'claude-haiku-4-5-20251001': 'Haiku',
        'claude-sonnet-5': 'Sonnet',
        'claude-opus-5': 'Opus',
        'claude-opus-4.1': 'Opus 4.1',
        'claude-fable-5': 'Fable',
        'claude-3.5-sonnet': 'Sonnet 3.5',
    }

    # Procurar match exato
    if modelo in mapeamento:
        return mapeamento[modelo]

    # Procurar substring
    for chave, valor in mapeamento.items():
        if chave in modelo or modelo in chave:
            return valor

    # Fallback: usar parte do ID
    if 'haiku' in modelo.lower():
        return 'Haiku'
    elif 'opus' in modelo.lower():
        return 'Opus'
    elif 'sonnet' in modelo.lower():
        return 'Sonnet'
    elif 'fable' in modelo.lower():
        return 'Fable'

    return modelo


def log_modelo_detectado(fase: str, modelo: str, origem: str = "herança"):
    """
    Log amigável mostrando modelo detectado

    Args:
        fase: Ex: "Phase 2"
        modelo: ID do modelo
        origem: "herança" | "override" | "default"
    """
    nome_amigavel = obter_nome_amigavel_modelo(modelo)
    origem_icon = {
        'herança': '📦',
        'override': '⚙️',
        'default': '📋'
    }.get(origem, '❓')

    print(f"   {origem_icon} {fase} Model: {nome_amigavel}")
    if origem != 'herança':
        print(f"      ({origem})")


if __name__ == '__main__':
    # Teste
    modelo = detectar_modelo_harness()
    nome = obter_nome_amigavel_modelo(modelo)
    print(f"Modelo detectado: {nome}")
    print(f"ID: {modelo}")
