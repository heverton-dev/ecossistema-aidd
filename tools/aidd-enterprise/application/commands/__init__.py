# -*- coding: utf-8 -*-
"""Use Cases da CLI do AIDD Enterprise — um módulo por comando."""

from application.commands.add_module import cmd_add_module, cmd_refine_module
from application.commands.audit import cmd_audit
from application.commands.bench import cmd_bench
from application.commands.compose import cmd_compose, cmd_compose_orca
from application.commands.deploy import cmd_deploy
from application.commands.export_frontend import cmd_export_frontend
from application.commands.heal import cmd_heal
from application.commands.init import cmd_init
from application.commands.inject import (
    _default_component_content,
    _tentar_injecao_por_linguagem_natural,
    cmd_inject,
    run_inject,
)
from application.commands.plan import cmd_apply, cmd_plan, parse_natural_language_intent
from application.commands.scaffold_infra import cmd_scaffold_infra
from application.commands.setup import cmd_setup, ensure_environment
from application.commands.status import cmd_status
from application.commands.test_cmd import cmd_test

__all__ = [
    "_default_component_content",
    "_tentar_injecao_por_linguagem_natural",
    "cmd_add_module",
    "cmd_apply",
    "cmd_audit",
    "cmd_bench",
    "cmd_compose",
    "cmd_compose_orca",
    "cmd_deploy",
    "cmd_export_frontend",
    "cmd_heal",
    "cmd_init",
    "cmd_inject",
    "cmd_plan",
    "cmd_refine_module",
    "cmd_scaffold_infra",
    "cmd_setup",
    "cmd_status",
    "cmd_test",
    "ensure_environment",
    "parse_natural_language_intent",
    "run_inject",
]