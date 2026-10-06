# -*- coding: utf-8 -*-
"""Use Case: export-frontend — exportação de front-end Next.js/TypeScript tipado."""

import json
import os

from application.commands.setup import ensure_environment


def cmd_export_frontend(args):
    ensure_environment()
    target_dir = os.path.abspath(getattr(args, "dir", "."))
    plano_path = os.path.join(target_dir, "PLANO-EXECUCAO-ESTRUTURADO.json")
    suite_name = "AIDD Suite"
    if os.path.exists(plano_path):
        with open(plano_path, "r", encoding="utf-8") as f:
            suite_name = json.load(f).get("projeto", {}).get("nome", suite_name)

    try:
        from openapi_to_ts import export_frontend
    except ImportError:
        from scripts.openapi_to_ts import export_frontend
    export_frontend(target_dir, suite_name, stack=getattr(args, "stack", "nextjs"))