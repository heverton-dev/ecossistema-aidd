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

Design funcional (corrige defeitos reais encontrados em `proj_ctt`, usado
como referencia de "padrao-ouro" mas com inconsistencias — validacao E2E do
Fluxo 01, 18/09/2026):
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

Design VISUAL (achado real, corrigido 18/09/2026): a Lei #11 exige nao so a
stack (Next.js/TS/Tailwind), mas a MESMA estetica do padrao-ouro `proj_ctt`
em todas as camadas de frontend. A primeira versao deste gerador produzia
paginas funcionais mas visualmente genericas (sem paleta, sem componentes
compartilhados) — reescrito para reproduzir a paleta real do proj_ctt
(Tailwind `slate` neutro + acentos semanticos emerald/amber/rose/blue, modo
escuro via classe + localStorage + script anti-flash), os componentes
compartilhados reais (`Navbar`, `Modal`, `ConfirmDialog`, `FormField`) e o
padrao real de pagina de modulo (header com acoes, tabela em card, modais de
criar/editar, confirmacao de exclusao, toast) — sem a cor de marca
hardcoded da CTT (`#DA291C`), substituida por um acento neutro monocromatico
(slate-900/white) por este ser um gerador de proposito geral, nao
CTT-especifico.
"""

import json
import os
import re
from typing import Any, Dict, List

try:
    from design_catalog import escolher_paleta
except ImportError:
    import sys
    _njs_dir = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "componentes", "compartilhado", "src-core"
    )
    if os.path.isdir(_njs_dir) and _njs_dir not in sys.path:
        sys.path.insert(0, _njs_dir)
    from design_catalog import escolher_paleta


class NextJSExporter:
    """Gera um frontend Next.js (App Router) para uma suite AIDD."""

    def export_project(self, project_dir: str, output_dir: str, suite_name: str = "") -> Dict[str, Any]:
        """Gera o frontend Next.js em `output_dir` (tipicamente `<projeto>/frontend`).

        Args:
            project_dir: raiz do projeto AIDD (contem `src/modules/`).
            output_dir: pasta onde o frontend Next.js sera gerado.
            suite_name: nome do projeto/suite (usado para resolver a
                identidade visual quando nao ha DESIGN-SYSTEM.json — ver
                `_resolver_paleta`).

        Returns:
            dict com `files_created` (list[str]) e `modules` (list[str]).
        """
        project_dir = os.path.abspath(project_dir)
        output_dir = os.path.abspath(output_dir)

        modules = self._discover_modules(project_dir)
        paleta = self._resolver_paleta(project_dir, suite_name or os.path.basename(project_dir), modules)
        result: Dict[str, Any] = {"files_created": [], "modules": modules, "paleta": paleta}

        os.makedirs(output_dir, exist_ok=True)

        created: List[str] = []
        created += self._write(output_dir, "package.json", self._package_json())
        created += self._write(output_dir, "next.config.js", self._next_config())
        created += self._write(output_dir, "tsconfig.json", self._tsconfig())
        created += self._write(output_dir, "tailwind.config.ts", self._tailwind_config(paleta))
        created += self._write(output_dir, "postcss.config.js", self._postcss_config())
        created += self._write(output_dir, ".eslintrc.json", self._eslintrc())
        created += self._write(output_dir, ".gitignore", self._gitignore())
        created += self._write(output_dir, ".dockerignore", self._dockerignore())
        created += self._write(output_dir, "Dockerfile", self._dockerfile())
        created += self._write(output_dir, "lib/api-client.ts", self._api_client())
        created += self._write(output_dir, "lib/theme-script.ts", self._theme_script())
        created += self._write(output_dir, "components/icons.tsx", self._icons_component())
        created += self._write(output_dir, "components/Navbar.tsx", self._navbar_component(modules))
        created += self._write(output_dir, "components/shared/Modal.tsx", self._modal_component())
        created += self._write(output_dir, "components/shared/ConfirmDialog.tsx", self._confirm_dialog_component())
        created += self._write(output_dir, "components/shared/FormField.tsx", self._form_field_component())
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

    def _resolver_paleta(self, project_dir: str, identidade: str, modules: List[str]) -> Dict[str, str]:
        """Resolve a paleta de marca do projeto (Lei #11): usa
        `DESIGN-SYSTEM.json` gerado pelo `aidd-planner` (fonte preferida —
        pode ter sido customizado por humano depois) quando existe na raiz
        do projeto; caso contrário deriva a MESMA paleta que o planner
        geraria, direto do nome do projeto (determinístico — nunca uma cor
        fixa/hardcoded, mesmo quando o projeto não passou pelo planner,
        lacuna de handoff já documentada no ecossistema)."""
        design_system_path = os.path.join(project_dir, "DESIGN-SYSTEM.json")
        if os.path.isfile(design_system_path):
            try:
                with open(design_system_path, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                paleta = dados.get("paleta")
                if paleta and "primaria" in paleta:
                    return paleta
            except (OSError, json.JSONDecodeError):
                pass
        return escolher_paleta(f"{identidade} {' '.join(modules)}")

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

    def _tailwind_config(self, paleta: Dict[str, str]) -> str:
        # Cor de marca (Lei #11): vem do DESIGN-SYSTEM.json do projeto (unico
        # por projeto, nunca fixo — ver _resolver_paleta). Neutro estrutural
        # (slate) e semanticas (emerald/amber/rose/blue) sao fixos, iguais em
        # todo projeto: sao convencao de UX universal, nao identidade visual.
        return (
            "import type { Config } from \"tailwindcss\";\n\n"
            "const config: Config = {\n"
            "  darkMode: \"class\",\n"
            "  content: [\n"
            "    \"./app/**/*.{ts,tsx}\",\n"
            "    \"./components/**/*.{ts,tsx}\",\n"
            "    \"./lib/**/*.{ts,tsx}\",\n"
            "  ],\n"
            "  theme: {\n"
            "    extend: {\n"
            "      colors: {\n"
            "        primary: {\n"
            f"          DEFAULT: \"{paleta['primaria']}\",\n"
            f"          hover: \"{paleta['primaria_hover']}\",\n"
            "          foreground: \"#ffffff\",\n"
            "        },\n"
            "      },\n"
            "    },\n"
            "  },\n"
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

    def _icons_component(self) -> str:
        # SVGs inline no estilo Lucide/Feather (stroke=currentColor), zero
        # dependencia externa — mesmo padrao do proj_ctt/components/icons.tsx.
        def icon(name: str, path: str) -> str:
            return (
                f"export function {name}(props: React.SVGProps<SVGSVGElement>) {{\n"
                "  return (\n"
                "    <svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" strokeWidth={2}\n"
                "      strokeLinecap=\"round\" strokeLinejoin=\"round\" className=\"w-5 h-5\" {...props}>\n"
                f"      {path}\n"
                "    </svg>\n"
                "  );\n"
                "}\n"
            )
        return (
            icon("PlusIcon", '<path d="M12 5v14M5 12h14" />') + "\n"
            + icon("PencilIcon", '<path d="M12 20h9M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" />') + "\n"
            + icon("TrashIcon", '<path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6h14Z" />') + "\n"
            + icon("XIcon", '<path d="M18 6 6 18M6 6l12 12" />') + "\n"
            + icon("SunIcon", '<circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />') + "\n"
            + icon("MoonIcon", '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79Z" />') + "\n"
        )

    def _navbar_component(self, modules: List[str]) -> str:
        module_links = "\n".join(
            f'        <Link href="/{mod}" className={{navLinkClass(pathname === "/{mod}")}}>{self._label(mod)}</Link>'
            for mod in modules
        )
        return (
            '"use client";\n\n'
            'import Link from "next/link";\n'
            'import { usePathname } from "next/navigation";\n'
            'import { useEffect, useState } from "react";\n'
            'import { SunIcon, MoonIcon } from "@/components/icons";\n\n'
            "function navLinkClass(active: boolean): string {\n"
            "  return active\n"
            "    ? \"px-3 py-1.5 rounded-md text-sm font-semibold bg-slate-100 dark:bg-slate-800 text-primary\"\n"
            "    : \"px-3 py-1.5 rounded-md text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/60\";\n"
            "}\n\n"
            "// Links para /docs, /docs/guia, /webhooks, /mcp e /metrics usam <a> (nao\n"
            "// <Link>): sao rotas nativas do backend Python, roteadas pelo Nginx para\n"
            "// outro servico — nao existem no roteador do Next.js.\n"
            "export function Navbar() {\n"
            "  const pathname = usePathname();\n"
            "  const [isDark, setIsDark] = useState(false);\n\n"
            "  useEffect(() => {\n"
            "    setIsDark(document.documentElement.classList.contains(\"dark\"));\n"
            "  }, []);\n\n"
            "  const alternarTema = () => {\n"
            "    const proximo = !isDark;\n"
            "    setIsDark(proximo);\n"
            "    document.documentElement.classList.toggle(\"dark\", proximo);\n"
            "    try { localStorage.setItem(\"theme\", proximo ? \"dark\" : \"light\"); } catch {}\n"
            "  };\n\n"
            "  return (\n"
            "    <header className=\"sticky top-0 z-40 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800\">\n"
            "      <nav className=\"max-w-6xl mx-auto flex flex-wrap items-center gap-2 px-6 py-3\">\n"
            "        <Link href=\"/\" className=\"flex items-center gap-2 mr-4\">\n"
            "          <span className=\"w-8 h-8 rounded-md bg-primary text-primary-foreground flex items-center justify-center font-bold text-sm\">A</span>\n"
            "          <span className=\"font-semibold text-slate-900 dark:text-white\">AIDD</span>\n"
            "        </Link>\n"
            f"{module_links}\n"
            "        <span className=\"flex-1\" />\n"
            "        <a href=\"/docs\" className={navLinkClass(false)}>Swagger</a>\n"
            "        <a href=\"/docs/guia\" className={navLinkClass(false)}>Guia</a>\n"
            "        <a href=\"/webhooks\" className={navLinkClass(false)}>Webhooks</a>\n"
            "        <a href=\"/mcp\" className={navLinkClass(false)}>MCP</a>\n"
            "        <a href=\"/metrics\" className={navLinkClass(false)}>Métricas</a>\n"
            "        <button\n"
            "          type=\"button\"\n"
            "          onClick={alternarTema}\n"
            "          aria-label=\"Alternar tema\"\n"
            "          className=\"ml-2 p-2 rounded-md text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800\"\n"
            "        >\n"
            "          {isDark ? <SunIcon /> : <MoonIcon />}\n"
            "        </button>\n"
            "      </nav>\n"
            "    </header>\n"
            "  );\n"
            "}\n"
        )

    def _modal_component(self) -> str:
        return (
            '"use client";\n\n'
            'import { useEffect } from "react";\n'
            'import { XIcon } from "@/components/icons";\n\n'
            "interface ModalProps {\n"
            "  aberto: boolean;\n"
            "  titulo: string;\n"
            "  onFechar: () => void;\n"
            "  children: React.ReactNode;\n"
            "  footer?: React.ReactNode;\n"
            "}\n\n"
            "export function Modal({ aberto, titulo, onFechar, children, footer }: ModalProps) {\n"
            "  useEffect(() => {\n"
            "    if (!aberto) return;\n"
            '    const onEsc = (e: KeyboardEvent) => { if (e.key === "Escape") onFechar(); };\n'
            '    window.addEventListener("keydown", onEsc);\n'
            '    return () => window.removeEventListener("keydown", onEsc);\n'
            "  }, [aberto, onFechar]);\n\n"
            "  if (!aberto) return null;\n\n"
            "  return (\n"
            '    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 backdrop-blur-sm p-4">\n'
            '      <div className="w-full max-w-lg rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xl">\n'
            '        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200 dark:border-slate-800">\n'
            '          <h2 className="text-base font-semibold text-slate-900 dark:text-white">{titulo}</h2>\n'
            '          <button type="button" onClick={onFechar} aria-label="Fechar"\n'
            '            className="p-1 rounded-md text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800">\n'
            "            <XIcon />\n"
            "          </button>\n"
            "        </div>\n"
            '        <div className="p-5">{children}</div>\n'
            '        {footer && <div className="flex justify-end gap-2 px-5 py-4 border-t border-slate-200 dark:border-slate-800">{footer}</div>}\n'
            "      </div>\n"
            "    </div>\n"
            "  );\n"
            "}\n"
        )

    def _confirm_dialog_component(self) -> str:
        return (
            'import { Modal } from "@/components/shared/Modal";\n\n'
            "interface ConfirmDialogProps {\n"
            "  aberto: boolean;\n"
            "  titulo: string;\n"
            "  mensagem: string;\n"
            "  onCancelar: () => void;\n"
            "  onConfirmar: () => void;\n"
            "}\n\n"
            "export function ConfirmDialog({ aberto, titulo, mensagem, onCancelar, onConfirmar }: ConfirmDialogProps) {\n"
            "  return (\n"
            "    <Modal\n"
            "      aberto={aberto}\n"
            "      titulo={titulo}\n"
            "      onFechar={onCancelar}\n"
            "      footer={\n"
            "        <>\n"
            '          <button type="button" onClick={onCancelar}\n'
            '            className="px-4 py-2 rounded-md text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800">\n'
            "            Cancelar\n"
            "          </button>\n"
            '          <button type="button" onClick={onConfirmar}\n'
            '            className="px-4 py-2 rounded-md text-sm font-medium bg-rose-600 hover:bg-rose-700 text-white">\n'
            "            Excluir\n"
            "          </button>\n"
            "        </>\n"
            "      }\n"
            "    >\n"
            '      <p className="text-sm text-slate-600 dark:text-slate-300">{mensagem}</p>\n'
            "    </Modal>\n"
            "  );\n"
            "}\n"
        )

    def _form_field_component(self) -> str:
        return (
            "export const inputBaseStyles =\n"
            '  "w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 ' \
            'px-3 py-2 text-sm text-slate-900 dark:text-white placeholder:text-slate-400 ' \
            'focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary";\n\n'
            "interface FormFieldProps {\n"
            "  label: string;\n"
            "  children: React.ReactNode;\n"
            "}\n\n"
            "export function FormField({ label, children }: FormFieldProps) {\n"
            "  return (\n"
            '    <label className="block mb-4">\n'
            '      <span className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">{label}</span>\n'
            "      {children}\n"
            "    </label>\n"
            "  );\n"
            "}\n"
        )

    def _globals_css(self) -> str:
        # Sem CSS customizado alem das 3 diretivas — igual ao padrao-ouro
        # (proj_ctt/planos-ctt-app/frontend/app/globals.css): todo estilo via
        # classes Tailwind inline nos componentes, nao em folha separada.
        return "@tailwind base;\n@tailwind components;\n@tailwind utilities;\n"

    def _theme_script(self) -> str:
        # Script anti-flash: aplica a classe "dark" no <html> ANTES da
        # hidratacao (evita o "flash" de tema claro em quem prefere escuro),
        # mesmo mecanismo do padrao-ouro proj_ctt (localStorage + matchMedia).
        return (
            "export const THEME_INIT_SCRIPT = `\n"
            "(function() {\n"
            "  try {\n"
            "    var stored = localStorage.getItem('theme');\n"
            "    var dark = stored ? stored === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches;\n"
            "    document.documentElement.classList.toggle('dark', dark);\n"
            "  } catch (e) {}\n"
            "})();\n"
            "`;\n"
        )

    def _layout_tsx(self) -> str:
        return (
            "import type { Metadata } from \"next\";\n"
            "import \"./globals.css\";\n"
            "import { Navbar } from \"@/components/Navbar\";\n"
            "import { THEME_INIT_SCRIPT } from \"@/lib/theme-script\";\n\n"
            "export const metadata: Metadata = {\n"
            "  title: \"AIDD\",\n"
            "  description: \"Gerado pelo Ecossistema AIDD (Lei #11: Next.js + TypeScript + Tailwind)\",\n"
            "};\n\n"
            "export default function RootLayout({ children }: { children: React.ReactNode }) {\n"
            "  return (\n"
            "    <html lang=\"pt-BR\" suppressHydrationWarning>\n"
            "      <head>\n"
            "        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />\n"
            "      </head>\n"
            "      <body className=\"bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 font-sans selection:bg-primary selection:text-primary-foreground\">\n"
            "        <Navbar />\n"
            "        {children}\n"
            "      </body>\n"
            "    </html>\n"
            "  );\n"
            "}\n"
        )

    def _index_page(self, modules: List[str]) -> str:
        cards = "\n".join(
            f'          <Link href="/{mod}" className="group rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm hover:shadow-md hover:border-primary/40 transition">\n'
            f'            <div className="w-10 h-10 rounded-lg bg-primary/10 text-primary flex items-center justify-center font-bold mb-3">{self._label(mod)[:1]}</div>\n'
            f'            <h2 className="text-base font-semibold text-slate-900 dark:text-white group-hover:text-primary">{self._label(mod)}</h2>\n'
            f'            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Gerenciar registros de {self._label(mod).lower()}</p>\n'
            f'          </Link>'
            for mod in modules
        )
        return (
            "import Link from \"next/link\";\n\n"
            "export default function Home() {\n"
            "  return (\n"
            "    <main className=\"max-w-6xl mx-auto px-6 py-10\">\n"
            "      <h1 className=\"text-2xl font-bold text-slate-900 dark:text-white mb-1\">Dashboard</h1>\n"
            "      <p className=\"text-sm text-slate-500 dark:text-slate-400 mb-8\">Selecione um módulo para gerenciar seus registros.</p>\n"
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
            'import { apiClient, ApiError } from "@/lib/api-client";\n'
            'import { Modal } from "@/components/shared/Modal";\n'
            'import { ConfirmDialog } from "@/components/shared/ConfirmDialog";\n'
            'import { FormField, inputBaseStyles } from "@/components/shared/FormField";\n'
            'import { PlusIcon, PencilIcon, TrashIcon } from "@/components/icons";\n\n'
            "interface Item {\n"
            "  id: number;\n"
            "  titulo: string;\n"
            "  descricao?: string;\n"
            "  status: string;\n"
            "  [key: string]: unknown;\n"
            "}\n\n"
            "const BADGE_POR_STATUS: Record<string, string> = {\n"
            '  ativo: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300",\n'
            '  concluido: "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300",\n'
            '  pendente: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",\n'
            '  inativo: "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300",\n'
            "};\n"
            "function corBadge(status: string): string {\n"
            '  return BADGE_POR_STATUS[status] ?? BADGE_POR_STATUS.inativo;\n'
            "}\n\n"
            f"export default function {pascal}Page() {{\n"
            "  const [items, setItems] = useState<Item[]>([]);\n"
            "  const [loading, setLoading] = useState(true);\n"
            "  const [erro, setErro] = useState<string | null>(null);\n"
            "  const [toast, setToast] = useState<string | null>(null);\n\n"
            "  const [modalAberto, setModalAberto] = useState(false);\n"
            "  const [itemEditando, setItemEditando] = useState<Item | null>(null);\n"
            "  const [itemExcluindo, setItemExcluindo] = useState<Item | null>(null);\n"
            '  const [titulo, setTitulo] = useState("");\n'
            '  const [descricao, setDescricao] = useState("");\n\n'
            "  const carregar = () => {\n"
            "    setLoading(true);\n"
            f'    apiClient.get<Item[]>("/api/{module_name}")\n'
            "      .then((data) => { setItems(data); setErro(null); })\n"
            "      .catch((err: ApiError) => setErro(err.message))\n"
            "      .finally(() => setLoading(false));\n"
            "  };\n\n"
            "  useEffect(carregar, []);\n\n"
            "  useEffect(() => {\n"
            "    if (!toast) return;\n"
            "    const t = setTimeout(() => setToast(null), 3000);\n"
            "    return () => clearTimeout(t);\n"
            "  }, [toast]);\n\n"
            "  const abrirNovo = () => {\n"
            '    setItemEditando(null); setTitulo(""); setDescricao(""); setModalAberto(true);\n'
            "  };\n"
            "  const abrirEdicao = (item: Item) => {\n"
            '    setItemEditando(item); setTitulo(item.titulo); setDescricao(item.descricao ?? ""); setModalAberto(true);\n'
            "  };\n\n"
            "  const salvar = async (e: React.FormEvent) => {\n"
            "    e.preventDefault();\n"
            "    if (!titulo.trim()) return;\n"
            "    try {\n"
            "      if (itemEditando) {\n"
            f'        await apiClient.post("/api/{module_name}/atualizar", {{ id: itemEditando.id, titulo, descricao }});\n'
            '        setToast("Registro atualizado.");\n'
            "      } else {\n"
            f'        await apiClient.post("/api/{module_name}/criar", {{ titulo, descricao, status: "ativo" }});\n'
            '        setToast("Registro criado.");\n'
            "      }\n"
            "      setModalAberto(false);\n"
            "      carregar();\n"
            "    } catch (err) {\n"
            "      setErro((err as ApiError).message);\n"
            "    }\n"
            "  };\n\n"
            "  const excluir = async () => {\n"
            "    if (!itemExcluindo) return;\n"
            "    try {\n"
            f'      await apiClient.post("/api/{module_name}/deletar", {{ id: itemExcluindo.id }});\n'
            '      setToast("Registro removido.");\n'
            "      setItemExcluindo(null);\n"
            "      carregar();\n"
            "    } catch (err) {\n"
            "      setErro((err as ApiError).message);\n"
            "    }\n"
            "  };\n\n"
            "  return (\n"
            '    <main className="max-w-5xl mx-auto px-6 py-10">\n'
            '      <div className="flex flex-wrap items-center justify-between gap-3 mb-6">\n'
            "        <div>\n"
            f'          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">{label}</h1>\n'
            f'          <p className="text-sm text-slate-500 dark:text-slate-400">Registros do módulo {label.lower()}</p>\n'
            "        </div>\n"
            '        <button type="button" onClick={abrirNovo}\n'
            '          className="flex items-center gap-1.5 rounded-lg bg-primary hover:bg-primary-hover text-primary-foreground text-sm font-medium px-4 py-2">\n'
            f'          <PlusIcon className="w-4 h-4" /> Novo {label}\n'
            "        </button>\n"
            "      </div>\n\n"
            '      {erro && <p className="mb-4 text-sm text-rose-600">{erro}</p>}\n\n'
            '      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm overflow-x-auto">\n'
            '        <table className="w-full text-sm">\n'
            '          <thead className="bg-slate-50 dark:bg-slate-800/50 text-left text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">\n'
            "            <tr>\n"
            '              <th className="px-4 py-3 font-medium">Título</th>\n'
            '              <th className="px-4 py-3 font-medium">Status</th>\n'
            '              <th className="px-4 py-3 font-medium text-right">Ações</th>\n'
            "            </tr>\n"
            "          </thead>\n"
            '          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">\n'
            "            {items.map((item) => (\n"
            '              <tr key={item.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">\n'
            '                <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">{item.titulo}</td>\n'
            "                <td className=\"px-4 py-3\">\n"
            '                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${corBadge(item.status)}`}>{item.status}</span>\n'
            "                </td>\n"
            '                <td className="px-4 py-3 text-right space-x-1">\n'
            '                  <button type="button" onClick={() => abrirEdicao(item)} aria-label="Editar"\n'
            '                    className="p-1.5 rounded-md text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"><PencilIcon className="w-4 h-4" /></button>\n'
            '                  <button type="button" onClick={() => setItemExcluindo(item)} aria-label="Excluir"\n'
            '                    className="p-1.5 rounded-md text-slate-400 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950"><TrashIcon className="w-4 h-4" /></button>\n'
            "                </td>\n"
            "              </tr>\n"
            "            ))}\n"
            "          </tbody>\n"
            "        </table>\n"
            '        {loading && <p className="px-4 py-6 text-sm text-slate-500">Carregando...</p>}\n'
            '        {!loading && items.length === 0 && (\n'
            '          <p className="px-4 py-6 text-sm text-slate-500">Nenhum registro encontrado.</p>\n'
            "        )}\n"
            "      </div>\n\n"
            "      <Modal\n"
            "        aberto={modalAberto}\n"
            f'        titulo={{itemEditando ? "Editar {label}" : "Novo {label}"}}\n'
            "        onFechar={() => setModalAberto(false)}\n"
            "        footer={\n"
            "          <>\n"
            '            <button type="button" onClick={() => setModalAberto(false)}\n'
            '              className="px-4 py-2 rounded-md text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800">Cancelar</button>\n'
            '            <button type="submit" form="form-item" className="px-4 py-2 rounded-md text-sm font-medium bg-primary hover:bg-primary-hover text-primary-foreground">Salvar</button>\n'
            "          </>\n"
            "        }\n"
            "      >\n"
            '        <form id="form-item" onSubmit={salvar}>\n'
            '          <FormField label="Título">\n'
            "            <input className={inputBaseStyles} value={titulo} onChange={(e) => setTitulo(e.target.value)} autoFocus />\n"
            "          </FormField>\n"
            '          <FormField label="Descrição">\n'
            "            <input className={inputBaseStyles} value={descricao} onChange={(e) => setDescricao(e.target.value)} />\n"
            "          </FormField>\n"
            "        </form>\n"
            "      </Modal>\n\n"
            "      <ConfirmDialog\n"
            "        aberto={itemExcluindo !== null}\n"
            f'        titulo="Excluir {label}"\n'
            '        mensagem={`Tem certeza que deseja excluir "${itemExcluindo?.titulo}"? Esta ação não pode ser desfeita.`}\n'
            "        onCancelar={() => setItemExcluindo(null)}\n"
            "        onConfirmar={excluir}\n"
            "      />\n\n"
            "      {toast && (\n"
            '        <div className="fixed top-4 right-4 z-50 rounded-lg bg-slate-900 dark:bg-white text-white dark:text-slate-900 text-sm px-4 py-2.5 shadow-lg">\n'
            "          {toast}\n"
            "        </div>\n"
            "      )}\n"
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
