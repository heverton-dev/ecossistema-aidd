# -*- coding: utf-8 -*-
"""
AIDD-Factory — Gateway Generator Engine.

Monta o prompt estruturado para LLM gerar o gateway FastAPI,
renderiza templates Jinja2, e valida o output.
"""
import os
import sys
from typing import Dict, List, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "componentes", "compartilhado", "src-core"))
from core.result import Result

_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "templates", "gateway")


def _montar_contexto(analysis: dict) -> dict:
    """Monta contexto para renderizacao dos templates."""
    nicho_slug = analysis["nicho_slug"]
    nicho_nome = analysis["nicho_nome_exibicao"]
    ferramentas = analysis.get("ferramentas", [])

    import re
    servicos = []
    for f in ferramentas:
        nome_slug = f["nome"].lower().replace(" ", "-").replace(".", "")
        nome_ident = re.sub(r'[^a-zA-Z0-9_]', '_', f["nome"].lower()).strip('_')
        if not nome_ident or nome_ident[0].isdigit():
            nome_ident = f"svc_{nome_ident}"
        nome_camel = "".join(w.capitalize() for w in re.split(r'[\s\-_.]+', f["nome"]) if w)
        servicos.append({
            "nome": f["nome"],
            "nome_slug": nome_slug,
            "nome_ident": nome_ident,
            "nome_camel": nome_camel,
            "url_default": f"http://{nome_slug}:8000",
            "porta": 8000,
            "descricao": f"Servico {f['nome']}",
            "icone": "layers",
        })

    return {
        "nicho_slug": nicho_slug,
        "nicho_nome_exibicao": nicho_nome,
        "servicos": servicos,
    }


def _renderizar_template(nome_template: str, contexto: dict) -> Result:
    """Renderiza um template Jinja2 com o contexto."""
    try:
        from jinja2 import Environment, FileSystemLoader
    except ImportError:
        return Result.fail("Jinja2 nao instalado. pip install jinja2", codigo="JINJA2_AUSENTE")

    caminho = os.path.join(_TEMPLATES_DIR, nome_template)
    if not os.path.isfile(caminho):
        return Result.fail(f"Template nao encontrado: {nome_template}", codigo="TEMPLATE_AUSENTE")

    env = Environment(loader=FileSystemLoader(_TEMPLATES_DIR))
    try:
        template = env.get_template(nome_template)
        resultado = template.render(**contexto)
        return Result.ok(resultado)
    except Exception as exc:
        return Result.fail(f"Erro ao renderizar {nome_template}: {exc}", codigo="TEMPLATE_RENDER_ERROR")


def gerar_gateway(analysis: dict, pasta_saida: str) -> Result:
    """Gera o gateway FastAPI completo.

    Args:
        analysis: Dicionario do factory_analysis.json.
        pasta_saida: Diretorio onde salvar o gateway.

    Returns:
        Result.ok(lista_de_arquivos) ou Result.fail.
    """
    contexto = _montar_contexto(analysis)
    arquivos_gerados = []

    templates = [
        ("main.py.jinja2", "main.py"),
        ("models.py.jinja2", "models.py"),
        ("routes.py.jinja2", "routes.py"),
    ]

    for tpl_nome, out_nome in templates:
        res = _renderizar_template(tpl_nome, contexto)
        if not res.sucesso:
            return res

        # Salvar
        out_dir = os.path.join(pasta_saida, "src", "gateway")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, out_nome)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(res.valor)
        arquivos_gerados.append(out_path)

    return Result.ok(arquivos_gerados)


def validar_gateway(pasta_gateway: str) -> Result:
    """Valida o gateway gerado (py_compile + imports)."""
    import py_compile

    problemas = []
    for nome in ["main.py", "models.py", "routes.py"]:
        caminho = os.path.join(pasta_gateway, nome)
        if not os.path.isfile(caminho):
            problemas.append(f"Arquivo ausente: {nome}")
            continue
        try:
            py_compile.compile(caminho, doraise=True)
        except py_compile.PyCompileError as exc:
            problemas.append(f"py_compile falhou em {nome}: {exc}")

    if problemas:
        return Result.fail("Gateway invalido", codigo="GATEWAY_INVALID", detalhes={"problemas": problemas})
    return Result.ok(True)
