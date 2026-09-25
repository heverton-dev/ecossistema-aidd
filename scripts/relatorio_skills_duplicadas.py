#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Relatório de skills globais duplicadas (skills-pocock ciclo-01, Ticket 11).

Compara a pasta de skills globais do usuário (padrão: ~/.agents/skills) com as
skills do projeto (padrão: componentes/compartilhado/skills) usando um mapa fixo
de pares upstream (mattpocock/skills) x AIDD. Imprime uma tabela Markdown com a
skill global, o par AIDD e a sugestão:
  - remover: o par AIDD existe no projeto (a cópia global é redundante);
  - manter:  o par AIDD não existe no projeto.

Somente leitura: nunca apaga, move ou escreve arquivo. A remoção é feita à mão
pelo usuário.

Uso:
  python scripts/relatorio_skills_duplicadas.py [--global DIR] [--projeto DIR]
Exit 0: relatório impresso. Exit 1: pasta informada não existe.
"""
import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

# Mapa fixo upstream -> par AIDD (PLANO-EVOLUCAO.md do ciclo, Ticket 11).
PARES_UPSTREAM_AIDD: dict[str, str] = {
    "grilling": "aidd-grill",
    "grill-me": "aidd-grill",
    "grill-with-docs": "aidd-grill-docs",
    "tdd": "aidd-tdd",
    "diagnosing-bugs": "aidd-diagnose",
    "to-spec": "aidd-spec",
    "to-tickets": "aidd-tickets",
    "handoff": "aidd-handoff",
    "code-review": "review-changes",
}


def _skills_na_pasta(base: Path) -> set[str]:
    return {p.name for p in base.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()}


def montar_linhas(global_dir: Path, projeto_dir: Path) -> list[tuple[str, str, str]]:
    globais = _skills_na_pasta(global_dir)
    do_projeto = _skills_na_pasta(projeto_dir)
    linhas = []
    for upstream in sorted(globais & PARES_UPSTREAM_AIDD.keys()):
        par = PARES_UPSTREAM_AIDD[upstream]
        sugestao = "remover" if par in do_projeto else "manter"
        linhas.append(((global_dir / upstream).as_posix(), par, sugestao))
    return linhas


def formatar_tabela(linhas: list[tuple[str, str, str]]) -> str:
    saida = ["| Skill global | Par AIDD | Sugestão |", "|---|---|---|"]
    saida += [f"| `{caminho}` | `{par}` | {sugestao} |" for caminho, par, sugestao in linhas]
    if not linhas:
        saida.append("| (nenhuma duplicata do mapa encontrada) | - | - |")
    return "\n".join(saida)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lista skills globais que duplicam skills AIDD (somente leitura).")
    parser.add_argument("--global", dest="global_dir", default=str(Path.home() / ".agents" / "skills"),
                        help="Pasta de skills globais (padrão: ~/.agents/skills)")
    parser.add_argument("--projeto", dest="projeto_dir",
                        default=str(ROOT_DIR / "componentes" / "compartilhado" / "skills"),
                        help="Pasta de skills do projeto (padrão: componentes/compartilhado/skills)")
    args = parser.parse_args(argv)
    # Saída em UTF-8 mesmo com stdout redirecionado no Windows (cp1252 quebraria os acentos).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    global_dir = Path(args.global_dir)
    projeto_dir = Path(args.projeto_dir)
    for rotulo, pasta in (("global", global_dir), ("projeto", projeto_dir)):
        if not pasta.is_dir():
            print(f"[ERRO] Pasta {rotulo} não existe: {pasta}", file=sys.stderr)
            return 1

    print(formatar_tabela(montar_linhas(global_dir, projeto_dir)))
    print("\nRemoção só à mão pelo usuário; este script nunca apaga nada.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
