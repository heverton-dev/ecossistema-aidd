# -*- coding: utf-8 -*-
"""Use Case: heal — auto-remediação determinística de gates e artefatos corrompidos."""

import json
import os

from application.commands.setup import ensure_environment


def cmd_heal(args):
    """Executa auto-remediação determinística de gates e arquivos corrompidos."""
    ensure_environment()
    target_dir = os.path.abspath(getattr(args, "dir", "."))
    print("=" * 80)
    print(f"🩺 [AIDD SELF-HEALING v5.1] Auto-Remediação de Artefatos")
    print(f"📁 Diretório Alvo: {target_dir}")
    print("=" * 80)

    try:
        from compose_suite import compose_suite
        plano_path = os.path.join(target_dir, "PLANO-EXECUCAO-ESTRUTURADO.json")
        if os.path.exists(plano_path):
            with open(plano_path, "r", encoding="utf-8") as f:
                plano = json.load(f)
            suite_name = plano.get("projeto", {}).get("nome", "App Suite")
            modulos = plano.get("projeto", {}).get("modulos", ["crm", "erp"])
            compose_suite(target_dir, suite_name, modulos)
            print("[OK] Kernel e Fatias Verticais ressincronizados com êxito.")
        else:
            print("[WARN] Manifesto não localizado para auto-cura.")
    except Exception as e:
        print(f"[ERRO] Falha durante auto-remediação: {e}")