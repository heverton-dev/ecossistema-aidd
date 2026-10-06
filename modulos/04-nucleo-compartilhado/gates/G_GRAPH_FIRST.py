#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G_GRAPH_FIRST.py — Quality Gate Determinístico (Lei #14 — Graph-First).

Lê o histórico do agente que trabalhou numa worktree e reprova se ele pesquisou
o código sem nenhuma chamada ao codebase-memory-mcp. Bloco 2 de
fronteiras-ferramentas (2026-10-02): o claude da Fase 8 fez 101 comandos de
shell e 0 chamadas ao graph.

Cobertura: só o claude grava histórico legível (~/.claude/projects/<pasta>/*.jsonl).
Sem histórico (agy, opencode, mimo), o gate só avisa e não reprova.

Uso:
    python gates/G_GRAPH_FIRST.py --worktree <pasta da worktree da fase>

Exit 0: graph consultado, ou harness sem histórico legível (aviso).
Exit 1: histórico legível com zero chamadas ao codebase-memory-mcp.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PREFIXO_GRAPH = "mcp__codebase-memory-mcp__"
VAR_PROJETOS = "AIDD_CLAUDE_PROJETOS"


def pasta_historico(worktree: Path) -> Path:
    """Pasta onde o claude grava as sessões abertas em `worktree` (todo caractere não alfanumérico vira '-')."""
    raiz = Path(os.environ.get(VAR_PROJETOS) or Path.home() / ".claude" / "projects")
    return raiz / re.sub(r"[^A-Za-z0-9]", "-", str(worktree.resolve()))


def ferramentas_chamadas(historico: Path) -> list:
    nomes = []
    for linha in historico.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            registro = json.loads(linha)
        except json.JSONDecodeError:
            continue
        conteudo = (registro.get("message") or {}).get("content") if isinstance(registro, dict) else None
        if isinstance(conteudo, list):
            nomes += [c.get("name", "") for c in conteudo if isinstance(c, dict) and c.get("type") == "tool_use"]
    return nomes


def main() -> int:
    parser = argparse.ArgumentParser(description="Lei #14: agente pesquisa o código pelo graph primeiro.")
    parser.add_argument("--worktree", required=True, help="Pasta da worktree onde o agente trabalhou")
    parser.add_argument("--desde", type=float, default=0.0,
                        help="Epoch: só sessões gravadas depois disso (rodada anterior na mesma pasta não conta)")
    args = parser.parse_args()

    pasta = pasta_historico(Path(args.worktree))
    historicos = sorted(h for h in pasta.glob("*.jsonl") if h.stat().st_mtime >= args.desde) if pasta.is_dir() else []
    if not historicos:
        print(f"[AVISO] G_GRAPH_FIRST: sem histórico legível em {pasta} (harness sem .jsonl); nada a conferir.")
        return 0

    nomes = [n for h in historicos for n in ferramentas_chamadas(h)]
    graph = sum(1 for n in nomes if n.startswith(PREFIXO_GRAPH))
    if graph == 0:
        print(f"[FALHA] G_GRAPH_FIRST: {len(nomes)} ferramenta(s) usada(s) e 0 chamada(s) ao codebase-memory-mcp "
              f"em {len(historicos)} sessão(ões). Lei #14: pesquisar pelo graph antes de grep/glob/leitura.")
        return 1
    print(f"[OK] G_GRAPH_FIRST: {graph} chamada(s) ao codebase-memory-mcp em {len(nomes)} ferramenta(s) usada(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
