# -*- coding: utf-8 -*-
"""Use Case: init — provisão de novo projeto modular."""

from application.commands.setup import ensure_environment


def cmd_init(args):
    ensure_environment()
    try:
        from provision_project import provision
    except ImportError:
        from scripts.provision_project import provision
    provision(args.nome, base_dir=getattr(args, "dir", "."))