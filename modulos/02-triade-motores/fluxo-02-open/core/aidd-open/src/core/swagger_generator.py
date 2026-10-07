# -*- coding: utf-8 -*-
"""
AIDD-Open — Swagger Generator Engine.

Gera openapi.json e README.md a partir do gateway gerado.
100% deterministico — zero LLM.
"""
import json
import os
import sys
from typing import Dict, List, Any


def _achar_raiz_repo(inicio: str) -> str:
    """Sobe pastas até achar ecossistema.py (raiz do repo), sem depender da profundidade."""
    curr = os.path.abspath(inicio)
    while os.path.dirname(curr) != curr:
        if os.path.isfile(os.path.join(curr, "ecossistema.py")):
            return curr
        curr = os.path.dirname(curr)
    return os.path.abspath(inicio)

sys.path.insert(0, os.path.join(_achar_raiz_repo(os.path.dirname(__file__)), "componentes", "compartilhado", "src-core"))
from core.result import Result



def _montar_contexto(analysis: dict) -> dict:
    """Monta contexto para templates de docs."""
    nicho_slug = analysis["nicho_slug"]
    nicho_nome = analysis["nicho_nome_exibicao"]
    ferramentas = analysis.get("ferramentas", [])

    servicos = []
    for f in ferramentas:
        nome_slug = f["nome"].lower().replace(" ", "-").replace(".", "")
        servicos.append({
            "nome": f["nome"],
            "nome_slug": nome_slug,
            "descricao": f"Servico {f['nome']}",
        })

    return {
        "nicho_slug": nicho_slug,
        "nicho_nome_exibicao": nicho_nome,
        "servicos": servicos,
    }


def gerar_swagger(analysis: dict, pasta_saida: str) -> Result:
    """Gera openapi.json e README.md."""
    contexto = _montar_contexto(analysis)
    arquivos = []

    # openapi.json
    try:
        from jinja2 import Environment, FileSystemLoader
    except ImportError:
        return Result.fail("Jinja2 nao instalado", codigo="JINJA2_AUSENTE")

    # openapi.json.j2 vem do almoxarifado (Bloco 4: a cópia em templates/docs saiu);
    # README.md.j2 é só do aidd-open e continua em templates/docs.
    from core.vsa_generator import obter_molde_vsa
    molde_openapi = obter_molde_vsa("openapi.json.j2")
    docs_locais = os.path.join(os.path.dirname(__file__), "..", "..", "templates", "docs")
    env = Environment(loader=FileSystemLoader([os.path.dirname(molde_openapi), docs_locais]))

    # OpenAPI
    try:
        tpl = env.get_template(os.path.basename(molde_openapi))
        conteudo = tpl.render(**contexto)
        # Validar JSON
        dados = json.loads(conteudo)
        if dados.get("openapi") != "3.1.0":
            return Result.fail("Spec nao e OpenAPI 3.1.0", codigo="OPENAPI_INVALID")

        out_path = os.path.join(pasta_saida, "openapi.json")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(dados, indent=2))
        arquivos.append(out_path)
    except json.JSONDecodeError as exc:
        return Result.fail(f"openapi.json invalido: {exc}", codigo="OPENAPI_JSON_ERROR")
    except Exception as exc:
        return Result.fail(f"Erro ao gerar openapi.json: {exc}", codigo="OPENAPI_ERROR")

    # README.md
    try:
        tpl = env.get_template("README.md.j2")
        conteudo = tpl.render(**contexto)
        out_path = os.path.join(pasta_saida, "README.md")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(conteudo)
        arquivos.append(out_path)
    except Exception as exc:
        return Result.fail(f"Erro ao gerar README.md: {exc}", codigo="README_ERROR")

    return Result.ok(arquivos)
