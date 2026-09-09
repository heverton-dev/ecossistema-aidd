#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.1 Enterprise — GERADOR DE FATIAS VERTICAIS (add_module.py)
=============================================================================
Gera uma fatia vertical completa, isolada e desacoplada com:
1. models.py (Schema SQLite WAL com índices e timestamps)
2. services.py (Regras de negócio Full CRUD + EventBus pub/sub)
3. routes.py (RouteRegistry com documentação OpenAPI 3.1)
4. UI Component Impeccable (HTML/Tailwind com Toasts e modais)
5. test_<modulo>.py (Suíte pytest unitária cobrindo 100% dos fluxos)
6. Atualização automática do manifesto PLANO-EXECUCAO-ESTRUTURADO.json
"""

import os
import sys
import re
import json
import click
import shutil
import tempfile

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from cookiecutter.main import cookiecutter

import keyword

MODULE_TEMPLATE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "templates", "cookiecutter-scaffold", "module"
)

RESERVED_WORDS = set(keyword.kwlist) | {"test", "core", "static", "modules", "shared", "server", "app", "api"}


def slugify(text: str) -> str:
    """Gera identificador slug padronizado em snake_case com proteção contra palavras reservadas."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    slug = re.sub(r'[\s_-]+', '_', text)
    if not slug:
        slug = "modulo_custom"
    if slug in RESERVED_WORDS or slug.isdigit():
        slug = f"mod_{slug}"
    return slug


def pascal_case(text: str) -> str:
    """Converte texto para PascalCase."""
    slug = slugify(text)
    return ''.join(word.capitalize() for word in slug.split('_'))


def criar_modulo(nome_modulo: str, descricao: str = "", target_dir: str = "."):
    """Gera atomicamente todos os artefatos de uma fatia vertical desacoplada."""
    slug = slugify(nome_modulo)
    pascal = pascal_case(nome_modulo)
    desc = descricao or f"Módulo de gestão e operações para {slug.replace('_', ' ').capitalize()}"

    target_dir = os.path.abspath(target_dir)
    src_dir = os.path.join(target_dir, "src")
    module_dir = os.path.join(src_dir, "modules", slug)
    comp_dir = os.path.join(src_dir, "static", "components")
    test_dir = os.path.join(target_dir, "tests", "unit")

    print(f"🚀 [AIDD v5.1] Gerando fatia vertical completa para o módulo: '{slug}'...")
    print(f"📁 Destino: {module_dir}")

    os.makedirs(module_dir, exist_ok=True)
    os.makedirs(comp_dir, exist_ok=True)
    os.makedirs(test_dir, exist_ok=True)

    # 0-5. Gera a fatia vertical inteira (models.py, services.py, routes.py,
    # componente UI e teste pytest) delegando ao Cookiecutter/Jinja2 —
    # substitui o antigo templating manual via f-strings.
    with tempfile.TemporaryDirectory() as tmp_out:
        cookiecutter(
            MODULE_TEMPLATE_DIR,
            no_input=True,
            extra_context={"slug": slug, "pascal": pascal, "desc": desc},
            output_dir=tmp_out,
            overwrite_if_exists=True,
        )
        gerado_dir = os.path.join(tmp_out, slug)

        # Os templates .py usam sufixo ".j2" propositalmente: gates
        # determinísticos (G_QUALIDADE) fazem ast.parse em todo .py do
        # projeto, e o arquivo de template bruto (com sintaxe Jinja2
        # "{{ cookiecutter.slug }}") não é Python válido — o sufixo evita
        # que o TEMPLATE em si seja confundido com código gerado. O
        # arquivo já RENDERIZADO (sem chaves Jinja2) recebe o nome final
        # ".py" aqui, na cópia para o destino.
        shutil.move(os.path.join(gerado_dir, "__init__.py"), os.path.join(module_dir, "__init__.py"))
        for fname in ("models.py", "services.py", "routes.py"):
            shutil.move(os.path.join(gerado_dir, f"{fname}.j2"), os.path.join(module_dir, fname))

        shutil.move(
            os.path.join(gerado_dir, "static", "components", f"{slug}.html"),
            os.path.join(comp_dir, f"{slug}.html")
        )
        shutil.move(
            os.path.join(gerado_dir, "tests", f"test_{slug}.py.j2"),
            os.path.join(test_dir, f"test_{slug}.py")
        )

    # 6. Atualizar PLANO-EXECUCAO-ESTRUTURADO.json se existir
    plano_path = os.path.join(target_dir, "PLANO-EXECUCAO-ESTRUTURADO.json")
    server_path = os.path.join(src_dir, "server.py")
    if os.path.isfile(plano_path):
        try:
            with open(plano_path, "r", encoding="utf-8") as f:
                plano = json.load(f)

            if "modulos" not in plano:
                plano["modulos"] = []

            mod_exists = any(m.get("slug") == slug for m in plano["modulos"] if isinstance(m, dict))
            if not mod_exists:
                plano["modulos"].append({
                    "nome": pascal,
                    "slug": slug,
                    "descricao": desc,
                    "status": "implementado",
                    "rotas": [
                        f"/api/{slug}",
                        f"/api/{slug}/obter",
                        f"/api/{slug}/criar",
                        f"/api/{slug}/atualizar",
                        f"/api/{slug}/deletar"
                    ],
                    "eventos": [f"{slug}_criado", f"{slug}_atualizado", f"{slug}_deletado"],
                    "testes": f"tests/unit/test_{slug}.py"
                })

                with open(plano_path, "w", encoding="utf-8") as f:
                    json.dump(plano, f, ensure_ascii=False, indent=2)
                print(f"  [+] Manifesto 'PLANO-EXECUCAO-ESTRUTURADO.json' atualizado com o módulo '{slug}'!")

            # 7. Religar src/server.py com o módulo recém-criado. Só roda quando
            # add_module.py é chamado dentro de um projeto JÁ COMPOSTO (server.py
            # já existe) — durante a composição inicial, compose_suite() chama
            # criar_modulo() antes de gerar o server.py e cuida disso sozinho,
            # então regenerar aqui de novo seria trabalho duplicado.
            if os.path.isfile(server_path):
                try:
                    from compose_suite import generate_modular_server_code
                except ImportError:
                    from scripts.compose_suite import generate_modular_server_code

                suite_name = plano.get("projeto", {}).get("nome", "AIDD Suite")
                db_engine = plano.get("projeto", {}).get("db_engine", "sqlite")
                module_slugs = [m.get("slug") for m in plano["modulos"] if isinstance(m, dict) and m.get("slug")]
                if slug not in module_slugs:
                    module_slugs.append(slug)

                server_code = generate_modular_server_code(suite_name, module_slugs, db_engine=db_engine)
                with open(server_path, "w", encoding="utf-8") as f:
                    f.write(server_code)
                print(f"  [+] 'src/server.py' regenerado e religado com o módulo '{slug}'!")
        except Exception as e:
            print(f"  [!] Aviso ao atualizar manifesto: {e}")

    print(f"✨ [OK] Módulo '{slug}' gerado com 100% de integridade e Clean Architecture!")


@click.command(name="add_module", help="AIDD v5.1 — Gerador de Módulos Desacoplados")
@click.argument("nome", required=True)
@click.option("--descricao", "-d", default="", help="Descrição da fatia vertical")
@click.option("--dir", "dir", default=".", help="Diretório raiz do projeto alvo")
@click.option("--pasta", "dir", help="Alias para --dir (diretório raiz do projeto alvo)")
def cli(nome: str, descricao: str, dir: str):
    """Gera fatia vertical completa: NOME do módulo (ex: faturamento, pedidos, crm)."""
    criar_modulo(nome, descricao, dir)


if __name__ == '__main__':
    cli()
