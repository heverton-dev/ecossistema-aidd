#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pré-voo LLM — Verificação rápida antes de rodar o pipeline.

Verifica se existe um LLM configurado e funcional (LLM_MODEL + credencial
do provedor) ANTES de gastar tempo com a Fase 1. Se faltar configuração,
o pipeline para imediatamente com mensagem clara.

Reaproveita a lógica do gate G_VERIFICAR_LLM_PRONTO (que só checa
presença de LLM_MODEL) e adiciona verificação de credencial do provedor.

Uso independente:
    python scripts/preflight_llm.py
    echo $?   # 0 = pronto, 1 = falta configuração

Uso no pipeline:
    from preflight_llm import verificar_llm_pronto
    ok, msg = verificar_llm_pronto()
"""

import sys
import os

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Mapeamento prefixo do LLM_MODEL → variável de ambiente da credencial
# Fonte: .env.example (provedores documentados)
_PROVEDOR_KEY_MAP = {
    'groq/':           'GROQ_API_KEY',
    'nvidia_nim/':     'NVIDIA_NIM_API_KEY',
    'openrouter/':     'OPENROUTER_API_KEY',
    'together_ai/':    'TOGETHERAI_API_KEY',
    'openai/':         'OPENAI_API_KEY',
}


def verificar_llm_pronto(fleet=None) -> tuple:
    """Verifica se ha um LLM configurado ou se ha um harness ativo para o Protocolo Delegado.

    1. Protocolo Delegado (Universal): Se houver harness ativo (Claude, MimoCode, OpenCode,
       Antigravity, ORCA), o pre-voo passa automaticamente sem exigir chaves externas de API.
    2. Modo Headless (Fallback CI/CD): Se nao houver nenhum harness ativo, exige LLM_MODEL
       e credencial no .env.

    Retorna (ok, mensagem):
      ok=True  -> pode prosseguir
      ok=False -> pare, mensagem explica o que configurar
    """
    # 1. Checa se o modo delegado esta disponivel via harness ativo
    try:
        from phases.utils_fleet_discovery import resolver_fleet, detectar_via_ambiente
    except ImportError:
        try:
            from utils_fleet_discovery import resolver_fleet, detectar_via_ambiente
        except ImportError:
            resolver_fleet = None
            detectar_via_ambiente = None

    if detectar_via_ambiente:
        env_detectados = detectar_via_ambiente()
        if env_detectados:
            harnesses = ", ".join(env_detectados)
            return (True, f"Harness ativo detectado ({harnesses}). Protocolo Delegado ativo (zero API keys requeridas).")

    if fleet is None and resolver_fleet:
        fleet = resolver_fleet()

    if fleet and getattr(fleet, 'agentes_detectados', None):
        # Se ha agentes instalados no host capazes de orquestrar
        nomes = [a.nome for a in fleet.agentes_detectados]
        if nomes:
            return (True, f"Harness/Agente disponivel no host ({', '.join(nomes)}). Modo Delegado ativo.")

    llm_model = os.environ.get('LLM_MODEL')

    if not llm_model:
        return (False,
            "Nenhuma IA configurada e nenhum harness ativo detectado. "
            "Se estiver rodando em modo Headless (sem agente interativo), "
            "configure LLM_MODEL e a chave do provedor no arquivo .env."
        )

    # Detecta o provedor pelo prefixo do modelo e verifica a credencial
    chave_requerida = None
    for prefixo, env_key in _PROVEDOR_KEY_MAP.items():
        if llm_model.startswith(prefixo):
            chave_requerida = env_key
            break

    if chave_requerida and not os.environ.get(chave_requerida):
        return (False,
            f"LLM_MODEL={llm_model} requer {chave_requerida}, "
            f"mas a variavel nao esta configurada. "
            f"Adicione {chave_requerida}=<sua-chave> no arquivo .env."
        )

    return (True, f"LLM configurado: {llm_model}")


def main():
    """Entrypoint standalone: verifica LLM e imprime resultado."""
    print("\n" + "=" * 70)
    print("PRÉ-VOO LLM — Verificação de configuração")
    print("=" * 70 + "\n")

    ok, msg = verificar_llm_pronto()

    if ok:
        print(f"✅ {msg}")
        print("\n" + "=" * 70)
        print("✅ PRÉ-VOO PASSOU — pode prosseguir para o pipeline")
        print("=" * 70 + "\n")
        return 0
    else:
        print(f"❌ {msg}")
        print("\n" + "=" * 70)
        print("❌ PRÉ-VOO FALHOU — configure o LLM antes de continuar")
        print("=" * 70 + "\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
