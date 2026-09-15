# -*- coding: utf-8 -*-
"""
AIDD-Factory — Frontend Generator Engine.

Gera scaffold Next.js + Tailwind + shadcn/ui whitelabel.
"""
import os
import sys
from typing import Dict, List, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "componentes", "compartilhado", "src-core"))
from core.result import Result

_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "templates", "frontend")


def _montar_contexto(analysis: dict) -> dict:
    """Monta contexto para renderizacao dos templates."""
    nicho_slug = analysis["nicho_slug"]
    nicho_nome = analysis["nicho_nome_exibicao"]
    ferramentas = analysis.get("ferramentas", [])

    servicos = []
    for f in ferramentas:
        nome_slug = f["nome"].lower().replace(" ", "-").replace(".", "")
        servicos.append({
            "nome": f["nome"],
            "nome_slug": nome_slug,
            "descricao": f"Modulo {f['nome']}",
            "icone": "layers",
        })

    return {
        "nicho_slug": nicho_slug,
        "nicho_nome_exibicao": nicho_nome,
        "servicos": servicos,
    }


def _renderizar_template(nome_template: str, contexto: dict) -> Result:
    """Renderiza um template Jinja2."""
    try:
        from jinja2 import Environment, FileSystemLoader
    except ImportError:
        return Result.fail("Jinja2 nao instalado", codigo="JINJA2_AUSENTE")

    if not os.path.isfile(os.path.join(_TEMPLATES_DIR, nome_template)):
        return Result.fail(f"Template ausente: {nome_template}", codigo="TEMPLATE_AUSENTE")

    env = Environment(loader=FileSystemLoader(_TEMPLATES_DIR))
    try:
        template = env.get_template(nome_template)
        return Result.ok(template.render(**contexto))
    except Exception as exc:
        return Result.fail(f"Erro ao renderizar {nome_template}: {exc}", codigo="TEMPLATE_RENDER_ERROR")


def gerar_frontend(analysis: dict, pasta_saida: str) -> Result:
    """Gera o frontend Next.js whitelabel."""
    contexto = _montar_contexto(analysis)
    arquivos_gerados = []

    templates = [
        ("next.config.js.j2", "next.config.js"),
        ("layout.tsx.j2", "app/layout.tsx"),
        ("page.tsx.j2", "app/page.tsx"),
        ("tenant.config.json.j2", "tenant.config.json"),
    ]

    # package.json basico
    nicho_slug = analysis["nicho_slug"]
    package_json = {
        "name": f"aidd-{nicho_slug}-frontend",
        "version": "1.0.0",
        "private": True,
        "scripts": {
            "dev": "next dev",
            "build": "next build",
            "start": "next start",
        },
        "dependencies": {
            "next": "^14.0.0",
            "react": "^18.0.0",
            "react-dom": "^18.0.0",
        },
        "devDependencies": {
            "tailwindcss": "^3.0.0",
            "postcss": "^8.0.0",
            "autoprefixer": "^10.0.0",
            "@types/node": "^20.0.0",
            "@types/react": "^18.0.0",
            "typescript": "^5.0.0",
        },
    }

    import json
    out_dir = os.path.join(pasta_saida, "frontend")
    os.makedirs(out_dir, exist_ok=True)
    pkg_path = os.path.join(out_dir, "package.json")
    with open(pkg_path, "w", encoding="utf-8") as f:
        json.dump(package_json, f, indent=2)
    arquivos_gerados.append(pkg_path)

    # tsconfig.json basico
    tsconfig = {
        "compilerOptions": {
            "target": "es5",
            "lib": ["dom", "dom.iterable", "esnext"],
            "allowJs": True,
            "skipLibCheck": True,
            "strict": True,
            "forceConsistentCasingInFileNames": True,
            "noEmit": True,
            "esModuleInterop": True,
            "module": "esnext",
            "moduleResolution": "bundler",
            "resolveJsonModule": True,
            "isolatedModules": True,
            "jsx": "preserve",
            "incremental": True,
            "plugins": [{"name": "next"}],
            "paths": {"@/*": ["./src/*"]},
        },
        "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
        "exclude": ["node_modules"],
    }
    ts_path = os.path.join(out_dir, "tsconfig.json")
    with open(ts_path, "w", encoding="utf-8") as f:
        json.dump(tsconfig, f, indent=2)
    arquivos_gerados.append(ts_path)

    # tailwind.config.js basico
    tailwind_config = """/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,ts,jsx,tsx}"],
  theme: { extend: {} },
  plugins: [],
};
"""
    tw_path = os.path.join(out_dir, "tailwind.config.js")
    with open(tw_path, "w", encoding="utf-8") as f:
        f.write(tailwind_config)
    arquivos_gerados.append(tw_path)

    # Renderizar templates Jinja2
    for tpl_nome, out_rel in templates:
        res = _renderizar_template(tpl_nome, contexto)
        if not res.sucesso:
            return res
        out_path = os.path.join(out_dir, out_rel)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(res.valor)
        arquivos_gerados.append(out_path)

    # globals.css
    globals_css = """@tailwind base;
@tailwind components;
@tailwind utilities;
"""
    css_path = os.path.join(out_dir, "app", "globals.css")
    os.makedirs(os.path.dirname(css_path), exist_ok=True)
    with open(css_path, "w", encoding="utf-8") as f:
        f.write(globals_css)
    arquivos_gerados.append(css_path)

    return Result.ok(arquivos_gerados)
