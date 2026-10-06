# -*- coding: utf-8 -*-
"""Use Case: deploy — delegado ao aidd-master (Ticket 18 / D1): deploy não é blindagem."""

from application.commands.delegacao import delegar_ou_sair


def cmd_deploy(args):
    delegar_ou_sair(["deploy", getattr(args, "alvo", None) or "docker"])
