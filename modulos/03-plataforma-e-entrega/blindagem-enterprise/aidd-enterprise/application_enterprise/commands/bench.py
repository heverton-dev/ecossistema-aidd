# -*- coding: utf-8 -*-
"""Use Case: bench — delegado ao aidd-master (Ticket 18 / D1).

O benchmark usa o Database/EventBus do núcleo do projeto, que o master obtém
do almoxarifado; o enterprise não lê mais os moldes de núcleo do master.
"""

from application_enterprise.commands.delegacao import delegar_ou_sair


def cmd_bench(args):
    n = getattr(args, "n", None) or 100
    delegar_ou_sair(["bench", "-n", str(n), "--dir", getattr(args, "dir", ".") or "."])
