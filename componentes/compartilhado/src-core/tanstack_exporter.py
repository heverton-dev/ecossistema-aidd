# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD — TanStack Router Frontend Exporter (Lei Inviolável #11: Padrão-Ouro)
=============================================================================
Gera o frontend `frontend/` em TanStack Start / Router + React + TypeScript +
Tailwind CSS para conformidade estrita com a Lei Inviolável #11 e AGENTS.md.
Abolição formal e definitiva do Next.js.
"""

import json
import os
import shutil
from typing import Any, Dict, List


def _achar_raiz_repo(inicio: str) -> str:
    """Sobe pastas até achar ecossistema.py (raiz do repo)."""
    curr = os.path.abspath(inicio)
    while os.path.dirname(curr) != curr:
        if os.path.isfile(os.path.join(curr, "ecossistema.py")):
            return curr
        curr = os.path.dirname(curr)
    return os.path.abspath(inicio)


class TanStackRouterExporter:
    """Gera um frontend TanStack Router + React + TS + Tailwind para suites AIDD."""

    def __init__(self, repo_root: str = None):
        self.repo_root = repo_root or _achar_raiz_repo(os.path.dirname(__file__))

    def export_project(self, project_dir: str, output_dir: str, suite_name: str = "") -> Dict[str, Any]:
        """Exporta o template padrão ouro do TanStack Router para o diretório de destino."""
        os.makedirs(output_dir, exist_ok=True)
        template_dir = os.path.join(
            self.repo_root, "componentes", "compartilhado", "templates", "frontend-tanstack"
        )
        if not os.path.isdir(template_dir):
            template_dir = os.path.join(
                self.repo_root, "modulos", "03-plataforma-e-entrega", "fatiamento-master",
                "aidd-master", "templates", "v2", "frontend"
            )

        if not os.path.isdir(template_dir):
            raise FileNotFoundError(f"Template canônico TanStack não encontrado em {template_dir}")

        def _ignorar_build(dir_src, names):
            return {"node_modules", ".git", "__pycache__", ".turbo"}.intersection(names)

        shutil.copytree(template_dir, output_dir, dirs_exist_ok=True, ignore=_ignorar_build)

        # Customizar package.json com o nome da suite se fornecido
        pkg_path = os.path.join(output_dir, "package.json")
        arquivos_criados = []
        for root, _, files in os.walk(output_dir):
            for f in files:
                arquivos_criados.append(os.path.join(root, f))

        if os.path.isfile(pkg_path) and suite_name:
            try:
                with open(pkg_path, "r", encoding="utf-8") as f:
                    pkg_data = json.load(f)
                slug = suite_name.lower().replace(" ", "-").replace("_", "-")
                pkg_data["name"] = f"app-{slug}"
                with open(pkg_path, "w", encoding="utf-8") as f:
                    json.dump(pkg_data, f, indent=2, ensure_ascii=False)
            except Exception:
                pass

        return {
            "status": "sucesso",
            "framework": "tanstack_router",
            "files_created": arquivos_criados,
            "output_dir": output_dir,
        }
