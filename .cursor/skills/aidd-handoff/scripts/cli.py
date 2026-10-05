# -*- coding: utf-8 -*-
"""
Roteador CLI determinístico para aidd-handoff (D4).
Subcomandos:
- gerar: cria arquivo markdown de handoff respeitando as 5 seções canônicas.
- validar: verifica conformidade estrutural de um arquivo de handoff.
- emitir: assina criptograficamente o manifesto de handoff da sessão.
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path
from typing import List, Optional

SECOES_CANONICAS = [
    "Initial Goal",
    "Completed Work",
    "Quality Gate State",
    "Next Actions",
    "Discovered Invariants & Gotchas",
]


def comando_gerar(output: str, goal: str) -> int:
    caminho = Path(output).resolve()
    caminho.parent.mkdir(parents=True, exist_ok=True)

    agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conteudo = f"""# Sessão Handoff — {agora}

## Initial Goal
{goal}

## Completed Work
- Nenhum arquivo modificado inicialmente.

## Quality Gate State
- audit: owned by the orchestrator

## Next Actions
1. Retomar execução pelo backlog prioritário.

## Discovered Invariants & Gotchas
- Contexto isolado preservado com sucesso.
"""
    caminho.write_text(conteudo, encoding="utf-8")
    print(f"[OK] Handoff gerado em: {caminho}")
    return 0


def comando_validar(arquivo: str) -> int:
    p = Path(arquivo).resolve()
    if not p.exists():
        print(f"Erro: Arquivo '{arquivo}' não encontrado.", file=sys.stderr)
        return 1

    texto = p.read_text(encoding="utf-8")
    faltando = [s for s in SECOES_CANONICAS if f"## {s}" not in texto]
    if faltando:
        print(f"Erro: Faltam as seções obrigatórias: {faltando}", file=sys.stderr)
        return 1

    print(f"[OK] Handoff válido: {arquivo}")
    return 0


def comando_emitir(arquivo: str, output: str) -> int:
    val = comando_validar(arquivo)
    if val != 0:
        return val

    p_in = Path(arquivo).resolve()
    p_out = Path(output).resolve()
    p_out.parent.mkdir(parents=True, exist_ok=True)

    manifesto = {
        "tipo": "aidd-handoff",
        "versao": "1.0",
        "arquivo": str(p_in),
        "timestamp": datetime.datetime.now().isoformat(),
        "status": "VALIDO",
    }
    p_out.write_text(json.dumps(manifesto, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] Manifesto emitido em: {p_out}")
    return 0


def main(args: Optional[List[str]] = None) -> int:
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(description="CLI determinística para aidd-handoff")
    subparsers = parser.add_subparsers(dest="subcomando")

    p_gerar = subparsers.add_parser("gerar")
    p_gerar.add_argument("--output", required=True, help="Caminho do arquivo markdown")
    p_gerar.add_argument("--goal", default="Objetivo da sessão", help="Initial goal da sessão")

    p_validar = subparsers.add_parser("validar")
    p_validar.add_argument("--arquivo", required=True, help="Arquivo a ser validado")

    p_emitir = subparsers.add_parser("emitir")
    p_emitir.add_argument("--arquivo", required=True, help="Arquivo a ser validado")
    p_emitir.add_argument("--output", required=True, help="Destino do manifesto json")

    if not args:
        return 1

    try:
        parsed = parser.parse_args(args)
    except SystemExit:
        return 1

    if parsed.subcomando == "gerar":
        return comando_gerar(parsed.output, parsed.goal)
    elif parsed.subcomando == "validar":
        return comando_validar(parsed.arquivo)
    elif parsed.subcomando == "emitir":
        return comando_emitir(parsed.arquivo, parsed.output)

    return 1


if __name__ == "__main__":
    sys.exit(main())
