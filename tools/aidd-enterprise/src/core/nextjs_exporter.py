# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD — Next.js Frontend Exporter (Lei Inviolavel #11: Padrao-Ouro de Stack)
=============================================================================
Gera o frontend `frontend/` (Next.js 14 App Router + TypeScript + Tailwind
CSS) de qualquer suite AIDD (monolito modular com `src/modules/<nome>/`).

Fonte unica de verdade (Lei #11, `docs/protocolos/PADRAO-OURO-STACK-TECNOLOGICA.md`):
copiada identica em `tools/aidd-master/src/core/nextjs_exporter.py` e
`tools/aidd-enterprise/src/core/nextjs_exporter.py` — qualquer alteracao aqui
precisa ser sincronizada nas 3 copias (G_DRIFT_NUCLEO_COMPARTILHADO cobre
apenas master/enterprise; sincronizar manualmente com `componentes/`).

Design (corrige defeitos reais encontrados em `proj_ctt`, usado como
referencia inicial de "padrao-ouro" mas com inconsistencias — validacao E2E
do Fluxo 01, 18/09/2026):
  - UMA unica env var (`NEXT_PUBLIC_API_URL`, default vazio = mesma origem),
    nao duas conflitantes.
  - UMA unica camada de acesso a API (`lib/api-client.ts`), sem duplicar
    controller+hook por modulo.
  - NAO reimplementa em React os Studios nativos do backend (`/docs`,
    `/webhooks`, `/mcp`, `/openapi.json`, `/health`, `/metrics`, `/api/*`) —
    esses continuam servidos pelo processo Python (`core/openapi.py`,
    `core/webhooks.py`, `core/mcp_server.py`), sem mock e sem duplicacao. O
    Next.js gera apenas paginas de PRODUTO (dashboard + 1 pagina por modulo).
    O Nginx roteia por prefixo entre os dois servicos (`app` vs `web`).
  - Zero dependencias externas — so stdlib.
"""

import json
import os
import re
from typing import Any, Dict, List


class NextJSExporter:
    """Gera um frontend Next.js (App Router) para uma suite AIDD."""

    def export_project(self, project_dir: str, output_dir: str) -> Dict[str, Any]:
        """Gera o frontend Next.js em `output_dir` (tipicamente `<projeto>/frontend`).

        Args:
            project_dir: raiz do projeto AIDD (contem `src/modules/`).
            output_dir: pasta onde o frontend Next.js sera gerado.

        Returns:
            dict com `files_created` (list[str]) e `modules` (list[str]).
        """
        project_dir = os.path.abspath(project_dir)
        output_dir = os.path.abspath(output_dir)

        modules = self._discover_modules(project_dir)
        result: Dict[str, Any] = {"files_created": [], "modules": modules}

        os.makedirs(output_dir, exist_ok=True)

        created: List[str] = []
        created += self._write(output_dir, "package.json", self._package_json())
        created += self._write(output_dir, "next.config.js", self._next_config())
        created += self._write(output_dir, "tsconfig.json", self._tsconfig())
        created += self._write(output_dir, "tailwind.config.ts", self._tailwind_config())
        created += self._write(output_dir, "postcss.config.js", self._postcss_config())
        created += self._write(output_dir, ".eslintrc.json", self._eslintrc())
        created += self._write(output_dir, ".gitignore", self._gitignore())
        created += self._write(output_dir, ".dockerignore", self._dockerignore())
        created += self._write(output_dir, "Dockerfile", self._dockerfile())
        created += self._write(output_dir, "lib/api-client.ts", self._api_client())
        created += self._write(output_dir, "components/Nav.tsx", self._nav_component(modules))
        created += self._write(output_dir, "public/.gitkeep", "")
        created += self._write(output_dir, "app/globals.css", self._globals_css())
        created += self._write(output_dir, "app/layout.tsx", self._layout_tsx())
        created += self._write(output_dir, "app/page.tsx", self._index_page(modules))

        for mod in modules:
            created += self._write(
                output_dir, f"app/{mod}/page.tsx", self._module_page(mod)
            )

        result["files_created"] = created
        return result

    # ------------------------------------------------------------------
    # Descoberta de modulos
    # ------------------------------------------------------------------

    def _discover_modules(self, project_dir: str) -> List[str]:
        modules_dir = os.path.join(project_dir, "src", "modules")
        if not os.path.isdir(modules_dir):
            return []
        modules = []
        for entry in sorted(os.listdir(modules_dir)):
            entry_path = os.path.join(modules_dir, entry)
            if not os.path.isdir(entry_path) or entry.startswith(("_", ".")):
                continue
            has_routes = os.path.isfile(os.path.join(entry_path, "routes.py"))
            has_services = os.path.isfile(os.path.join(entry_path, "services.py"))
            if has_routes or has_services:
                modules.append(entry)
        return modules

    # ------------------------------------------------------------------
    # Config files
    # ------------------------------------------------------------------

    def _package_json(self) -> str:
        package = {
            "name": "aidd-frontend",
            "version": "1.0.0",
            "private": True,
            "scripts": {
                "dev": "next dev",
                "build": "next build",
                "start": "next start",
                "lint": "next lint",
            },
            "dependencies": {
                "next": "^14.2.5",
                "react": "^18.3.1",
                "react-dom": "^18.3.1",
            },
            "devDependencies": {
                "@types/node": "^20.11.0",
                "@types/react": "^18.3.3",
                "@types/react-dom": "^18.3.0",
                "typescript": "^5.4.5",
                "tailwindcss": "^3.4.4",
                "postcss": "^8.4.38",
                "autoprefixer": "^10.4.19",
                "eslint": "^8.57.0",
                "eslint-config-next": "^14.2.5",
            },
        }
        return json.dumps(package, indent=2, ensure_ascii=False) + "\n"

    def _next_config(self) -> str:
        return (
            "/** @type {import('next').NextConfig} */\n"
            "const nextConfig = {\n"
            "  reactStrictMode: true,\n"
            "  output: \"standalone\",\n"
            "};\n\n"
            "module.exports = nextConfig;\n"
        )

    def _tsconfig(self) -> str:
        tsconfig = {
            "compilerOptions": {
                "target": "es5",
                "lib": ["dom", "dom.iterable", "esnext"],
                "allowJs": True,
                "skipLibCheck": True,
                "strict": True,
                "noEmit": True,
                "esModuleInterop": True,
                "module": "esnext",
                "moduleResolution": "bundler",
                "resolveJsonModule": True,
                "isolatedModules": True,
                "jsx": "preserve",
                "incremental": True,
                "plugins": [{"name": "next"}],
                "paths": {"@/*": ["./*"]},
            },
            "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
            "exclude": ["node_modules"],
        }
        return json.dumps(tsconfig, indent=2, ensure_ascii=False) + "\n"

    def _tailwind_config(self) -> str:
        return (
            "import type { Config } from \"tailwindcss\";\n\n"
            "const config: Config = {\n"
            "  darkMode: \"class\",\n"
            "  content: [\n"
            "    \"./app/**/*.{ts,tsx}\",\n"
            "    \"./components/**/*.{ts,tsx}\",\n"
            "    \"./lib/**/*.{ts,tsx}\",\n"
            "  ],\n"
            "  theme: { extend: {} },\n"
            "  plugins: [],\n"
            "};\n\n"
            "export default config;\n"
        )

    def _postcss_config(self) -> str:
        return (
            "module.exports = {\n"
            "  plugins: { tailwindcss: {}, autoprefixer: {} },\n"
            "};\n"
        )

    def _eslintrc(self) -> str:
        return json.dumps({"extends": "next/core-web-vitals"}, indent=2) + "\n"

    def _gitignore(self) -> str:
        return (
            "/node_modules\n/.pnp\n.pnp.js\n/coverage\n/.next/\n/out/\n/build\n"
            ".DS_Store\n*.pem\nnpm-debug.log*\nyarn-debug.log*\nyarn-error.log*\n"
            ".env*.local\n.env\n.vercel\n*.tsbuildinfo\nnext-env.d.ts\n"
        )

    def _dockerignore(self) -> str:
        return "node_modules\n.next\n.git\n.env*\nnpm-debug.log*\n"

    def _dockerfile(self) -> str:
        return (
            "# =========================================================================\n"
            "# AIDD Frontend — Next.js Production Dockerfile (Lei #11)\n"
            "# =========================================================================\n\n"
            "FROM node:20-alpine AS builder\n"
            "WORKDIR /app\n"
            "COPY package*.json ./\n"
            "RUN npm install\n"
            "COPY . .\n"
            "RUN npm run build\n\n"
            "FROM node:20-alpine AS runner\n"
            "WORKDIR /app\n"
            "ENV NODE_ENV=production\n"
            "ENV PORT=3000\n"
            "ENV HOSTNAME=\"0.0.0.0\"\n\n"
            "RUN addgroup --system --gid 1001 nodejs && \\\n"
            "    adduser --system --uid 1001 nextjs\n\n"
            "COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./\n"
            "COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static\n"
            "COPY --from=builder --chown=nextjs:nodejs /app/public ./public\n\n"
            "USER nextjs\n"
            "EXPOSE 3000\n\n"
            "HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \\\n"
            "    CMD [\"node\", \"-e\", \"require('http').get('http://localhost:3000/', r => process.exit(r.statusCode < 500 ? 0 : 1)).on('error', () => process.exit(1))\"]\n\n"
            "CMD [\"node\", \"server.js\"]\n"
        )

    # ------------------------------------------------------------------
    # Cliente de API — fonte unica, sem duplicacao de camada
    # ------------------------------------------------------------------

    def _api_client(self) -> str:
        return (
            "// Cliente de API unico do frontend AIDD (Lei #11).\n"
            "// Fetch direto do browser para o backend Python. NEXT_PUBLIC_API_URL vazia\n"
            "// (default) significa mesma origem — funciona atras do Nginx, que roteia\n"
            "// /api, /docs, /webhooks, /mcp, /openapi.json, /health, /metrics para o\n"
            "// backend e o resto para este frontend.\n"
            "const API_BASE = process.env.NEXT_PUBLIC_API_URL || \"\";\n\n"
            "export class ApiError extends Error {\n"
            "  status: number;\n"
            "  constructor(message: string, status: number) {\n"
            "    super(message);\n"
            "    this.status = status;\n"
            "  }\n"
            "}\n\n"
            "async function request<T>(path: string, init?: RequestInit): Promise<T> {\n"
            "  const res = await fetch(`${API_BASE}${path}`, {\n"
            "    headers: { \"Content-Type\": \"application/json\" },\n"
            "    ...init,\n"
            "  });\n"
            "  if (!res.ok) {\n"
            "    throw new ApiError(`Falha em ${path}: HTTP ${res.status}`, res.status);\n"
            "  }\n"
            "  return res.json() as Promise<T>;\n"
            "}\n\n"
            "export const apiClient = {\n"
            "  get: <T>(path: string) => request<T>(path),\n"
            "  post: <T>(path: string, body: unknown) =>\n"
            "    request<T>(path, { method: \"POST\", body: JSON.stringify(body) }),\n"
            "};\n"
        )

    # ------------------------------------------------------------------
    # Componentes/paginas
    # ------------------------------------------------------------------

    def _nav_component(self, modules: List[str]) -> str:
        module_links = "\n".join(
            f'        <Link href="/{mod}" className="hover:underline">{self._label(mod)}</Link>'
            for mod in modules
        )
        return (
            "import Link from \"next/link\";\n\n"
            "// Links para /docs, /webhooks e /mcp usam <a> (nao <Link>): sao rotas\n"
            "// nativas do backend Python, roteadas pelo Nginx para outro servico —\n"
            "// nao existem no roteador do Next.js.\n"
            "export function Nav() {\n"
            "  return (\n"
            "    <nav className=\"flex flex-wrap gap-4 items-center px-6 py-4 border-b border-zinc-200 dark:border-zinc-800\">\n"
            "      <Link href=\"/\" className=\"font-semibold\">AIDD</Link>\n"
            f"{module_links}\n"
            "      <span className=\"flex-1\" />\n"
            "      <a href=\"/docs\" className=\"hover:underline\">Swagger</a>\n"
            "      <a href=\"/webhooks\" className=\"hover:underline\">Webhooks</a>\n"
            "      <a href=\"/mcp\" className=\"hover:underline\">MCP</a>\n"
            "    </nav>\n"
            "  );\n"
            "}\n"
        )

    def _globals_css(self) -> str:
        return (
            "@tailwind base;\n@tailwind components;\n@tailwind utilities;\n\n"
            "body {\n"
            "  @apply bg-white text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100;\n"
            "}\n"
        )

    def _layout_tsx(self) -> str:
        return (
            "import type { Metadata } from \"next\";\n"
            "import \"./globals.css\";\n"
            "import { Nav } from \"@/components/Nav\";\n\n"
            "export const metadata: Metadata = {\n"
            "  title: \"AIDD\",\n"
            "  description: \"Gerado pelo Ecossistema AIDD (Lei #11: Next.js + TypeScript + Tailwind)\",\n"
            "};\n\n"
            "export default function RootLayout({ children }: { children: React.ReactNode }) {\n"
            "  return (\n"
            "    <html lang=\"pt-BR\">\n"
            "      <body>\n"
            "        <Nav />\n"
            "        {children}\n"
            "      </body>\n"
            "    </html>\n"
            "  );\n"
            "}\n"
        )

    def _index_page(self, modules: List[str]) -> str:
        cards = "\n".join(
            f'          <Link href="/{mod}" className="rounded-lg border border-zinc-200 dark:border-zinc-800 p-6 hover:border-zinc-400 dark:hover:border-zinc-600 transition">\n'
            f'            <h2 className="text-lg font-medium">{self._label(mod)}</h2>\n'
            f'          </Link>'
            for mod in modules
        )
        return (
            "import Link from \"next/link\";\n\n"
            "export default function Home() {\n"
            "  return (\n"
            "    <main className=\"max-w-5xl mx-auto px-6 py-10\">\n"
            "      <h1 className=\"text-2xl font-semibold mb-8\">Dashboard</h1>\n"
            "      <div className=\"grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4\">\n"
            f"{cards}\n"
            "      </div>\n"
            "    </main>\n"
            "  );\n"
            "}\n"
        )

    def _module_page(self, module_name: str) -> str:
        label = self._label(module_name)
        pascal = self._to_pascal_case(module_name)
        return (
            '"use client";\n\n'
            'import { useEffect, useState } from "react";\n'
            'import { apiClient, ApiError } from "@/lib/api-client";\n\n'
            "interface Item {\n"
            "  id: number;\n"
            "  titulo: string;\n"
            "  status: string;\n"
            "  [key: string]: unknown;\n"
            "}\n\n"
            f"export default function {pascal}Page() {{\n"
            "  const [items, setItems] = useState<Item[]>([]);\n"
            "  const [loading, setLoading] = useState(true);\n"
            "  const [error, setError] = useState<string | null>(null);\n"
            '  const [titulo, setTitulo] = useState("");\n\n'
            "  const carregar = () => {\n"
            "    setLoading(true);\n"
            f'    apiClient.get<Item[]>("/api/{module_name}")\n'
            "      .then((data) => { setItems(data); setError(null); })\n"
            "      .catch((err: ApiError) => setError(err.message))\n"
            "      .finally(() => setLoading(false));\n"
            "  };\n\n"
            "  useEffect(carregar, []);\n\n"
            "  const criar = async (e: React.FormEvent) => {\n"
            "    e.preventDefault();\n"
            '    if (!titulo.trim()) return;\n'
            "    try {\n"
            f'      await apiClient.post("/api/{module_name}/criar", {{ titulo, status: "ativo" }});\n'
            '      setTitulo("");\n'
            "      carregar();\n"
            "    } catch (err) {\n"
            "      setError((err as ApiError).message);\n"
            "    }\n"
            "  };\n\n"
            "  return (\n"
            '    <main className="max-w-3xl mx-auto px-6 py-10">\n'
            f'      <h1 className="text-2xl font-semibold mb-6">{label}</h1>\n\n'
            '      <form onSubmit={criar} className="flex gap-2 mb-8">\n'
            "        <input\n"
            "          value={titulo}\n"
            "          onChange={(e) => setTitulo(e.target.value)}\n"
            f'          placeholder="Novo item em {label.lower()}"\n'
            '          className="flex-1 rounded-md border border-zinc-300 dark:border-zinc-700 bg-transparent px-3 py-2"\n'
            "        />\n"
            '        <button type="submit" className="rounded-md bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 px-4 py-2">\n'
            "          Criar\n"
            "        </button>\n"
            "      </form>\n\n"
            '      {loading && <p className="text-zinc-500">Carregando...</p>}\n'
            '      {error && <p className="text-red-600">{error}</p>}\n\n'
            '      <div className="grid gap-3">\n'
            "        {items.map((item) => (\n"
            '          <div key={item.id} className="rounded-lg border border-zinc-200 dark:border-zinc-800 p-4">\n'
            '            <p className="font-medium">{item.titulo}</p>\n'
            '            <p className="text-sm text-zinc-500">{item.status}</p>\n'
            "          </div>\n"
            "        ))}\n"
            "        {!loading && items.length === 0 && (\n"
            '          <p className="text-zinc-500">Nenhum registro encontrado.</p>\n'
            "        )}\n"
            "      </div>\n"
            "    </main>\n"
            "  );\n"
            "}\n"
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _write(output_dir: str, rel_path: str, content: str) -> List[str]:
        full_path = os.path.join(output_dir, *rel_path.split("/"))
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return [full_path]

    @staticmethod
    def _label(module_name: str) -> str:
        return module_name.replace("_", " ").replace("-", " ").title()

    @staticmethod
    def _to_pascal_case(s: str) -> str:
        return "".join(word.capitalize() for word in re.split(r"[-_]+", s))
