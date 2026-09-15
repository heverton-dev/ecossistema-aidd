# -*- coding: utf-8 -*-
"""
AIDD-Factory — Swagger Generator Engine.

Gera openapi.json e README.md a partir do gateway gerado.
100% deterministico — zero LLM.
"""
import json
import os
import sys
from typing import Dict, List, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "componentes", "compartilhado", "src-core"))
from core.result import Result

_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "templates", "docs")


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

    env = Environment(loader=FileSystemLoader(_TEMPLATES_DIR))

    # OpenAPI
    try:
        tpl = env.get_template("openapi.json.j2")
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
