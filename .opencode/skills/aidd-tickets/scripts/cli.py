# -*- coding: utf-8 -*-
"""
CLI determinística para decomposição de tickets em fatias verticais (Ticket 1 / D2 / DoD 1).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import parser as tickets_parser
import grafo_dag



def validar_arquivo(caminho: str) -> int:
    p = Path(caminho)
    if not p.exists():
        print(f"Erro: Arquivo '{caminho}' não encontrado.", file=sys.stderr)
        return 1

    texto = p.read_text(encoding="utf-8")
    tickets, erros = tickets_parser.parsear_tickets_markdown(texto)

    if erros:
        print("[FALHA] Validação de schema rejeitou os tickets:")
        for e in erros:
            print(f" - {e}")
        return 1

    if not tickets:
        print("[FALHA] Nenhum ticket [TICKET-XX] encontrado no arquivo.", file=sys.stderr)
        return 1

    valido, ordem, msg_ciclo = grafo_dag.ordenar_topologicamente_kahn(tickets)
    if not valido:
        print(f"[FALHA] {msg_ciclo}", file=sys.stderr)
        return 1

    print(f"[OK] {len(tickets)} tickets válidos e ordenados em DAG com sucesso.")
    return 0


def exportar_tickets(caminho: str, output: str) -> int:
    p = Path(caminho)
    if not p.exists():
        print(f"Erro: Arquivo '{caminho}' não encontrado.", file=sys.stderr)
        return 1

    texto = p.read_text(encoding="utf-8")
    tickets, erros = tickets_parser.parsear_tickets_markdown(texto)
    if erros or not tickets:
        print(f"[FALHA] Não foi possível exportar: {erros}", file=sys.stderr)
        return 1

    valido, ordem, msg = grafo_dag.ordenar_topologicamente_kahn(tickets)
    if not valido:
        print(f"[FALHA] {msg}", file=sys.stderr)
        return 1

    out_p = Path(output)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    dados = {
        "versao": "1.0",
        "total_tickets": len(tickets),
        "ordem_topologica": ordem,
        "tickets": tickets
    }

    with open(out_p, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

    print(f"[OK] {len(tickets)} tickets exportados com sucesso para: {out_p}")
    return 0


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    arg_parser = argparse.ArgumentParser(description="CLI determinística de validação e ordenação de aidd-tickets")
    sub = arg_parser.add_subparsers(dest="subcomando", required=True)

    p_val = sub.add_parser("validar", help="Valida conformidade de schema e aciclicidade do grafo")
    p_val.add_argument("--arquivo", required=True, help="Arquivo markdown com os tickets")

    p_exp = sub.add_parser("exportar", help="Exporta tickets parseados e ordenados em JSON")
    p_exp.add_argument("--arquivo", required=True, help="Arquivo markdown com os tickets")
    p_exp.add_argument("--output", required=True, help="Destino JSON")

    parsed = arg_parser.parse_args(args)

    if parsed.subcomando == "validar":
        return validar_arquivo(parsed.arquivo)
    elif parsed.subcomando == "exportar":
        return exportar_tickets(parsed.arquivo, parsed.output)

    return 1


if __name__ == "__main__":
    sys.exit(main())
