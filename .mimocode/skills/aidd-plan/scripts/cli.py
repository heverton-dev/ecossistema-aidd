# -*- coding: utf-8 -*-
"""
CLI determinística local para aidd-plan (D4).
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

ROOT_DIR = Path(__file__).resolve().parents[5]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.gerenciador_planos import (
    cmd_init,
    cmd_check_fences,
    cmd_aprovar,
    cmd_iniciar_execucao,
    cmd_ler_nota,
    cmd_atualizar_nota,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CLI local do aidd-plan")
    subparsers = parser.add_subparsers(dest="subcomando")

    # init
    p_init = subparsers.add_parser("init")
    p_init.add_argument("iniciativa", help="Nome da iniciativa")
    p_init.add_argument("--itens", nargs="+", required=True, help="Lista de itens")
    p_init.add_argument("--destino", default=None, help="Pasta destino base")

    # check-fences
    p_cf = subparsers.add_parser("check-fences")
    p_cf.add_argument("caminho", help="Arquivo ou pasta de plano")

    # aprovar
    p_ap = subparsers.add_parser("aprovar")
    p_ap.add_argument("pasta", help="Pasta do plano")

    # iniciar-execucao
    p_ie = subparsers.add_parser("iniciar-execucao")
    p_ie.add_argument("pasta", help="Pasta do plano")

    # ler-nota
    p_ln = subparsers.add_parser("ler-nota")
    p_ln.add_argument("caminho", help="Arquivo ou pasta do plano")
    p_ln.add_argument("--item", default=None, help="Item do plano")

    # atualizar-nota
    p_an = subparsers.add_parser("atualizar-nota")
    p_an.add_argument("caminho", help="Arquivo ou pasta do plano")
    p_an.add_argument("--item", default=None, help="Item do plano")
    p_an.add_argument("--nota-atual", required=True, help="Nota atual")
    p_an.add_argument("--evidencia", default=None, help="Evidencia")

    return parser


def main(args: Optional[List[str]] = None) -> int:
    parser = build_parser()
    if args is None:
        args = sys.argv[1:]

    if not args:
        return 1

    try:
        parsed = parser.parse_args(args)
    except SystemExit:
        return 1

    if not parsed.subcomando:
        return 1

    if parsed.subcomando == "init":
        dest = Path(parsed.destino) if parsed.destino else None
        return cmd_init(parsed.iniciativa, parsed.itens, destino_base=dest)
    elif parsed.subcomando == "check-fences":
        return cmd_check_fences(parsed.caminho)
    elif parsed.subcomando == "aprovar":
        return cmd_aprovar(parsed.pasta)
    elif parsed.subcomando == "iniciar-execucao":
        return cmd_iniciar_execucao(parsed.pasta)
    elif parsed.subcomando == "ler-nota":
        return cmd_ler_nota(parsed.caminho, parsed.item)
    elif parsed.subcomando == "atualizar-nota":
        return cmd_atualizar_nota(parsed.caminho, parsed.item, parsed.nota_atual, parsed.evidencia)

    return 1


if __name__ == "__main__":
    sys.exit(main())
