# -*- coding: utf-8 -*-
"""Use Case: compose / compose-orca — composição de suíte empresarial."""

import json
import os
import sys
import time

from application.commands.setup import ensure_environment


def cmd_compose(args):
    ensure_environment()
    try:
        from compose_suite import compose_suite
    except ImportError:
        from scripts.compose_suite import compose_suite
    compose_suite(
        args.target_dir,
        args.suite_name,
        args.modulos or ["crm", "erp", "helpdesk", "logistica"],
        db_engine=getattr(args, "db", "sqlite")
    )


def cmd_compose_orca(args):
    """Compose using the SubagentEngine with Context-Purge.
    Each module is built by an isolated subagent that receives only its slice's SPEC.
    After execution, subagent context is purged — zero cross-contamination.
    """
    ensure_environment()
    target_dir = os.path.abspath(getattr(args, "dir", "."))
    suite_name = getattr(args, "suite_name", "AIDD Suite")
    modulos = getattr(args, "modulos", None) or ["crm", "erp", "helpdesk", "logistica"]

    # Resolve SubagentEngine from src/core
    master_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    core_src = os.path.join(master_root, "src", "core")
    if core_src not in sys.path:
        sys.path.insert(0, core_src)

    try:
        from subagent_engine import SubagentSpec, ContextPurgeEngine
    except ImportError:
        print("[ERRO] SubagentEngine não encontrado em src/core/subagent_engine.py")
        sys.exit(1)

    print("=" * 80)
    print(f"🔀 [AIDD COMPOSE-ORCA v5.1] Composição via Subagentes Efêmeros")
    print(f"📁 Diretório Alvo: {target_dir}")
    print(f"📦 Suite: {suite_name}")
    print(f"🧩 Módulos ({len(modulos)}): {', '.join(modulos)}")
    print("=" * 80)

    os.makedirs(target_dir, exist_ok=True)

    # Build SubagentSpec for each module
    specs = []
    for modulo in modulos:
        spec_text = (
            f"# Vertical Slice SPEC: {modulo}\n"
            f"- Module: {modulo}\n"
            f"- Suite: {suite_name}\n"
            f"- Target: {target_dir}\n"
            f"- Generate: __init__.py, models.py, services.py, routes.py, mcp_tools.py\n"
            f"- Generate: tests/unit/test_{modulo}.py\n"
            f"- Pattern: AIDD Modular Clean Architecture\n"
            f"- DB: SQLite WAL with mod_{modulo} table\n"
            f"- Events: {modulo}_criado, {modulo}_atualizado, {modulo}_deletado\n"
            f"- REST: /api/{modulo}/(criar|listar|obter|atualizar|deletar|metricas)\n"
            f"- MCP: mod_{modulo}_(listar|criar|obter|atualizar|deletar)\n"
        )
        specs.append(SubagentSpec(
            module_name=modulo,
            spec_text=spec_text,
            target_dir=target_dir,
        ))

    # Spawn all subagents via ContextPurgeEngine
    engine = ContextPurgeEngine()
    t0 = time.time()

    results = engine.spawn_all(specs)
    total_ms = (time.time() - t0) * 1000

    # Report results
    summary = engine.get_summary()

    print("\n" + "=" * 80)
    print(f"📊 RELATÓRIO DE COMPOSIÇÃO ORCA (Context-Purge)")
    print("=" * 80)
    print(f"   - Total de Módulos:     {summary['total_modules']}")
    print(f"   - Sucesso (PASS):       {summary['success']}")
    print(f"   - Falha (FAIL):         {summary['failed']}")
    print(f"   - Erro (ERROR):         {summary['errors']}")
    print(f"   - Arquivos Criados:     {summary['total_files_created']}")
    print(f"   - Duração Total:        {total_ms:.2f} ms")
    print(f"   - Status Final:         {summary['status']}")
    print("=" * 80)

    # Per-module detail
    for name, detail in summary["modules"].items():
        icon = "✅" if detail["status"] == "success" else "❌"
        print(f"   {icon} {name}: {detail['status']} "
              f"({detail['files_created']} arquivos, {detail['duration_ms']:.1f} ms)")
        if detail["errors"]:
            for err in detail["errors"]:
                print(f"      ⚠️  {err}")

    # Save manifest
    manifest_path = os.path.join(target_dir, "COMPOSE-ORCA-MANIFEST.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n📄 Manifesto salvo: {manifest_path}")

    if summary["status"] == "REPROVADO":
        print("\n❌ [BLOQUEADO]: Um ou mais módulos falharam na composição ORCA.")
        sys.exit(1)

    print("\n🏆 [SUCESSO]: Todos os módulos compostos com êxito via Subagentes Efêmeros!")
    sys.exit(0)