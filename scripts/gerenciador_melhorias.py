#!/usr/bin/env python3
"""
Gerenciador deterministico de relatorios de analise profunda de melhorias.
Gera o par <arquivo>.html + <arquivo>.json em docs/melhorias/, seguindo o
padrao de nomenclatura e o protocolo de nota (0-10) com evidencia real
definidos em docs/relatorios/DIRETRIZES-DESIGN-RELATORIOS.md.

Etapa anterior ao /plan no fluxo /melhoria -> /plan -> /orchestrate.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_MELHORIAS = ROOT_DIR / "docs" / "melhorias"

NOTA_NAO_AUDITADA = "NAO AUDITADO"
EVIDENCIA_PENDENTE = "(nota pendente de medicao real - nao preencher com estimativa)"


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-")


def _tres_palavras(texto: str) -> str:
    """Reduz um texto (nome curto ou o proprio pedido) as 3 primeiras palavras
    significativas, no formato exigido pela nomenclatura canonica de docs/."""
    palavras = [p for p in slugify(texto).split("-") if p][:3]
    return "-".join(palavras) if palavras else "sem-titulo"


def cmd_init(
    pedido: str,
    nome: str | None = None,
    nota_atual: str | None = None,
    evidencia: str | None = None,
    resumo: str | None = None,
    achados: list[str] | None = None,
    riscos: list[str] | None = None,
    recomendacao: str | None = None,
    destino_base: Path | None = None,
    hoje: date | None = None,
) -> int:
    if not pedido:
        print("[ERRO] --pedido (descricao em linguagem natural) e obrigatorio.")
        return 1

    base = destino_base or DOCS_MELHORIAS
    base.mkdir(parents=True, exist_ok=True)

    tres = _tres_palavras(nome or pedido)
    data_str = (hoje or date.today()).strftime("%d-%m-%Y")
    slug_arquivo = f"{data_str}_melhoria-{tres}"

    caminho_json = base / f"{slug_arquivo}.json"
    caminho_html = base / f"{slug_arquivo}.html"

    if caminho_json.exists() or caminho_html.exists():
        print(f"[ERRO] Ja existe um relatorio com este nome hoje: {slug_arquivo}")
        return 1

    evidencia_str = evidencia or EVIDENCIA_PENDENTE
    nota_atual_str = nota_atual or NOTA_NAO_AUDITADA
    if evidencia_str == EVIDENCIA_PENDENTE:
        # Sem evidencia real, a nota nunca vira numero - mesma regra do /plan.
        nota_atual_str = NOTA_NAO_AUDITADA

    dados = {
        "pedido_original": pedido,
        "data": data_str,
        "nota_atual": nota_atual_str,
        "evidencia": evidencia_str,
        "resumo": resumo or "[Resumo pendente]",
        "achados": achados or [],
        "riscos": riscos or [],
        "recomendacao": recomendacao or "[Recomendacao pendente]",
        "status": "RASCUNHO - aguardando decisao humana sobre proximo passo (ex: iniciar /plan)",
    }

    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)
        f.write("\n")

    caminho_html.write_text(_renderizar_html(slug_arquivo, dados), encoding="utf-8")

    print("[SUCESSO] Relatorio de melhoria criado em:")
    print(f"  {caminho_html}")
    print(f"  {caminho_json}")
    print(f"  Nota Atual: {nota_atual_str}")
    return 0


def _escapar_html(texto: str) -> str:
    return (
        texto.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _renderizar_html(titulo: str, dados: dict) -> str:
    achados_html = "".join(f"<li>{_escapar_html(a)}</li>" for a in dados["achados"]) or "<li>(nenhum achado registrado)</li>"
    riscos_html = "".join(f"<li>{_escapar_html(r)}</li>" for r in dados["riscos"]) or "<li>(nenhum risco registrado)</li>"
    return f"""<!doctype html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<title>{_escapar_html(titulo)}</title>
<style>
  :root {{ color-scheme: light dark; --bg:#0b111a; --fg:#e6edf3; --accent:#388bfd; }}
  * {{ scrollbar-width: thin; scrollbar-color: var(--accent) var(--bg); box-sizing: border-box; }}
  ::-webkit-scrollbar {{ width:4px; height:4px; }}
  ::-webkit-scrollbar-track {{ background: var(--bg); }}
  ::-webkit-scrollbar-thumb {{ background: var(--accent); border-radius:4px; }}
  body {{ background:var(--bg); color:var(--fg); font-family: system-ui, sans-serif; margin:0; padding:24px; max-width: 900px; }}
  h1 {{ font-size: 1.4rem; }}
  .nota {{ font-size:2rem; font-weight:700; color:var(--accent); }}
  section {{ margin-bottom: 24px; }}
</style>
</head>
<body>
<h1>Relatorio de Analise Profunda — {_escapar_html(titulo)}</h1>
<section>
  <strong>Pedido original:</strong> {_escapar_html(dados['pedido_original'])}
</section>
<section>
  <strong>Nota Atual (0-10):</strong> <span class="nota">{_escapar_html(dados['nota_atual'])}</span><br>
  <strong>Evidencia:</strong> {_escapar_html(dados['evidencia'])}
</section>
<section>
  <h2>Resumo</h2>
  <p>{_escapar_html(dados['resumo'])}</p>
</section>
<section>
  <h2>Achados</h2>
  <ul>{achados_html}</ul>
</section>
<section>
  <h2>Riscos / Limitacoes</h2>
  <ul>{riscos_html}</ul>
</section>
<section>
  <h2>Recomendacao</h2>
  <p>{_escapar_html(dados['recomendacao'])}</p>
</section>
<section>
  <strong>Status:</strong> {_escapar_html(dados['status'])}
</section>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description="Gerenciador deterministico de relatorios de melhoria")
    subparsers = parser.add_subparsers(dest="subcomando", required=True)

    parser_init = subparsers.add_parser("init", help="Gera o relatorio de analise profunda de uma melhoria")
    parser_init.add_argument("--pedido", required=True, help="Descricao em linguagem natural do que o usuario quer melhorar")
    parser_init.add_argument("--nome", default=None, help="Nome curto para compor o nome do arquivo (senao deriva do --pedido)")
    parser_init.add_argument("--nota-atual", default=None, help="Nota atual (0-10) do que foi investigado")
    parser_init.add_argument("--evidencia", default=None, help="Evidencia real (arquivos/comandos checados) que sustenta a nota atual")
    parser_init.add_argument("--resumo", default=None, help="Resumo executivo (2-3 frases) da analise")
    parser_init.add_argument("--achados", nargs="+", default=[], help="Lista de achados concretos da investigacao")
    parser_init.add_argument("--riscos", nargs="+", default=[], help="Lista de riscos/limitacoes identificados")
    parser_init.add_argument("--recomendacao", default=None, help="Recomendacao de proximo passo")

    args = parser.parse_args()

    if args.subcomando == "init":
        sys.exit(cmd_init(
            args.pedido,
            nome=args.nome,
            nota_atual=args.nota_atual,
            evidencia=args.evidencia,
            resumo=args.resumo,
            achados=args.achados,
            riscos=args.riscos,
            recomendacao=args.recomendacao,
        ))


if __name__ == "__main__":
    main()
