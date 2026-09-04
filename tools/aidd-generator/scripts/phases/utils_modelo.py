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
from pathlib import Path
from typing import Optional

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


# Lista de harnesses conhecidos com padrões de detecção de sessão e modelos
HARNESSES_REGISTRY = {
    'claude': {
        'nome': 'Claude Code',
        'env_sessao': ['CLAUDECODE', 'CLAUDE_SESSION'],
        'env_modelo': ['CLAUDE_MODEL', 'ANTHROPIC_MODEL'],
        'config_paths': ['~/.claude/.config', '~/.claude/config.json'],
        'model_keys': ['model'],
        'modelo_default': None,
    },
    'opencode': {
        'nome': 'OpenCode',
        'env_sessao': ['OPENCODE', 'OPENCODE_SESSION'],
        'env_modelo': ['OPENCODE_MODEL', 'OPENCODE_DEFAULT_MODEL'],
        'config_paths': ['~/.config/opencode/oh-my-opencode-slim.json', '~/.config/opencode/opencode.json', '~/.opencode/config.json'],
        'model_keys': ['orchestrator.model', 'model'],
        'modelo_default': 'opencode/big-pickle',
    },
    'mimocode': {
        'nome': 'MimoCode',
        'env_sessao': ['MIMOCODE', 'MIMO_SESSION'],
        'env_modelo': ['MIMO_MODEL', 'MIMOCODE_MODEL'],
        'config_paths': ['~/.config/mimocode/config.json', '~/.mimocode/config.json'],
        'model_keys': ['model', 'orchestrator.model'],
        'modelo_default': 'mimo-v2.5-pro',
    },
    'freebuff': {
        'nome': 'Freebuff',
        'env_sessao': ['FREEBUFF', 'FREEBUFF_SESSION'],
        'env_modelo': ['FREEBUFF_MODEL', 'FREEBUFF_DEFAULT_MODEL'],
        'config_paths': ['~/.config/freebuff/config.json', '~/.freebuff/config.json'],
        'model_keys': ['model', 'default_model'],
        'modelo_default': None,
    },
    'hermes': {
        'nome': 'Hermes',
        'env_sessao': ['HERMES', 'HERMES_SESSION'],
        'env_modelo': ['HERMES_MODEL', 'HERMES_DEFAULT_MODEL'],
        'config_paths': ['~/.config/hermes/config.json', '~/.hermes/config.json'],
        'model_keys': ['model', 'llm'],
        'modelo_default': None,
    },
    'deepseek': {
        'nome': 'DeepSeek Harness',
        'env_sessao': ['DEEPSEEK_HARNESS', 'DEEPSEEK_SESSION'],
        'env_modelo': ['DEEPSEEK_MODEL', 'DEEPSEEK_DEFAULT_MODEL'],
        'config_paths': ['~/.config/deepseek/config.json', '~/.deepseek/config.json'],
        'model_keys': ['model'],
        'modelo_default': 'deepseek-chat',
    },
    'antigravity': {
        'nome': 'Antigravity',
        'env_sessao': ['ANTIGRAVITY_CLI', 'AGY_SESSION'],
        'env_modelo': ['ANTIGRAVITY_MODEL', 'AGY_MODEL'],
        'config_paths': ['~/.config/antigravity/config.json', '~/.agy/config.json'],
        'model_keys': ['model', 'default_model'],
        'modelo_default': None,
    },
    'gemini': {
        'nome': 'Gemini CLI',
        'env_sessao': ['GEMINI_CLI', 'GEMINI_SESSION'],
        'env_modelo': ['GEMINI_MODEL', 'GEMINI_DEFAULT_MODEL'],
        'config_paths': ['~/.config/gemini/config.json', '~/.gemini/config.json'],
        'model_keys': ['model'],
        'modelo_default': 'gemini-2.5-pro',
    },
    'codex': {
        'nome': 'Codex',
        'env_sessao': ['CODEX_SESSION', 'CODEX_PORT'],
        'env_modelo': ['CODEX_MODEL', 'OPENAI_MODEL'],
        'config_paths': ['~/.codex/config.json'],
        'model_keys': ['model'],
        'modelo_default': None,
    },
    'cursor': {
        'nome': 'Cursor',
        'env_sessao': ['CURSOR_SESSION', 'CURSOR_TRACE'],
        'env_modelo': ['CURSOR_MODEL'],
        'config_paths': ['~/.cursor/config.json'],
        'model_keys': ['model'],
        'modelo_default': None,
    },
}


def _extrair_chave_composta(dicionario: dict, chave_composta: str) -> Optional[str]:
    """Extrai chave de dicionário suportando caminhos aninhados como 'orchestrator.model'."""
    partes = chave_composta.split('.')
    cursor = dicionario
    for parte in partes:
        if isinstance(cursor, dict) and parte in cursor:
            cursor = cursor[parte]
        else:
            return None
    return str(cursor) if cursor is not None else None


def _ler_modelo_de_arquivo(caminho_expandido: str, chaves: list) -> Optional[str]:
    """Tenta carregar um arquivo JSON de configuração e extrair a chave do modelo."""
    path = Path(os.path.expanduser(caminho_expandido))
    if not path.exists():
        return None
    try:
        import json
        with open(path, 'r', encoding='utf-8') as f:
            dados = json.load(f)

        # Se houver presets (ex: oh-my-opencode-slim), busca no preset ativo
        if 'preset' in dados and 'presets' in dados:
            preset_ativo = dados.get('preset')
            preset_dados = dados.get('presets', {}).get(preset_ativo, {})
            if isinstance(preset_dados, dict):
                for k in chaves:
                    val = _extrair_chave_composta(preset_dados, k)
                    if val:
                        return val

        for k in chaves:
            val = _extrair_chave_composta(dados, k)
            if val:
                return val
    except Exception:
        pass
    return None


def detectar_harness_nome() -> str:
    """
    Detecta o nome do harness em execução de forma agnóstica.
    Ordem de prioridade:
    1. Override universal: AIDD_HARNESS_NAME
    2. Variáveis de sessão ativa registradas em HARNESSES_REGISTRY
    3. Inspeção agnóstica por variáveis de sessão dinâmica: <QUALQUER>_SESSION / <QUALQUER>_HARNESS
    4. "desconhecido" (Zero Alucinação)
    """
    override = os.getenv('AIDD_HARNESS_NAME')
    if override:
        return override

    # Checagem direta do registro
    for harness_id, meta in HARNESSES_REGISTRY.items():
        for env_var in meta['env_sessao']:
            val = os.getenv(env_var)
            if val in ('1', 'true', 'True') or (val and env_var.endswith(('_SESSION', '_PORT', '_AGENT'))):
                return meta['nome']

    # Detecção agnóstica universal: qualquer variável <NOME>_SESSION ou <NOME>_HARNESS
    for env_k, env_v in os.environ.items():
        if env_k.endswith('_SESSION') and env_v and not env_k.startswith('ORCA_'):
            prefixo = env_k.replace('_SESSION', '').lower()
            return HARNESSES_REGISTRY.get(prefixo, {}).get('nome', prefixo.capitalize())
        if env_k.endswith('_HARNESS') and env_v in ('1', 'true', 'True'):
            prefixo = env_k.replace('_HARNESS', '').lower()
            return HARNESSES_REGISTRY.get(prefixo, {}).get('nome', prefixo.capitalize())

    return 'desconhecido'


def detectar_modelo_harness() -> str:
    """
    Detecta qual modelo está rodando no harness de forma 100% agnóstica.

    Estratégia universal:
    1. Override universal: AIDD_LLM_MODEL / LLM_MODEL
    2. Variável de modelo explícita do harness ativo (<HARNESS>_MODEL)
    3. Leitura dinâmica de arquivos de configuração do harness ativo
    4. Modelo default do harness ativo registrado
    5. "desconhecido" — honesto, sem fabricação
    """
    # 1. Override universal
    override = os.getenv('AIDD_LLM_MODEL') or os.getenv('LLM_MODEL')
    if override:
        return override

    harness_ativo = detectar_harness_nome().lower()

    # 2. Se há harness ativo identificado no registro:
    for harness_id, meta in HARNESSES_REGISTRY.items():
        eh_este_harness = (harness_id in harness_ativo or meta['nome'].lower() in harness_ativo)

        # Checa variáveis de modelo do harness
        for env_m in meta['env_modelo']:
            val = os.getenv(env_m)
            if val:
                return val

        # Se for o harness ativo, inspeciona os arquivos de config
        if eh_este_harness:
            for cfg_path in meta['config_paths']:
                modelo_cfg = _ler_modelo_de_arquivo(cfg_path, meta['model_keys'])
                if modelo_cfg:
                    return modelo_cfg

            # Se o harness tem um modelo default conhecido
            if meta['modelo_default']:
                return meta['modelo_default']

    # 3. Busca agnóstica dinâmica: qualquer variável terminada em _MODEL
    if harness_ativo != 'desconhecido':
        prefixo = harness_ativo.split()[0].upper()
        dinamico_val = os.getenv(f"{prefixo}_MODEL") or os.getenv(f"{prefixo}_LLM")
        if dinamico_val:
            return dinamico_val

        # Tenta inspecionar ~/.config/<harness>/config.json de forma totalmente genérica
        generico = _ler_modelo_de_arquivo(f"~/.config/{harness_ativo.split()[0].lower()}/config.json", ['model', 'orchestrator.model', 'llm'])
        if generico:
            return generico

    return "desconhecido"


def obter_nome_amigavel_modelo(modelo: str) -> str:
    """
    Converte qualquer ID de modelo para um nome amigável de exibição de forma agnóstica.
    Suporta modelos conhecidos e formata genericamente qualquer slug ou identificador.
    """
    if not modelo or modelo == 'desconhecido':
        return 'desconhecido'

    mapeamento_exato = {
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
        'mimo-v2.5': 'MiMo v2.5',
        'gemini-2.5-pro': 'Gemini 2.5 Pro',
        'gemini-2.5-flash': 'Gemini 2.5 Flash',
        'gpt-4o': 'GPT-4o',
        'gpt-4o-mini': 'GPT-4o Mini',
        'deepseek-chat': 'DeepSeek Chat',
        'deepseek-coder': 'DeepSeek Coder',
        'deepseek-v3': 'DeepSeek V3',
        'deepseek-r1': 'DeepSeek R1',
    }

    if modelo in mapeamento_exato:
        return mapeamento_exato[modelo]

    # Substring em mapeamento exato
    for k, v in mapeamento_exato.items():
        if k.lower() in modelo.lower() or modelo.lower() in k.lower():
            return v

    # Fallback agnóstico e universal: extrai nome limpo e converte para Title Case
    # Remove prefixo de namespace (ex: "openrouter/", "freebuff/", "meta-llama/")
    nome_limpo = modelo.split('/')[-1]

    # Substitui hífens e underscores por espaços
    palavras = nome_limpo.replace('_', ' ').replace('-', ' ').split()

    termos_notaveis = {
        'gpt': 'GPT',
        'llama': 'LLaMA',
        'qwen': 'Qwen',
        'deepseek': 'DeepSeek',
        'claude': 'Claude',
        'gemini': 'Gemini',
        'hermes': 'Hermes',
        'freebuff': 'Freebuff',
        'mimo': 'MiMo',
        'codex': 'Codex',
        'r1': 'R1',
        'v3': 'V3',
        'v4': 'V4',
        'pro': 'Pro',
        'flash': 'Flash',
        'instruct': 'Instruct',
        'chat': 'Chat',
        'coder': 'Coder',
    }

    formatadas = [termos_notaveis.get(p.lower(), p.capitalize()) for p in palavras]
    return ' '.join(formatadas) if formatadas else modelo


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
