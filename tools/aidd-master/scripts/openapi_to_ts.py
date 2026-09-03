#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.0-Release — Exportador de Front-End Next.js/TypeScript
=============================================================================
Introspecciona os módulos gerados (mesmo RouteRegistry que alimenta /openapi.json,
sem exigir que o servidor esteja rodando) e gera:
1. frontend/types.ts — interfaces TypeScript por módulo, inferidas dos exemplos
   de requestBody já usados no Swagger Studio.
2. frontend/ — projeto Next.js 14 (App Router) mínimo, com uma página por
   módulo consumindo a API tipada via fetch.
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


_PACKAGE_JSON = """{
  "name": "aidd-frontend",
  "version": "5.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "next": "^14.2.5",
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "typescript": "^5.4.5",
    "@types/node": "^20.11.0",
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "tailwindcss": "^3.4.4",
    "postcss": "^8.4.38",
    "autoprefixer": "^10.4.19"
  }
}
"""

_TSCONFIG_JSON = """{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
"""

_NEXT_CONFIG_JS = """/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
};
module.exports = nextConfig;
"""

_TAILWIND_CONFIG_TS = """import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: { extend: {} },
  plugins: [],
};

export default config;
"""

_POSTCSS_CONFIG_JS = """module.exports = {
  plugins: { tailwindcss: {}, autoprefixer: {} },
};
"""

_GLOBALS_CSS = """@tailwind base;
@tailwind components;
@tailwind utilities;
"""

_API_LIB_TS = """const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:3000";

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`GET ${path} falhou: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`POST ${path} falhou: ${res.status}`);
  }
  return res.json() as Promise<T>;
}
"""


def _generate_layout_tsx(suite_name: str) -> str:
    return f"""import "./globals.css";
import type {{ Metadata }} from "next";

export const metadata: Metadata = {{
  title: "{suite_name}",
  description: "Frontend gerado automaticamente pelo AIDD Master",
}};

export default function RootLayout({{ children }}: {{ children: React.ReactNode }}) {{
  return (
    <html lang="pt-BR">
      <body>{{children}}</body>
    </html>
  );
}}
"""


def _generate_home_page_tsx(suite_name: str, modulos: list) -> str:
    modulos_ts_array = ", ".join(f'"{m}"' for m in modulos)
    return f"""import Link from "next/link";

const MODULOS = [{modulos_ts_array}];

export default function Home() {{
  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 p-8">
      <h1 className="text-2xl font-bold mb-6">{suite_name}</h1>
      <ul className="space-y-2">
        {{MODULOS.map((m) => (
          <li key={{m}}>
            <Link href={{`/${{m}}`}} className="text-sky-400 hover:underline">
              {{m}}
            </Link>
          </li>
        ))}}
      </ul>
    </main>
  );
}}
"""


def _generate_module_page_tsx(slug: str, pascal: str) -> str:
    return f"""import {{ apiGet }} from "../../lib/api";
import type {{ {pascal} }} from "../../types";

export const dynamic = "force-dynamic";

export default async function {pascal}Page() {{
  let itens: {pascal}[] = [];
  let erro: string | null = null;
  try {{
    itens = await apiGet<{pascal}[]>("/api/{slug}");
  }} catch (e) {{
    erro = e instanceof Error ? e.message : "Erro desconhecido";
  }}

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 p-8">
      <h1 className="text-xl font-bold mb-4">{pascal}</h1>
      {{erro && <p className="text-rose-400">{{erro}}</p>}}
      <table className="w-full text-sm text-left">
        <thead>
          <tr className="border-b border-slate-800">
            <th className="p-2">ID</th>
            <th className="p-2">Titulo</th>
            <th className="p-2">Status</th>
          </tr>
        </thead>
        <tbody>
          {{itens.map((item: any) => (
            <tr key={{item.id}} className="border-b border-slate-900">
              <td className="p-2">{{item.id}}</td>
              <td className="p-2">{{item.titulo}}</td>
              <td className="p-2">{{item.status}}</td>
            </tr>
          ))}}
        </tbody>
      </table>
    </main>
  );
}}
"""


def export_frontend(target_dir: str, suite_name: str = "AIDD Suite", stack: str = "nextjs"):
    if stack != "nextjs":
        raise ValueError(f"Stack de frontend não suportado: {stack}")

    target_dir = os.path.abspath(target_dir)
    modulos = discover_modules(target_dir)
    if not modulos:
        print("[AVISO] Nenhum módulo encontrado em src/modules/ — abortando exportação de frontend.")
        return

    print("=" * 80)
    print(f"🚀 [AIDD v5.0] Exportando Front-End Next.js/TypeScript para: {suite_name}")
    print(f"📦 Módulos: {', '.join(modulos)}")
    print("=" * 80)

    spec = build_openapi_spec(target_dir, suite_name)

    frontend_dir = os.path.join(target_dir, "frontend")
    app_dir = os.path.join(frontend_dir, "app")
    lib_dir = os.path.join(frontend_dir, "lib")
    os.makedirs(app_dir, exist_ok=True)
    os.makedirs(lib_dir, exist_ok=True)

    def _write(rel_path, content):
        full_path = os.path.join(frontend_dir, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  [+] frontend/{rel_path}")

    _write("package.json", _PACKAGE_JSON)
    _write("tsconfig.json", _TSCONFIG_JSON)
    _write("next.config.js", _NEXT_CONFIG_JS)
    _write("tailwind.config.ts", _TAILWIND_CONFIG_TS)
    _write("postcss.config.js", _POSTCSS_CONFIG_JS)
    _write("types.ts", generate_typescript_types(spec, modulos))
    _write(os.path.join("lib", "api.ts"), _API_LIB_TS)
    _write(os.path.join("app", "globals.css"), _GLOBALS_CSS)
    _write(os.path.join("app", "layout.tsx"), _generate_layout_tsx(suite_name))
    _write(os.path.join("app", "page.tsx"), _generate_home_page_tsx(suite_name, modulos))

    for slug in modulos:
        pascal = _pascal_case(slug)
        _write(os.path.join("app", slug, "page.tsx"), _generate_module_page_tsx(slug, pascal))

    print("\n" + "=" * 80)
    print("🏆 [SUCESSO]: Front-End Next.js/TypeScript exportado em frontend/")
    print(f"   ➔ cd {frontend_dir} && npm install && npm run build")
    print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python openapi_to_ts.py <target_dir> [suite_name]")
        sys.exit(1)
    export_frontend(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "AIDD Suite")
