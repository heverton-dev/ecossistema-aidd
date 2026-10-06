# -*- coding: utf-8 -*-
"""Use Case: init — delegado ao aidd-master (Ticket 18 / D1): provisionar projeto é construção."""

from application.commands.delegacao import delegar_ou_sair


def cmd_init(args):
    delegar_ou_sair(["init", args.nome, "--dir", getattr(args, "dir", ".") or "."])
