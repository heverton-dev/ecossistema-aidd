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
    1. AIDD_LLM_MODEL / LLM_MODEL — override universal explícito
    2. OpenCode (OPENCODE_MODEL, oh-my-opencode-slim.json [orchestrator], opencode.json)
    3. Claude Code (CLAUDE_MODEL, ANTHROPIC_MODEL, ~/.claude/.config)
    4. Antigravity / Gemini / MimoCode (ANTIGRAVITY_MODEL, GEMINI_MODEL, MIMO_MODEL)
    5. Fallback por harness ativo: se OpenCode ativo, infere modelo do orchestrator
    6. "desconhecido" — sem dado real, sem fabricar modelo inválido
    """
    # Estratégia 1: override universal
    override = os.getenv('AIDD_LLM_MODEL') or os.getenv('LLM_MODEL')
    if override:
        return override

    # Estratégia 2: OpenCode (se env específico presente ou harness for OpenCode)
    env_opencode = os.getenv('OPENCODE_MODEL') or os.getenv('OPENCODE_DEFAULT_MODEL')
    if env_opencode:
        return env_opencode

    harness_atual = detectar_harness_nome().lower()

    if 'opencode' in harness_atual:
        opencode_slim_path = os.path.expanduser('~/.config/opencode/oh-my-opencode-slim.json')
        if os.path.exists(opencode_slim_path):
            try:
                import json
                with open(opencode_slim_path, 'r', encoding='utf-8') as f:
                    cfg_slim = json.load(f)
                    preset = cfg_slim.get('preset', 'zen')
                    orchestrator = cfg_slim.get('presets', {}).get(preset, {}).get('orchestrator', {})
                    if 'model' in orchestrator:
                        return orchestrator['model']
            except Exception:
                pass

        opencode_cfg_path = os.path.expanduser('~/.config/opencode/opencode.json')
        if os.path.exists(opencode_cfg_path):
            try:
                import json
                with open(opencode_cfg_path, 'r', encoding='utf-8') as f:
                    cfg_oc = json.load(f)
                    if 'model' in cfg_oc:
                        return cfg_oc['model']
            except Exception:
                pass

        return "opencode/big-pickle"

    # Estratégia 3: Claude Code (se env específico presente ou harness for Claude)
    env_model = os.getenv('CLAUDE_MODEL') or os.getenv('ANTHROPIC_MODEL')
    if env_model:
        return env_model

    if 'claude' in harness_atual:
        claude_cfg = os.path.expanduser('~/.claude/.config')
        if os.path.exists(claude_cfg):
            try:
                import json
                with open(claude_cfg, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if 'model' in config:
                        return config['model']
            except Exception:
                pass

    # Estratégia 4: Antigravity, MimoCode, Gemini
    for env_var in ('ANTIGRAVITY_MODEL', 'AGY_MODEL', 'MIMO_MODEL', 'MIMOCODE_MODEL', 'GEMINI_MODEL'):
        val = os.getenv(env_var)
        if val:
            return val

    # Estratégia 5: Fallback via harness detectado
    harness = detectar_harness_nome().lower()
    if 'opencode' in harness:
        return "opencode/big-pickle"

    return "desconhecido"


def detectar_harness_nome() -> str:
    """
    Detecta o nome do harness em execução.
    Verifica overrides explícitos, variáveis de sessão de harnesses conhecidos
    (Claude Code, OpenCode, Antigravity, MimoCode, Gemini) e ambiente.
    """
    override = os.getenv('AIDD_HARNESS_NAME')
    if override:
        return override

    if os.getenv('CLAUDECODE') == '1':
        return 'Claude Code'

    if os.getenv('OPENCODE') == '1' or os.getenv('OPENCODE_SESSION'):
        return 'OpenCode'

    if os.getenv('ANTIGRAVITY_CLI') == '1' or os.getenv('AGY_SESSION'):
        return 'Antigravity'

    if os.getenv('MIMOCODE') == '1' or os.getenv('MIMO_SESSION'):
        return 'MimoCode'

    if os.getenv('GEMINI_SESSION') or os.getenv('GEMINI_CLI') == '1':
        return 'Gemini CLI'

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
        'opencode/big-pickle': 'Big Pickle',
        'big-pickle': 'Big Pickle',
        'Big Pickle': 'Big Pickle',
        '9router/free-program': '9Router Free Program',
        'mimo-v2.5-pro': 'MiMo v2.5 Pro',
        'gemini-2.5-pro': 'Gemini 2.5 Pro',
        'gemini-2.5-flash': 'Gemini 2.5 Flash',
    }

    # Procurar match exato
    if modelo in mapeamento:
        return mapeamento[modelo]

    # Procurar substring
    for chave, valor in mapeamento.items():
        if chave.lower() in modelo.lower() or modelo.lower() in chave.lower():
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
    elif 'pickle' in modelo.lower():
        return 'Big Pickle'

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
