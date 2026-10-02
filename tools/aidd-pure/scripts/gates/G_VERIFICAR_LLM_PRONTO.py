#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GATE: G_VERIFICAR_LLM_PRONTO — Pré-voo obrigatório antes de rodar
pipeline_completo.py com fallback headless.

Verifica mecanicamente (não em prosa, que é ignorável) se existe uma
rede de segurança headless configurada — não valida se a chave é
VÁLIDA (isso custaria uma chamada de API real), só que os dois campos
mínimos foram preenchidos.

Uso:
    python scripts/gates/G_VERIFICAR_LLM_PRONTO.py
    echo $?   # 0 = pronto para prosseguir, 1 = PARE e peça a chave ao usuário

Achado real (2026-08-30): Antigravity pulou o Passo 0 (instrução em
prosa) duas vezes seguidas e caiu na mesma falha de credencial ausente.
Este gate existe para tornar essa checagem mecânica, não opcional.
"""

import sys
import os
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

try:
    from dotenv import load_dotenv
    _ENV_PATH = Path(__file__).resolve().parent.parent.parent / '.env'
    if _ENV_PATH.exists():
        load_dotenv(_ENV_PATH)
except ImportError:
    pass


def main():
    print("\n" + "=" * 70)
    print("GATE: G_VERIFICAR_LLM_PRONTO — Pré-voo do Passo 0")
    print("=" * 70 + "\n")

    claudecode = os.environ.get('CLAUDECODE') == '1'
    llm_model = os.environ.get('LLM_MODEL')

    if claudecode:
        print("🔍 CLAUDECODE=1 detectado — protocolo delegado nativo disponível.")

    if llm_model:
        print(f"✓ LLM_MODEL configurado: {llm_model}")
        print("✓ Rede de segurança headless pronta (protocolo delegado ainda é tentado primeiro).")
        print("\n" + "=" * 70)
        print("✅ GATE PASSOU — pode prosseguir para o Passo 2 (pipeline_completo.py)")
        print("=" * 70 + "\n")
        return 0

    print("❌ LLM_MODEL não está configurado nesta sessão.")
    print("")
    print("PARE AQUI. Não prossiga para o Passo 2 sem resolver isso.")
    print("")
    print("Se você (harness/agente lendo isto) não tem como configurar uma")
    print("chave de API sozinho, PERGUNTE EXPLICITAMENTE AO USUÁRIO agora:")
    print('  "Preciso de uma chave de API (ex: NVIDIA NIM ou Groq, ambos com')
    print('   camada gratuita) para garantir que o pipeline não trave na Fase 2/3')
    print('   caso o protocolo delegado não funcione no meu ambiente. Pode me')
    print('   fornecer uma, ou configurá-la você mesmo com export LLM_MODEL=...')
    print('   e a variável de chave correspondente, no seu terminal (não aqui no chat)?"')
    print("")
    print("Só prossiga para o Passo 2 depois que LLM_MODEL estiver configurado")
    print("(ou se o usuário confirmar explicitamente que quer prosseguir sem")
    print("rede de segurança, aceitando o risco de falha na Fase 2/3).")
    print("\n" + "=" * 70)
    print("❌ GATE FALHOU — pare e peça a chave antes de continuar")
    print("=" * 70 + "\n")
    return 1


if __name__ == '__main__':
    sys.exit(main())
