# -*- coding: utf-8 -*-
"""Use Cases da CLI do AIDD Enterprise — um módulo por comando."""

from application_enterprise.commands.add_module import cmd_add_module, cmd_refine_module
from application_enterprise.commands.audit import cmd_audit
from application_enterprise.commands.bench import cmd_bench
from application_enterprise.commands.compose import cmd_compose, cmd_compose_orca
from application_enterprise.commands.deploy import cmd_deploy
from application_enterprise.commands.export_frontend import cmd_export_frontend
from application_enterprise.commands.heal import cmd_heal
from application_enterprise.commands.init import cmd_init
from application_enterprise.commands.plan import cmd_apply, cmd_plan, parse_natural_language_intent
from application_enterprise.commands.scaffold_infra import cmd_scaffold_infra
from application_enterprise.commands.setup import cmd_setup, ensure_environment
from application_enterprise.commands.status import cmd_status
from application_enterprise.commands.test_cmd import cmd_test
from application_enterprise.commands.verificar_drift import cmd_verificar_drift
from application_enterprise.pecas_catalogo import carregar_injetor

# Injetor: peça do almoxarifado (Ticket 18), não a cópia application_enterprise/commands/inject.py.
_injetor = carregar_injetor()
_default_component_content = _injetor._default_component_content
_tentar_injecao_por_linguagem_natural = _injetor._tentar_injecao_por_linguagem_natural
cmd_inject = _injetor.cmd_inject
run_inject = _injetor.run_inject

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
    "cmd_verificar_drift",
    "ensure_environment",
    "parse_natural_language_intent",
    "run_inject",
]