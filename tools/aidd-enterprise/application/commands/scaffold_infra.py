# -*- coding: utf-8 -*-
"""Use Case: scaffold-infra — delegado ao aidd-master (Ticket 18 / D1): infraestrutura não é blindagem."""

from application.commands.delegacao import delegar_ou_sair


def cmd_scaffold_infra(args):
    delegar_ou_sair(["scaffold-infra", "--dir", getattr(args, "dir", ".") or "."])
