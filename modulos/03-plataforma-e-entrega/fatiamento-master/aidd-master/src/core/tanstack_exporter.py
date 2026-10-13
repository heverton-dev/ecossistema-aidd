# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD — TanStack Router Frontend Exporter (Lei Inviolavel #11: Padrao-Ouro de Stack)
=============================================================================
Gera o frontend `frontend/` (React 18 + TanStack Router + Vite + TypeScript +
Tailwind CSS) de qualquer suite AIDD (monolito modular com `src/modules/<nome>/`).
SPA estatica: o build (`dist/`) e servido por nginx; sem servidor Node em producao.
O Next.js foi abolido do ecossistema (agnosticismo de plataforma).

Fonte unica de verdade, copiada byte-identica pelo `components sync` em
`aidd-master/src/core/` e `aidd-enterprise/src/core/` (ver `src-core/MANIFEST.json`).

Design funcional (herdado do gerador anterior, achados reais da validacao E2E):
  - UMA unica env var (`VITE_API_URL`, default vazio = mesma origem).
  - UMA unica camada de acesso a API (`src/lib/api-client.ts`).
  - NAO reimplementa os Studios nativos do backend (`/docs`, `/webhooks`, `/mcp`,
    `/openapi.json`, `/health`, `/metrics`, `/api/*`): continuam no processo Python,
    roteados por prefixo pelo Nginx. Gera so paginas de PRODUTO (dashboard + 1 por modulo).
  - Cor de marca vinda do `DESIGN-SYSTEM.json` do planner (ou derivada do nome do
    projeto), nunca fixa. Neutro slate e semanticas emerald/amber/rose/blue sao convencao.
  - Rotas declaradas em codigo (`src/router.tsx`), sem plugin de geracao: deterministico.
  - Offline-first: inclui as libs do template padrao-ouro (`frontend-tanstack`).
  - Zero dependencias externas no gerador — so stdlib.
"""

import json
import os
import re
import shutil
from typing import Any, Dict, List


def _achar_raiz_repo(inicio: str) -> str:
    """Sobe pastas até achar ecossistema.py (raiz do repo), sem depender da profundidade."""
    curr = os.path.abspath(inicio)
    while os.path.dirname(curr) != curr:
        if os.path.isfile(os.path.join(curr, "ecossistema.py")):
            return curr
        curr = os.path.dirname(curr)
    return os.path.abspath(inicio)

try:
    from design_catalog import escolher_paleta
except ImportError:
    import sys
    _njs_dir = os.path.join(
        _achar_raiz_repo(os.path.dirname(__file__)), "componentes", "compartilhado", "src-core"
    )
    if os.path.isdir(_njs_dir) and _njs_dir not in sys.path:
        sys.path.insert(0, _njs_dir)
    from design_catalog import escolher_paleta



class TanStackRouterExporter:
    """Gera um frontend TanStack Router + Vite (SPA) para uma suite AIDD."""

    # Libs do template padrao-ouro copiadas para o frontend gerado (offline-first).
    _LIBS_OFFLINE = (
        "src/lib/pwa.ts",
        "src/lib/seguranca.ts",
        "src/lib/banco.ts",
        "src/lib/offline/sync-queue.ts",
        "src/hooks/use-mobile.tsx",
    )

    def __init__(self, repo_root: str = None):
        self.repo_root = repo_root or _achar_raiz_repo(os.path.dirname(os.path.abspath(__file__)))

    def export_project(self, project_dir: str, output_dir: str, suite_name: str = "") -> Dict[str, Any]:
        """Gera o frontend em `output_dir` (tipicamente `<projeto>/frontend`).

        Returns:
            dict com `files_created` (list[str]), `modules` (list[str]) e `paleta`.
        """
        project_dir = os.path.abspath(project_dir)
        output_dir = os.path.abspath(output_dir)

        modules = self._discover_modules(project_dir)
        paleta = self._resolver_paleta(project_dir, suite_name or os.path.basename(project_dir), modules)
        result: Dict[str, Any] = {"files_created": [], "modules": modules, "paleta": paleta}

        os.makedirs(output_dir, exist_ok=True)

        created: List[str] = []
        created += self._write(output_dir, "package.json", self._package_json())
        created += self._write(output_dir, "vite.config.ts", self._vite_config())
        created += self._write(output_dir, "tsconfig.json", self._tsconfig())
        created += self._write(output_dir, "tailwind.config.ts", self._tailwind_config(paleta))
        created += self._write(output_dir, "postcss.config.js", self._postcss_config())
        created += self._write(output_dir, "index.html", self._index_html())
        created += self._write(output_dir, ".gitignore", self._gitignore())
        created += self._write(output_dir, ".dockerignore", self._dockerignore())
        created += self._write(output_dir, "Dockerfile", self._dockerfile())
        created += self._write(output_dir, "nginx.conf", self._nginx_conf())
        created += self._write(output_dir, "public/.gitkeep", "")
        created += self._write(output_dir, "src/main.tsx", self._main_tsx())
        created += self._write(output_dir, "src/index.css", self._index_css())
        created += self._write(output_dir, "src/router.tsx", self._router_tsx(modules))
        created += self._write(output_dir, "src/lib/api-client.ts", self._api_client())
        created += self._write(output_dir, "src/components/icons.tsx", self._icons_component())
        created += self._write(output_dir, "src/components/Navbar.tsx", self._navbar_component(modules))
        created += self._write(output_dir, "src/components/shared/Modal.tsx", self._modal_component())
        created += self._write(output_dir, "src/components/shared/ConfirmDialog.tsx", self._confirm_dialog_component())
        created += self._write(output_dir, "src/components/shared/FormField.tsx", self._form_field_component())
        created += self._write(output_dir, "src/routes/index.tsx", self._index_page(modules))
        for mod in modules:
            created += self._write(output_dir, f"src/routes/{mod}.tsx", self._module_page(mod))
        created += self._copiar_libs_offline(output_dir)

        result["files_created"] = created
        return result

    # ------------------------------------------------------------------
    # Config files
    # ------------------------------------------------------------------

    def _package_json(self) -> str:
        package = {
            "name": "aidd-frontend",
            "version": "1.0.0",
            "private": True,
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "tsc --noEmit && vite build",
                "preview": "vite preview",
            },
            "dependencies": {
                "@tanstack/react-router": "^1.81.0",
                "react": "^18.3.1",
                "react-dom": "^18.3.1",
            },
            "devDependencies": {
                "@types/node": "^20.11.0",
                "@types/react": "^18.3.3",
                "@types/react-dom": "^18.3.0",
                "@vitejs/plugin-react": "^4.3.3",
                "autoprefixer": "^10.4.19",
                "postcss": "^8.4.38",
                "tailwindcss": "^3.4.4",
                "typescript": "^5.4.5",
                "vite": "^5.4.10",
            },
        }
        return json.dumps(package, indent=2, ensure_ascii=False) + "\n"

    def _vite_config(self) -> str:
        return (
            "import { defineConfig } from \"vite\";\n"
            "import react from \"@vitejs/plugin-react\";\n"
            "import { fileURLToPath, URL } from \"node:url\";\n\n"
            "export default defineConfig({\n"
            "  plugins: [react()],\n"
            "  resolve: {\n"
            "    alias: { \"@\": fileURLToPath(new URL(\"./src\", import.meta.url)) },\n"
            "  },\n"
            "  server: { port: 3000, host: true },\n"
            "  build: {\n"
            "    outDir: \"dist\",\n"
            "  },\n"
            "});\n"
        )

    def _tsconfig(self) -> str:
        tsconfig = {
            "compilerOptions": {
                "target": "ES2020",
                "lib": ["ES2020", "DOM", "DOM.Iterable"],
                "module": "ESNext",
                "moduleResolution": "bundler",
                "jsx": "react-jsx",
                "strict": True,
                "noEmit": True,
                "skipLibCheck": True,
                "esModuleInterop": True,
                "resolveJsonModule": True,
                "isolatedModules": True,
                "types": ["vite/client"],
                "baseUrl": ".",
                "paths": {"@/*": ["./src/*"]},
            },
            "include": ["src", "vite.config.ts"],
        }
        return json.dumps(tsconfig, indent=2, ensure_ascii=False) + "\n"

    def _tailwind_config(self, paleta: Dict[str, str]) -> str:
        # Cor de marca (Lei #11): vem do DESIGN-SYSTEM.json do projeto (unico por
        # projeto, nunca fixo — ver _resolver_paleta). Neutro estrutural (slate) e
        # semanticas (emerald/amber/rose/blue) sao convencao de UX, nao identidade.
        return (
            "import type { Config } from \"tailwindcss\";\n\n"
            "const config: Config = {\n"
            "  darkMode: \"class\",\n"
            "  content: [\"./index.html\", \"./src/**/*.{ts,tsx}\"],\n"
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
            "export default {\n"
            "  plugins: { tailwindcss: {}, autoprefixer: {} },\n"
            "};\n"
        )

    def _gitignore(self) -> str:
        return (
            "/node_modules\n/dist\n/coverage\n.DS_Store\n*.pem\nnpm-debug.log*\n"
            ".env.local\n.env\n*.tsbuildinfo\n"
        )

    def _dockerignore(self) -> str:
        return "node_modules\ndist\n.git\n.env*\nnpm-debug.log*\n"

    def _dockerfile(self) -> str:
        return (
            "# =========================================================================\n"
            "# AIDD Frontend — TanStack Router (SPA estatica) servido por nginx (Lei #11)\n"
            "# =========================================================================\n\n"
            "FROM node:20-alpine AS builder\n"
            "WORKDIR /app\n"
            "COPY package*.json ./\n"
            "RUN npm install\n"
            "COPY . .\n"
            "ARG VITE_API_URL=\"\"\n"
            "ENV VITE_API_URL=$VITE_API_URL\n"
            "RUN npm run build\n\n"
            "FROM nginx:1.27-alpine AS runner\n"
            "COPY nginx.conf /etc/nginx/conf.d/default.conf\n"
            "COPY --from=builder /app/dist /usr/share/nginx/html\n\n"
            "EXPOSE 3000\n\n"
            "HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \\\n"
            "    CMD wget -q -O /dev/null http://127.0.0.1:3000/ || exit 1\n"
        )

    def _nginx_conf(self) -> str:
        return (
            "server {\n"
            "    listen 3000;\n"
            "    server_name _;\n"
            "    root /usr/share/nginx/html;\n"
            "    index index.html;\n\n"
            "    location /assets/ {\n"
            "        expires 1y;\n"
            "        add_header Cache-Control \"public, immutable\";\n"
            "    }\n\n"
            "    location / {\n"
            "        try_files $uri /index.html;\n"
            "    }\n"
            "}\n"
        )

    def _index_html(self) -> str:
        # Script anti-flash: aplica a classe "dark" no <html> ANTES de montar o
        # React (localStorage + matchMedia), evitando o "flash" de tema claro.
        return (
            "<!doctype html>\n"
            "<html lang=\"pt-BR\">\n"
            "  <head>\n"
            "    <meta charset=\"UTF-8\" />\n"
            "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />\n"
            "    <title>AIDD</title>\n"
            "    <script>\n"
            "      (function () {\n"
            "        try {\n"
            "          var stored = localStorage.getItem('theme');\n"
            "          var dark = stored ? stored === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches;\n"
            "          document.documentElement.classList.toggle('dark', dark);\n"
            "        } catch (e) {}\n"
            "      })();\n"
            "    </script>\n"
            "  </head>\n"
            "  <body class=\"bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 font-sans selection:bg-primary selection:text-primary-foreground\">\n"
            "    <div id=\"root\"></div>\n"
            "    <script type=\"module\" src=\"/src/main.tsx\"></script>\n"
            "  </body>\n"
            "</html>\n"
        )

    def _index_css(self) -> str:
        # Sem CSS customizado alem das 3 diretivas: todo estilo via classes Tailwind.
        return "@tailwind base;\n@tailwind components;\n@tailwind utilities;\n"

    def _main_tsx(self) -> str:
        return (
            "import React from \"react\";\n"
            "import ReactDOM from \"react-dom/client\";\n"
            "import { RouterProvider } from \"@tanstack/react-router\";\n"
            "import { router } from \"./router\";\n"
            "import \"./index.css\";\n\n"
            "ReactDOM.createRoot(document.getElementById(\"root\") as HTMLElement).render(\n"
            "  <React.StrictMode>\n"
            "    <RouterProvider router={router} />\n"
            "  </React.StrictMode>,\n"
            ");\n"
        )

    def _router_tsx(self, modules: List[str]) -> str:
        def ident(mod: str) -> str:
            return re.sub(r"\W", "_", mod)

        imports = "\n".join(
            f'import {{ {self._to_pascal_case(mod)}Page }} from "@/routes/{mod}";' for mod in modules
        )
        rotas = "\n".join(
            f"const {ident(mod)}Route = createRoute({{\n"
            f"  getParentRoute: () => rootRoute,\n"
            f'  path: "/{mod}",\n'
            f"  component: {self._to_pascal_case(mod)}Page,\n"
            f"}});\n"
            for mod in modules
        )
        filhas = ", ".join(["indexRoute"] + [f"{ident(mod)}Route" for mod in modules])
        return (
            "import { createRootRoute, createRoute, createRouter, Outlet } from \"@tanstack/react-router\";\n"
            "import { Navbar } from \"@/components/Navbar\";\n"
            "import { HomePage } from \"@/routes/index\";\n"
            f"{imports}\n\n"
            "const rootRoute = createRootRoute({\n"
            "  component: () => (\n"
            "    <>\n"
            "      <Navbar />\n"
            "      <Outlet />\n"
            "    </>\n"
            "  ),\n"
            "});\n\n"
            "const indexRoute = createRoute({\n"
            "  getParentRoute: () => rootRoute,\n"
            "  path: \"/\",\n"
            "  component: HomePage,\n"
            "});\n\n"
            f"{rotas}\n"
            f"const routeTree = rootRoute.addChildren([{filhas}]);\n\n"
            "export const router = createRouter({ routeTree });\n\n"
            "declare module \"@tanstack/react-router\" {\n"
            "  interface Register {\n"
            "    router: typeof router;\n"
            "  }\n"
            "}\n"
        )

    # ------------------------------------------------------------------
    # Cliente de API — fonte unica, sem duplicacao de camada
    # ------------------------------------------------------------------

    def _api_client(self) -> str:
        return (
            "// Cliente de API unico do frontend AIDD (Lei #11).\n"
            "// Fetch direto do browser para o backend Python. VITE_API_URL vazia\n"
            "// (default) significa mesma origem — funciona atras do Nginx, que roteia\n"
            "// /api, /docs, /webhooks, /mcp, /openapi.json, /health, /metrics para o\n"
            "// backend e o resto para este frontend.\n"
            "const API_BASE: string = import.meta.env.VITE_API_URL || \"\";\n\n"
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
    # Componentes/paginas especificos do roteador
    # ------------------------------------------------------------------

    def _navbar_component(self, modules: List[str]) -> str:
        module_links = "\n".join(
            f'        <Link to="/{mod}" className={{navLinkClass(pathname === "/{mod}")}}>{self._label(mod)}</Link>'
            for mod in modules
        )
        return (
            'import { Link, useRouterState } from "@tanstack/react-router";\n'
            'import { useEffect, useState } from "react";\n'
            'import { SunIcon, MoonIcon } from "@/components/icons";\n\n'
            "function navLinkClass(active: boolean): string {\n"
            "  return active\n"
            "    ? \"px-3 py-1.5 rounded-md text-sm font-semibold bg-slate-100 dark:bg-slate-800 text-primary\"\n"
            "    : \"px-3 py-1.5 rounded-md text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/60\";\n"
            "}\n\n"
            "// Links para /docs, /docs/guia, /webhooks, /mcp e /metrics usam <a> (nao\n"
            "// <Link>): sao rotas nativas do backend Python, roteadas pelo Nginx para\n"
            "// outro servico — nao existem no roteador do frontend.\n"
            "export function Navbar() {\n"
            "  const pathname = useRouterState({ select: (s) => s.location.pathname });\n"
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
            "        <Link to=\"/\" className=\"flex items-center gap-2 mr-4\">\n"
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

    def _index_page(self, modules: List[str]) -> str:
        cards = "\n".join(
            f'        <Link to="/{mod}" className="group rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm hover:shadow-md transition">\n'
            f'          <div className="w-10 h-10 rounded-lg bg-primary/10 text-primary flex items-center justify-center font-bold mb-3">{self._label(mod)[:1]}</div>\n'
            f'          <h2 className="text-base font-semibold text-slate-900 dark:text-white group-hover:text-primary">{self._label(mod)}</h2>\n'
            f'          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Gerenciar registros de {self._label(mod).lower()}</p>\n'
            f'        </Link>'
            for mod in modules
        )
        return (
            "import { Link } from \"@tanstack/react-router\";\n\n"
            "export function HomePage() {\n"
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

    def _copiar_libs_offline(self, output_dir: str) -> List[str]:
        """Copia as libs offline-first do template padrao-ouro para o frontend gerado."""
        # No repositorio: componentes/compartilhado/templates/frontend-tanstack. Em um projeto
        # gerado (sem o repositorio): templates/frontend-tanstack ao lado de scripts/.
        candidatos = [
            os.path.join(self.repo_root, "componentes", "compartilhado", "templates", "frontend-tanstack"),
            os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates", "frontend-tanstack")),
        ]
        base = next((c for c in candidatos if os.path.isdir(c)), None)
        if base is None:
            raise FileNotFoundError("Template canonico TanStack nao encontrado em: " + " | ".join(candidatos))
        criados: List[str] = []
        for rel in self._LIBS_OFFLINE:
            origem = os.path.join(base, *rel.split("/"))
            if not os.path.isfile(origem):
                raise FileNotFoundError(f"Lib offline ausente no template: {rel}")
            with open(origem, "r", encoding="utf-8") as f:
                criados += self._write(output_dir, rel, f.read())
        return criados

    # ------------------------------------------------------------------
    # Componentes React neutros (reaproveitados do gerador anterior)
    # ------------------------------------------------------------------

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

    def _modal_component(self) -> str:
        return (
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

    def _module_page(self, module_name: str) -> str:
        label = self._label(module_name)
        pascal = self._to_pascal_case(module_name)
        return (
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
            f"export function {pascal}Page() {{\n"
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
