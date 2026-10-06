# -*- coding: utf-8 -*-
"""Use Case: heal — delegado ao aidd-master (Ticket 18 / D1): recompor kernel e fatias é construção."""

from application.commands.delegacao import delegar_ou_sair


def cmd_heal(args):
    delegar_ou_sair(["heal", "--dir", getattr(args, "dir", ".") or "."])
