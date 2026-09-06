#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sentinela do Protocolo Delegado — Bateria 5 AIDD Generator

Lista pedidos pendentes (_llm_request_*.json sem _llm_response_*.json
correspondente) na pasta de cache, imprimindo id/fase/prompt de cada um.

Uso: python docs/testes/testes/05_aidd_generator_sentinela.py
     (cwd = raiz do monorepo)
"""

import sys
import json
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

CACHE_DIR = Path(r'C:\Users\trcnologia\Desktop\ecossistema-aidd\tools\aidd-generator\scripts\.aidd\cache')

def listar_pendentes():
    if not CACHE_DIR.exists():
        print(f"[SENTINELA] Cache dir não encontrado: {CACHE_DIR}")
        return []

    pedidos = sorted(CACHE_DIR.glob('_llm_request_*.json'))
    pendentes = []

    for pedido in pedidos:
        req_id = pedido.stem.replace('_llm_request_', '')
        resposta = CACHE_DIR / f'_llm_response_{req_id}.json'
        if not resposta.exists():
            pendentes.append((req_id, pedido))

    return pendentes

def main():
    pendentes = listar_pendentes()

    if not pendentes:
        print("[SENTINELA] Nenhum pedido pendente no momento.")
        return

    print(f"\n[SENTINELA] {len(pendentes)} pedido(s) pendente(s) aguardando resposta:\n")
    print("=" * 80)

    for req_id, pedido_path in pendentes:
        try:
            with open(pedido_path, 'r', encoding='utf-8') as f:
                dados = json.load(f)

            fase = dados.get('fase', 'DESCONHECIDA')
            timestamp = dados.get('timestamp', '')
            prompt = dados.get('prompt', '')
            contexto = dados.get('contexto', '')

            print(f"ID: {req_id}")
            print(f"Fase: {fase}")
            print(f"Timestamp: {timestamp}")
            print(f"Contexto: {contexto}")
            print(f"Prompt (primeiros 500 chars):")
            print(f"  {prompt[:500]}{'...' if len(prompt) > 500 else ''}")
            print("-" * 80)

        except Exception as e:
            print(f"ID: {req_id} — ERRO ao ler: {e}")
            print("-" * 80)

    print(f"\nTotal pendentes: {len(pendentes)}")
    print(f"Cache dir: {CACHE_DIR}\n")

if __name__ == '__main__':
    main()
