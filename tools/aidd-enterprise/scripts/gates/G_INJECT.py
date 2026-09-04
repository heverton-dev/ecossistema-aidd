#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.1 Enterprise — GATE DETERMINÍSTICO DO UNIVERSAL COMPONENT INJECTOR (G_INJECT)
=============================================================================
Valida o contrato JSON Schema (Draft 2020-12) do injector, a integridade
estrutural do COMPONENT-REGISTRY.json e a sincronização byte-a-byte dos
componentes materializados entre todos os harnesses de IA.
"""

import os
import sys
import json
import argparse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def verificar_injector(target_dir: str = "."):
    print("[GATE G_INJECT] Validando contrato, registry e sincronização multi-harness do Universal Component Injector...")
    target_dir = os.path.abspath(target_dir)
    scripts_dir = os.path.join(target_dir, "scripts")
    src_dir = os.path.join(target_dir, "src")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

    erros = []

    # 1. Validar existência e formato do contrato (JSON Schema Draft 2020-12)
    schema_path = os.path.join(scripts_dir, "injector", "schema", "component_manifest.schema.json")
    if not os.path.exists(schema_path):
        erros.append(f"Contrato ausente: {schema_path}")
    else:
        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                schema = json.load(f)
            if "2020-12" not in schema.get("$schema", ""):
                erros.append("component_manifest.schema.json não declara Draft 2020-12 em '$schema'.")
            if not isinstance(schema.get("properties", {}).get("type", {}).get("enum"), list):
                erros.append("component_manifest.schema.json não define o enum de 'type' esperado.")
        except Exception as e:
            erros.append(f"component_manifest.schema.json inválido: {e}")

    # 2. Validar COMPONENT-REGISTRY.json (se existir) e sincronização multi-harness
    registry_path = os.path.join(target_dir, "COMPONENT-REGISTRY.json")
    if os.path.exists(registry_path):
        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                registry = json.load(f)
            if not isinstance(registry, list):
                erros.append("COMPONENT-REGISTRY.json deve ser uma lista de componentes.")
            else:
                for entrada in registry:
                    if not isinstance(entrada, dict) or "name" not in entrada or "type" not in entrada:
                        erros.append(f"Entrada de registry malformada: {entrada!r}")
        except Exception as e:
            erros.append(f"COMPONENT-REGISTRY.json inválido: {e}")

        if not erros:
            try:
                from injector import aidd_core_injector as injector_core
                resultado_sync = injector_core.sync_check(target_dir)
                if not resultado_sync.sucesso:
                    for problema in resultado_sync.detalhes.get("problemas", []):
                        erros.append(problema)
            except Exception as e:
                erros.append(f"Falha ao executar sync_check() do injector: {e}")

    if erros:
        print("\n[FAIL] ❌ Violações do Universal Component Injector detectadas:")
        for e in erros:
            print(f"  - {e}")
        sys.exit(1)

    print("[OK] SUCESSO: Contrato, registry e sincronização multi-harness do injector validados com 100% de êxito!")
    sys.exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=".", help="Diretório alvo do projeto")
    args, _ = parser.parse_known_args()
    verificar_injector(args.dir)
