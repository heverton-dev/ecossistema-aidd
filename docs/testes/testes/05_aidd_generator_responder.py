#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Responder do Protocolo Delegado — Bateria 5 AIDD Generator

Escreve _llm_response_{id}.json de forma atômica a partir de um arquivo JSON
com o conteúdo real da resposta.

Uso: python docs/testes/testes/05_aidd_generator_responder.py <id> <arquivo-json>
     (cwd = raiz do monorepo)

Exemplo:
  python docs/testes/testes/05_aidd_generator_responder.py abc12345 /tmp/minha_resposta.json
"""

import sys
import json
import os
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

CACHE_DIR = Path(r'C:\Users\trcnologia\Desktop\ecossistema-aidd\tools\aidd-generator\scripts\.aidd\cache')


def escrever_resposta(req_id: str, conteudo_resposta: dict) -> Path:
    """Escreve _llm_response_{id}.json de forma atômica."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    caminho_final = CACHE_DIR / f'_llm_response_{req_id}.json'
    caminho_tmp = CACHE_DIR / f'_llm_response_{req_id}.tmp'

    # Validação mínima
    if 'conteudo' not in conteudo_resposta:
        raise ValueError("Resposta deve ter campo 'conteudo'")
    if 'tokens_consumidos' not in conteudo_resposta:
        raise ValueError("Resposta deve ter campo 'tokens_consumidos'")

    # Garantir modelo_usado
    if 'modelo_usado' not in conteudo_resposta:
        conteudo_resposta['modelo_usado'] = 'antigravity-claude-sonnet-4-6'

    # Escrita atômica: tmp → rename
    with open(caminho_tmp, 'w', encoding='utf-8') as f:
        json.dump(conteudo_resposta, f, indent=2, ensure_ascii=False)

    os.replace(caminho_tmp, caminho_final)
    return caminho_final


def main():
    if len(sys.argv) < 3:
        print("Uso: python 05_aidd_generator_responder.py <id> <arquivo-json-da-resposta>")
        print("Exemplo: python 05_aidd_generator_responder.py abc12345 /tmp/resp.json")
        sys.exit(1)

    req_id = sys.argv[1]
    arquivo_resposta = Path(sys.argv[2])

    # Verificar que pedido existe
    pedido_path = CACHE_DIR / f'_llm_request_{req_id}.json'
    if not pedido_path.exists():
        print(f"ERRO: Pedido não encontrado: {pedido_path}")
        sys.exit(1)

    # Verificar que resposta ainda não existe
    resposta_path = CACHE_DIR / f'_llm_response_{req_id}.json'
    if resposta_path.exists():
        print(f"AVISO: Resposta já existe: {resposta_path}")
        print("Sobrescrevendo...")

    # Ler arquivo de resposta
    if not arquivo_resposta.exists():
        print(f"ERRO: Arquivo de resposta não encontrado: {arquivo_resposta}")
        sys.exit(1)

    with open(arquivo_resposta, 'r', encoding='utf-8') as f:
        conteudo_resposta = json.load(f)

    # Escrever resposta
    try:
        caminho = escrever_resposta(req_id, conteudo_resposta)
        print(f"✓ Resposta escrita: {caminho}")

        # Mostrar info do pedido original
        with open(pedido_path, 'r', encoding='utf-8') as f:
            pedido = json.load(f)
        print(f"  Fase: {pedido.get('fase', '?')}")
        print(f"  Tokens declarados: {conteudo_resposta.get('tokens_consumidos', '?')}")

    except Exception as e:
        print(f"ERRO ao escrever resposta: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
