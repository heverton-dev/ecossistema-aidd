# -*- coding: utf-8 -*-
"""Use Case: plan / apply / prompt — planejar e compor vão para o aidd-master (Ticket 18 / D1).

O enterprise só mantém a parte de blindagem da entrada em linguagem natural:
um pedido de injeção de componente é atendido aqui, pelo injetor da peça do
almoxarifado; o resto (SPEC, plano estruturado e composição) é delegado.
"""

from application_enterprise.commands.delegacao import delegar_ou_sair
from application_enterprise.pecas_catalogo import carregar_injetor


def _tentar_injecao_por_linguagem_natural(prompt: str, base_dir: str = ".") -> bool:
    return carregar_injetor()._tentar_injecao_por_linguagem_natural(prompt, base_dir=base_dir)


def cmd_plan(prompt: str, base_dir: str = ".", auto_apply: bool = False):
    """Fase 1.5 (SPEC + plano estruturado), delegada ao aidd-master."""
    if _tentar_injecao_por_linguagem_natural(prompt, base_dir=base_dir):
        return
    argv = ["plan", prompt, "--dir", base_dir or "."]
    if auto_apply:
        argv.append("--apply")
    delegar_ou_sair(argv)


def cmd_apply(args):
    """Fase 2 (executa o plano aprovado), delegada ao aidd-master."""
    delegar_ou_sair(["apply", "--dir", getattr(args, "dir", ".") or "."])


def parse_natural_language_intent(prompt: str, base_dir: str = "."):
    """Linguagem natural: injeção fica no enterprise; o resto vira `plan` no master."""
    if _tentar_injecao_por_linguagem_natural(prompt, base_dir=base_dir):
        return
    cmd_plan(prompt, base_dir=base_dir, auto_apply=False)
