# -*- coding: utf-8 -*-
"""Use Case: export-frontend — delegado ao aidd-master (Ticket 18 / D1): o OpenAPI é do Quarteto."""

from application_enterprise.commands.delegacao import delegar_ou_sair


def cmd_export_frontend(args):
    delegar_ou_sair([
        "export-frontend",
        "--stack", getattr(args, "stack", None) or "nextjs",
        "--dir", getattr(args, "dir", ".") or ".",
    ])
