# -*- coding: utf-8 -*-
"""
Quality Gate: Validação de Integridade do Histórico de Sessões (secoes/historico_sessoes.json e secoes/INDICE-SESSOES.md).
Retorna exit 0 em sucesso e exit 1 em inconsistências estruturais.
"""

import json
import os
import sys
from pathlib import Path

DEFAULT_JSON = Path("secoes/historico_sessoes.json")
DEFAULT_MD = Path("secoes/INDICE-SESSOES.md")


def validar_historico(caminho_json: Path = DEFAULT_JSON, caminho_md: Path = DEFAULT_MD) -> int:
    if not caminho_json.exists():
        print(f"EXIT 1: Arquivo JSON '{caminho_json}' ausente.")
        return 1

    try:
        dados = json.loads(caminho_json.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"EXIT 1: JSON de sessões corrompido: {exc}")
        return 1

    if not isinstance(dados, dict) or "sessoes" not in dados:
        print("EXIT 1: Campo obrigatório 'sessoes' ausente no JSON.")
        return 1

    sessoes = dados.get("sessoes", [])
    if not isinstance(sessoes, list):
        print("EXIT 1: 'sessoes' deve ser uma lista.")
        return 1

    for s in sessoes:
        if not s.get("id"):
            print("EXIT 1: Sessão sem 'id' identificada.")
            return 1
        if not s.get("harness"):
            print(f"EXIT 1: Sessão '{s.get('id')}' sem campo 'harness'.")
            return 1

    if caminho_md.exists():
        conteudo_md = caminho_md.read_text(encoding="utf-8")
        if "# 📑 Índice Canônico de Sessões Agênticas" not in conteudo_md:
            print("EXIT 1: Espelho Markdown com cabeçalho canônico ausente.")
            return 1

    print("EXIT 0: Histórico de sessões íntegro e em conformidade.")
    return 0


if __name__ == "__main__":
    sys.exit(validar_historico())
