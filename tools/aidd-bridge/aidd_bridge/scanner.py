# -*- coding: utf-8 -*-
"""
Scanner determinístico de projetos Lovable / Vite / React / Supabase.
Inspeciona a estrutura de arquivos, extrai rotas (React Router e TanStack Router),
páginas, dependências, tokens de design e migrações de banco de dados.
"""

import os
import json
import re
from typing import Dict, List, Any

class LovableScanner:
    def __init__(self, project_dir: str):
        self.project_dir = os.path.abspath(project_dir)

    def is_valid_project(self) -> bool:
        pkg_path = os.path.join(self.project_dir, "package.json")
        return os.path.exists(pkg_path)

    def scan(self) -> Dict[str, Any]:
        if not self.is_valid_project():
            raise FileNotFoundError(f"package.json nao encontrado em: {self.project_dir}")

        manifest = {
            "project_dir": self.project_dir,
            "package_info": self._scan_package_json(),
            "pages": self._scan_pages(),
            "routes": self._scan_routes(),
            "components": self._scan_components(),
            "styles": self._scan_styles(),
            "database": self._scan_database(),
            "env_vars": self._scan_env_vars(),
            "edge_functions": self._scan_edge_functions()
        }
        return manifest

    def _scan_edge_functions(self) -> List[str]:
        """
        Lista as Supabase Edge Functions reais do projeto (pastas com
        index.ts dentro de supabase/functions/), ignorando "main" e
        "_shared" — "main" é o roteador que o próprio aidd-bridge gera,
        "_shared" é convenção de código compartilhado entre funções, não
        uma função em si.
        """
        functions_dir = os.path.join(self.project_dir, "supabase", "functions")
        functions = []
        if os.path.exists(functions_dir):
            for name in sorted(os.listdir(functions_dir)):
                if name in ("main", "_shared") or name.startswith("."):
                    continue
                full = os.path.join(functions_dir, name)
                if os.path.isdir(full) and os.path.exists(os.path.join(full, "index.ts")):
                    functions.append(name)
        return functions

    def _scan_package_json(self) -> Dict[str, Any]:
        pkg_path = os.path.join(self.project_dir, "package.json")
        try:
            with open(pkg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {
                    "name": data.get("name", "unknown"),
                    "version": data.get("version", "0.0.0"),
                    "dependencies": data.get("dependencies", {}),
                    "devDependencies": data.get("devDependencies", {}),
                    "scripts": data.get("scripts", {})
                }
        except Exception as e:
            return {"error": str(e)}

    def _scan_pages(self) -> List[str]:
        pages = []
        for candidate_dir in ["src/pages", "src/routes"]:
            full_dir = os.path.join(self.project_dir, candidate_dir)
            if os.path.exists(full_dir):
                for root, _, files in os.walk(full_dir):
                    for file in files:
                        if file.endswith((".tsx", ".jsx", ".js", ".ts")) and not file.startswith("__"):
                            rel = os.path.relpath(os.path.join(root, file), self.project_dir)
                            pages.append(rel.replace("\\", "/"))
        return sorted(pages)

    def _scan_routes(self) -> List[Dict[str, str]]:
        routes = []

        # 1. TanStack Router (File-based Routing em src/routes)
        routes_dir = os.path.join(self.project_dir, "src", "routes")
        if os.path.exists(routes_dir):
            for root, _, files in os.walk(routes_dir):
                for file in sorted(files):
                    if file.endswith((".tsx", ".jsx")) and not file.startswith("__"):
                        rel_to_routes = os.path.relpath(os.path.join(root, file), routes_dir).replace("\\", "/")
                        # Converte nome de arquivo TanStack em caminho de rota
                        clean_name = rel_to_routes.replace(".tsx", "").replace(".jsx", "")
                        if clean_name == "index":
                            path = "/"
                        else:
                            parts = clean_name.split("/")
                            formatted_parts = []
                            for p in parts:
                                if p == "index":
                                    continue
                                if p.startswith("$"):
                                    formatted_parts.append(f":{p[1:]}")
                                else:
                                    formatted_parts.append(p)
                            path = "/" + "/".join(formatted_parts)
                        routes.append({
                            "path": path,
                            "component": file,
                            "source_file": rel_to_routes,
                            "type": "tanstack-file-route"
                        })
            if routes:
                return routes

        # 2. React Router DOM clássico em App.tsx / main.tsx
        app_candidates = [
            os.path.join(self.project_dir, "src", "App.tsx"),
            os.path.join(self.project_dir, "src", "App.jsx"),
            os.path.join(self.project_dir, "src", "main.tsx")
        ]
        route_pattern = re.compile(r'<Route\s+[^>]*path=["\']([^"\']+)["\'][^>]*element=\{<([^/>\s]+)', re.MULTILINE)

        for candidate in app_candidates:
            if os.path.exists(candidate):
                with open(candidate, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    matches = route_pattern.findall(content)
                    for path, component in matches:
                        routes.append({
                            "path": path,
                            "component": component,
                            "source_file": os.path.basename(candidate),
                            "type": "react-router"
                        })
                if routes:
                    break
        return routes

    def _scan_components(self) -> Dict[str, List[str]]:
        comp_dir = os.path.join(self.project_dir, "src", "components")
        components = {"ui": [], "custom": []}
        if os.path.exists(comp_dir):
            for root, _, files in os.walk(comp_dir):
                for file in files:
                    if file.endswith((".tsx", ".jsx")):
                        rel = os.path.relpath(os.path.join(root, file), comp_dir).replace("\\", "/")
                        if rel.startswith("ui/"):
                            components["ui"].append(rel)
                        else:
                            components["custom"].append(rel)
        return components

    def _scan_styles(self) -> Dict[str, Any]:
        styles = {
            "has_tailwind": False,
            "tailwind_config": None,
            "global_css": None,
            "color_tokens": []
        }
        for cfg in ["tailwind.config.ts", "tailwind.config.js"]:
            p = os.path.join(self.project_dir, cfg)
            if os.path.exists(p):
                styles["has_tailwind"] = True
                styles["tailwind_config"] = cfg
                break

        for css in ["src/styles.css", "src/index.css", "src/App.css", "src/globals.css"]:
            p = os.path.join(self.project_dir, css)
            if os.path.exists(p):
                styles["global_css"] = css
                try:
                    with open(p, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        tokens = re.findall(r'--([a-zA-Z0-9_-]+):\s*([^;]+);', content)
                        styles["color_tokens"] = [{"token": f"--{t[0]}", "value": t[1].strip()} for t in tokens[:30]]
                except Exception:
                    pass
                break
        return styles

    def _scan_database(self) -> Dict[str, Any]:
        db_info = {"has_supabase": False, "migrations": []}
        migrations_dir = os.path.join(self.project_dir, "supabase", "migrations")
        if os.path.exists(migrations_dir):
            db_info["has_supabase"] = True
            for file in sorted(os.listdir(migrations_dir)):
                if file.endswith(".sql"):
                    full_p = os.path.join(migrations_dir, file)
                    db_info["migrations"].append({
                        "filename": file,
                        "size_bytes": os.path.getsize(full_p),
                        "path": full_p.replace("\\", "/")
                    })
        return db_info

    def _scan_env_vars(self) -> List[str]:
        env_vars = set()
        for env_file in [".env", ".env.example", ".env.local"]:
            p = os.path.join(self.project_dir, env_file)
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            var_name = line.split("=")[0].strip()
                            env_vars.add(var_name)

        src_dir = os.path.join(self.project_dir, "src")
        if os.path.exists(src_dir):
            for root, _, files in os.walk(src_dir):
                for file in files:
                    if file.endswith((".ts", ".tsx", ".js", ".jsx")):
                        fp = os.path.join(root, file)
                        try:
                            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                                matches = re.findall(r'import\.meta\.env\.(VITE_[A-Z0-9_]+)', f.read())
                                for m in matches:
                                    env_vars.add(m)
                        except Exception:
                            pass

        return sorted(list(env_vars))