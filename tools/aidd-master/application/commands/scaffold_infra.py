# -*- coding: utf-8 -*-
"""Use Case: scaffold-infra — geração de infraestrutura declarativa Terraform + Helm."""

import json
import os


def cmd_scaffold_infra(args):
    target_dir = os.path.abspath(getattr(args, "dir", "."))
    plano_path = os.path.join(target_dir, "PLANO-EXECUCAO-ESTRUTURADO.json")
    suite_name = "AIDD Suite"
    if os.path.exists(plano_path):
        with open(plano_path, "r", encoding="utf-8") as f:
            suite_name = json.load(f).get("projeto", {}).get("nome", suite_name)

    try:
        from scaffold_infra import scaffold_infra
    except ImportError:
        from scripts.scaffold_infra import scaffold_infra
    scaffold_infra(target_dir, suite_name)