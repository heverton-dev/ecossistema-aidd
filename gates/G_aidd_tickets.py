#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quality Gate Determinístico de Decomposição de Tickets (Ticket 7 / D13 / DoD 6 / Leis #8, #9 e #13).
Garante que todo plano ou arquivo de tickets decompostos cumpra:
1. Padrão canônico vertical com pelo menos um arquivo de teste por ticket (Lei #5).
2. Comando de validação explícito por ticket.
3. Grafo acíclico dirigido (DAG) comprovado sem dependências circulares / deadlocks.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".agents" / "skills" / "aidd-tickets" / "scripts"))

try:
    import parser as tickets_parser
    import grafo_dag
except ImportError:
    tickets_parser = None
    grafo_dag = None


def validar_tickets_conteudo(texto: str) -> tuple[bool, list[str]]:
    erros = []
    if not tickets_parser or not grafo_dag:
        return False, ["Módulos de parsing ou grafo de aidd-tickets indisponíveis."]

    tickets, erros_parse = tickets_parser.parsear_tickets_markdown(texto)
    if erros_parse:
        erros.extend(erros_parse)

    if not tickets:
        erros.append("Nenhum ticket encontrado para validação.")
        return False, erros

    valido, ordem, msg_ciclo = grafo_dag.ordenar_topologicamente_kahn(tickets)
    if not valido:
        erros.append(msg_ciclo)

    return len(erros) == 0, erros


def main():
    parser = argparse.ArgumentParser(description="Quality Gate para aidd-tickets")
    parser.add_argument("--arquivo", default=None, help="Caminho opcional do arquivo markdown com tickets")
    args = parser.parse_args()

    if args.arquivo:
        p = Path(args.arquivo)
        if not p.exists():
            print(f"[FALHA] Arquivo '{args.arquivo}' não existe.")
            sys.exit(1)
        texto = p.read_text(encoding="utf-8")
        valido, erros = validar_tickets_conteudo(texto)
        if not valido:
            print("[FALHA] Quality Gate G_aidd_tickets REPROVOU os tickets:")
            for e in erros:
                print(f" - {e}")
            sys.exit(1)
        print("[SUCESSO] Quality Gate G_aidd_tickets APROVADO. EXIT 0")
        sys.exit(0)

    # Modo default: se não houver arquivo especificado, audita conformidade dos componentes
    scripts_dir = ROOT / ".agents" / "skills" / "aidd-tickets" / "scripts"
    obrigatorios = ["cli.py", "isolamento.py", "parser.py", "grafo_dag.py", "fallback.py", "observabilidade.py"]
    for ob in obrigatorios:
        if not (scripts_dir / ob).exists():
            print(f"[FALHA] Script obrigatório ausente: {ob}")
            sys.exit(1)

    print("[SUCESSO] Quality Gate G_aidd_tickets APROVADO (Módulos íntegros). EXIT 0")
    sys.exit(0)


if __name__ == "__main__":
    main()
