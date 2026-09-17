# -*- coding: utf-8 -*-
"""
G_PLANNER_SCHEMA — Valida a conformidade de schema do PLANNER.json gerado pelo aidd-planner.

Verifica:
  1. Presença do arquivo PLANNER.json
  2. Sintaxe JSON válida
  3. Presença dos blocos obrigatórios de primeiro nível
  4. Validação de meta, ddd_bounded_contexts e bdd_cenarios
  5. Ausência de stubs (TODO, FIXME, a definir)
"""
import json
import os
import sys

_PLANNER_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ECOSSISTEMA_ROOT = os.path.dirname(_PLANNER_ROOT)

# Adiciona o diretório da ferramenta ao sys.path para imports limpos
if _PLANNER_ROOT not in sys.path:
    sys.path.insert(0, _PLANNER_ROOT)
if _ECOSSISTEMA_ROOT not in sys.path:
    sys.path.insert(0, _ECOSSISTEMA_ROOT)

from src.core.planner_engine import validar_plano


def resolver_caminho_plano(alvo: str) -> str:
    if os.path.isfile(alvo):
        return alvo
    candidatos = [
        os.path.join(alvo, "PLANNER.json"),
        os.path.join(alvo, "PRE-PLANO.json"),
        os.path.join(alvo, "planner.json"),
    ]
    for c in candidatos:
        if os.path.isfile(c):
            return c
    return os.path.join(alvo, "PLANNER.json")


def verificar_stubs(obj, caminho_campo=""):
    stubs = []
    palavras_proibidas = ["todo", "fixme", "a definir", "implementar depois", "stub"]
    if isinstance(obj, str):
        val_lower = obj.lower().strip()
        for p in palavras_proibidas:
            if p in val_lower:
                stubs.append(f"Stub detectado em '{caminho_campo}': '{obj}'")
    elif isinstance(obj, dict):
        for k, v in obj.items():
            stubs.extend(verificar_stubs(v, f"{caminho_campo}.{k}" if caminho_campo else k))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            stubs.extend(verificar_stubs(item, f"{caminho_campo}[{idx}]"))
    return stubs


def main(alvo_arg: str = ".") -> int:
    caminho = resolver_caminho_plano(alvo_arg)
    if not os.path.isfile(caminho):
        print(f"[G_PLANNER_SCHEMA] ERRO: Arquivo de plano não encontrado em: '{caminho}'", file=sys.stderr)
        return 1

    try:
        with open(caminho, "r", encoding="utf-8") as f:
            plano = json.load(f)
    except Exception as exc:
        print(f"[G_PLANNER_SCHEMA] ERRO: JSON inválido: {exc}", file=sys.stderr)
        return 1

    valido, erros = validar_plano(plano)
    stubs = verificar_stubs(plano)

    todos_erros = erros + stubs
    if todos_erros:
        print(f"[G_PLANNER_SCHEMA] FALHA: {len(todos_erros)} inconsistência(s) encontrada(s):", file=sys.stderr)
        for e in todos_erros:
            print(f"  [X] {e}", file=sys.stderr)
        return 1

    print(f"[G_PLANNER_SCHEMA] PASS: {caminho} cumpre integralmente as regras do schema.")
    return 0


if __name__ == "__main__":
    alvo = sys.argv[1] if len(sys.argv) > 1 else "."
    sys.exit(main(alvo))
