# -*- coding: utf-8 -*-
"""Use Case: compose / compose-orca — delegados ao aidd-master (Ticket 18 / D1).

Compor a suíte e as fatias via subagentes é trabalho de construção, do
aidd-master; o enterprise só repassa os argumentos (ver delegacao.py).
"""

from application_enterprise.commands.delegacao import delegar_ou_sair


def cmd_compose(args):
    argv = ["compose", args.target_dir, args.suite_name, *(args.modulos or ())]
    argv += ["--db", getattr(args, "db", None) or "sqlite"]
    delegar_ou_sair(argv)


def cmd_compose_orca(args):
    argv = ["compose-orca", "--dir", getattr(args, "dir", ".") or "."]
    argv += ["--suite-name", getattr(args, "suite_name", None) or "AIDD Suite"]
    argv += list(getattr(args, "modulos", None) or ())
    delegar_ou_sair(argv)
