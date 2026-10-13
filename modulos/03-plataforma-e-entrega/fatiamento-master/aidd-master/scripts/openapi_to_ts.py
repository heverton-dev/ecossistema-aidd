#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.0-Release — Exportador de Front-End TanStack/TypeScript
=============================================================================
Introspecciona os módulos gerados (mesmo RouteRegistry que alimenta /openapi.json,
sem exigir que o servidor esteja rodando) e gera:
1. frontend/types.ts — interfaces TypeScript por módulo, inferidas dos exemplos
   de requestBody já usados no Swagger Studio.
2. frontend/ — projeto TanStack Router + Vite (SPA), gerado pelo TanStackRouterExporter,
   com uma página por módulo consumindo a API via fetch.
"""

import os
import sys
import json


def _pascal_case(slug: str) -> str:
    return "".join(w.capitalize() for w in slug.split("_"))


def _infer_ts_type(value) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "number"
    if isinstance(value, float):
        return "number"
    if isinstance(value, list):
        return "any[]"
    if isinstance(value, dict):
        return "Record<string, any>"
    return "string"


def discover_modules(target_dir: str) -> list:
    modules_dir = os.path.join(target_dir, "src", "modules")
    if not os.path.isdir(modules_dir):
        return []
    return sorted(
        m for m in os.listdir(modules_dir)
        if os.path.isdir(os.path.join(modules_dir, m)) and not m.startswith("__")
    )


def build_openapi_spec(target_dir: str, suite_name: str = "AIDD Suite") -> dict:
    """Importa os módulos gerados e monta o spec OpenAPI 3.1 em memória, sem
    exigir que o servidor HTTP esteja de pé — mesma introspecção do RouteRegistry
    que alimenta /openapi.json em tempo de execução."""
    src_dir = os.path.join(target_dir, "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

    from core.openapi import RouteRegistry

    # RouteRegistry é um Singleton (ver templates/v2/openapi.py): toda
    # instância criada neste processo compartilha o mesmo `self.routes`/
    # `self.endpoints`, então registrar as rotas de cada módulo já as
    # expõe no registry compartilhado — nenhuma mesclagem explícita é
    # necessária (mesclar o singleton nele mesmo causaria loop infinito).
    shared_registry = RouteRegistry()
    for slug in discover_modules(target_dir):
        module_name = f"modules.{slug}.routes"
        mod = __import__(module_name, fromlist=["registrar_rotas", "registry"])
        mod.registrar_rotas(None)

    return shared_registry.generate_openapi_json(suite_name, "5.0.0")


def generate_typescript_types(spec: dict, modulos: list) -> str:
    """Gera interfaces TS por módulo a partir do exemplo de requestBody de /criar."""
    lines = [
        "// Gerado automaticamente por scripts/openapi_to_ts.py — NÃO EDITE MANUALMENTE.",
        "// Fonte: introspecção do RouteRegistry (mesma base do /openapi.json).",
        "",
    ]

    for slug in modulos:
        pascal = _pascal_case(slug)
        example = None
        criar_op = spec.get("paths", {}).get(f"/api/{slug}/criar", {}).get("post")
        if criar_op:
            schema = criar_op.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
            example = schema.get("example")

        campos = example if isinstance(example, dict) else {"titulo": "Exemplo", "status": "ativo"}

        lines.append(f"export interface {pascal} {{")
        lines.append("  id: number;")
        for k, v in campos.items():
            lines.append(f"  {k}: {_infer_ts_type(v)};")
        lines.append("  criado_em?: string;")
        lines.append("  atualizado_em?: string;")
        lines.append("}")
        lines.append("")
        lines.append(f"export interface {pascal}CreatePayload {{")
        for k, v in campos.items():
            lines.append(f"  {k}: {_infer_ts_type(v)};")
        lines.append("}")
        lines.append("")

    return "\n".join(lines)


def _carregar_exportador():
    """Importa o TanStackRouterExporter (copiado em scripts/ no projeto gerado, ou do núcleo compartilhado)."""
    try:
        from tanstack_exporter import TanStackRouterExporter
        return TanStackRouterExporter
    except ImportError:
        aqui = os.path.dirname(os.path.abspath(__file__))
        candidatos = [os.path.join(aqui, "..", "src", "core")]
        atual = aqui
        while os.path.dirname(atual) != atual:
            if os.path.isfile(os.path.join(atual, "ecossistema.py")):
                candidatos.append(os.path.join(atual, "componentes", "compartilhado", "src-core"))
                break
            atual = os.path.dirname(atual)
        for c in candidatos:
            if os.path.isdir(c) and c not in sys.path:
                sys.path.insert(0, c)
        from tanstack_exporter import TanStackRouterExporter
        return TanStackRouterExporter


def export_frontend(target_dir: str, suite_name: str = "AIDD Suite", stack: str = "tanstack"):
    if stack != "tanstack":
        raise ValueError(f"Stack de frontend não suportado: {stack}")

    target_dir = os.path.abspath(target_dir)
    modulos = discover_modules(target_dir)
    if not modulos:
        print("[AVISO] Nenhum módulo encontrado em src/modules/ — abortando exportação de frontend.")
        return

    print("=" * 80)
    print(f"🚀 [AIDD v5.0] Exportando Front-End TanStack/TypeScript para: {suite_name}")
    print(f"📦 Módulos: {', '.join(modulos)}")
    print("=" * 80)

    spec = build_openapi_spec(target_dir, suite_name)

    frontend_dir = os.path.join(target_dir, "frontend")
    resultado = _carregar_exportador()().export_project(target_dir, frontend_dir, suite_name=suite_name)
    print(f"  [+] frontend/ ({len(resultado['files_created'])} arquivos, módulos: {', '.join(resultado['modules'])})")

    tipos_path = os.path.join(frontend_dir, "src", "types.ts")
    os.makedirs(os.path.dirname(tipos_path), exist_ok=True)
    with open(tipos_path, "w", encoding="utf-8") as f:
        f.write(generate_typescript_types(spec, modulos))
    print("  [+] frontend/src/types.ts")

    print("\n" + "=" * 80)
    print("🏆 [SUCESSO]: Front-End TanStack/TypeScript exportado em frontend/")
    print(f"   ➔ cd {frontend_dir} && npm install && npm run build")
    print("=" * 80)
