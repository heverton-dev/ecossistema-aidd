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

STATUS_AVALIACAO_VALIDOS = {"feito", "parcial", "nao-feito"}
STATUS_AVALIACAO_ROTULO = {"feito": "✅ Feito", "parcial": "🟡 Parcial", "nao-feito": "❌ Nao feito"}

try:
    from scripts import gerenciador_planos as _gp
except ImportError:  # executado como script solto - scripts/ ja esta em sys.path[0]
    import gerenciador_planos as _gp


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


def _parsear_itens_avaliados(entradas: list[str]) -> list[dict]:
    """Cada entrada no formato '<item>::<status>::<justificativa>'. status deve
    ser um de STATUS_AVALIACAO_VALIDOS. Levanta ValueError com mensagem clara
    se o formato ou o status forem invalidos - nunca aceita silenciosamente."""
    resultado = []
    for entrada in entradas:
        partes = entrada.split("::", 2)
        if len(partes) != 3:
            raise ValueError(
                f"--itens-avaliados: formato invalido em '{entrada}'. "
                "Use '<item>::<feito|parcial|nao-feito>::<justificativa>'."
            )
        item, status, justificativa = (p.strip() for p in partes)
        if status not in STATUS_AVALIACAO_VALIDOS:
            raise ValueError(
                f"--itens-avaliados: status '{status}' invalido em '{entrada}'. "
                f"Valores aceitos: {', '.join(sorted(STATUS_AVALIACAO_VALIDOS))}."
            )
        if not justificativa:
            raise ValueError(f"--itens-avaliados: justificativa vazia em '{entrada}' - obrigatoria.")
        resultado.append({"item": item, "status": status, "justificativa": justificativa})
    return resultado


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
    plano_existente: str | None = None,
    item_relacionado: str | None = None,
    itens_avaliados: list[str] | None = None,
) -> int:
    if not pedido:
        print("[ERRO] --pedido (descricao em linguagem natural) e obrigatorio.")
        return 1

    try:
        itens_avaliados_parsed = _parsear_itens_avaliados(itens_avaliados or [])
    except ValueError as exc:
        print(f"[ERRO] {exc}")
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

    nota_anterior_str = None
    evidencia_anterior_str = None
    if plano_existente:
        pasta_plano = Path(plano_existente)
        if not pasta_plano.is_absolute():
            pasta_plano = ROOT_DIR / pasta_plano
        info_anterior = (
            _gp.ler_nota_item(pasta_plano, item_relacionado) if item_relacionado
            else _gp.ler_nota_geral(pasta_plano)
        )
        if info_anterior is None:
            nota_anterior_str = _gp.NOTA_NAO_AUDITADA
            evidencia_anterior_str = "(plano criado antes desta metrica existir, ou item sem nota registrada)"
        else:
            nota_anterior_str = info_anterior["nota_atual"]
            evidencia_anterior_str = info_anterior["evidencia"]

    dados = {
        "pedido_original": pedido,
        "data": data_str,
        "nota_atual": nota_atual_str,
        "evidencia": evidencia_str,
        "plano_existente": plano_existente,
        "item_relacionado": item_relacionado,
        "nota_anterior": nota_anterior_str,
        "evidencia_anterior": evidencia_anterior_str,
        "itens_avaliados": itens_avaliados_parsed,
        "resumo": resumo or "[Resumo pendente]",
        "achados": achados or [],
        "riscos": riscos or [],
        "recomendacao": recomendacao or "[Recomendacao pendente]",
        "status": "RASCUNHO - aguardando decisao humana sobre proximo passo (ex: iniciar /plan, ou atualizar a nota do plano existente)",
    }

    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)
        f.write("\n")

    caminho_html.write_text(_renderizar_html(slug_arquivo, dados), encoding="utf-8")

    print("[SUCESSO] Relatorio de melhoria criado em:")
    print(f"  {caminho_html}")
    print(f"  {caminho_json}")
    if plano_existente:
        alvo_txt = f" (item {item_relacionado})" if item_relacionado else " (nota geral da iniciativa)"
        print(f"  Reanalise do plano: {plano_existente}{alvo_txt}")
        print(f"  Nota Anterior: {nota_anterior_str}  ->  Nota Nova: {nota_atual_str}")
        item_flag = f' --item "{item_relacionado}"' if item_relacionado else ""
        print("  Para gravar a nota nova no plano (so depois de confirmar com o usuario):")
        print(f'    python ecossistema.py plan atualizar-nota "{plano_existente}"{item_flag} '
              f'--nota-atual "{nota_atual_str}" --evidencia "{caminho_html.name}"')
    else:
        print(f"  Nota Atual: {nota_atual_str}")
    return 0


def _escapar_html(texto: str) -> str:
    return (
        texto.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


STATUS_BADGE_CLASSE = {"feito": "badge-good", "parcial": "badge-warn", "nao-feito": "badge-bad"}


def _banda_nota(valor: str) -> str:
    """Classifica a nota numerica em faixa de cor (good/warn/bad).
    Nao numerica (ex: NAO AUDITADO) cai em 'neutra'."""
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return "neutra"
    if numero >= 7:
        return "good"
    if numero >= 4:
        return "warn"
    return "bad"


def _renderizar_gauge_nota(rotulo: str, valor: str) -> str:
    """Barra horizontal 0-10 colorida por faixa, com o numero sempre escrito
    ao lado (nunca so cor - acessibilidade). NAO AUDITADO vira barra neutra
    tracejada, sem fingir uma posicao numerica que nao existe."""
    banda = _banda_nota(valor)
    try:
        pct = max(0.0, min(10.0, float(valor))) * 10
        largura = f"{pct:.0f}%"
        rotulo_valor = f"{valor}/10"
    except (TypeError, ValueError):
        largura = "100%"
        rotulo_valor = _escapar_html(valor)
    classe_tracejada = " gauge-fill-neutra" if banda == "neutra" else ""
    return f"""<div class="gauge">
  <div class="gauge-rotulo">{_escapar_html(rotulo)}</div>
  <div class="gauge-trilho" role="img" aria-label="{_escapar_html(rotulo)}: {rotulo_valor}">
    <div class="gauge-fill gauge-{banda}{classe_tracejada}" style="width:{largura};"></div>
  </div>
  <div class="gauge-valor gauge-texto-{banda}">{rotulo_valor}</div>
</div>"""


def _renderizar_badge(status: str) -> str:
    classe = STATUS_BADGE_CLASSE.get(status, "badge-neutra")
    rotulo = STATUS_AVALIACAO_ROTULO.get(status, status)
    return f'<span class="badge {classe}">{_escapar_html(rotulo)}</span>'


def _renderizar_barra_distribuicao(itens: list[dict]) -> str:
    """Barra segmentada mostrando a proporcao feito/parcial/nao-feito -
    leitura instantanea antes de ler a tabela item a item."""
    if not itens:
        return ""
    contagem = {"feito": 0, "parcial": 0, "nao-feito": 0}
    for i in itens:
        contagem[i["status"]] = contagem.get(i["status"], 0) + 1
    total = len(itens)
    segmentos = "".join(
        f'<div class="dist-seg dist-{status}" style="width:{(qtd / total * 100):.1f}%" '
        f'title="{STATUS_AVALIACAO_ROTULO.get(status, status)}: {qtd}"></div>'
        for status, qtd in contagem.items() if qtd
    )
    legenda = "".join(
        f'<span class="dist-legenda-item"><span class="dist-dot dist-{status}"></span>'
        f'{STATUS_AVALIACAO_ROTULO.get(status, status)}: {qtd}</span>'
        for status, qtd in contagem.items() if qtd
    )
    return f"""<div class="dist-bar" role="img" aria-label="Distribuicao de status dos itens avaliados">{segmentos}</div>
<div class="dist-legenda">{legenda}</div>"""


def _renderizar_html(titulo: str, dados: dict) -> str:
    achados_html = "".join(f"<li>{_escapar_html(a)}</li>" for a in dados["achados"]) or "<li>(nenhum achado registrado)</li>"
    riscos_html = "".join(f"<li>{_escapar_html(r)}</li>" for r in dados["riscos"]) or "<li>(nenhum risco registrado)</li>"

    secao_nota = f"""<section class="card">
  <h2 class="eyebrow">Nota Atual</h2>
  {_renderizar_gauge_nota("Nota Atual (0-10)", dados['nota_atual'])}
  <p class="evidencia"><strong>Evidencia:</strong> {_escapar_html(dados['evidencia'])}</p>
</section>"""

    secao_reanalise = ""
    if dados.get("plano_existente"):
        alvo = f"item {dados['item_relacionado']}" if dados.get("item_relacionado") else "nota geral da iniciativa"
        secao_nota = f"""<section class="card">
  <h2 class="eyebrow">Reanalise de Plano Existente ({_escapar_html(alvo)})</h2>
  <p class="plano-caminho"><strong>Plano:</strong> {_escapar_html(dados['plano_existente'])}</p>
  <div class="comparativo-notas">
    {_renderizar_gauge_nota("Nota Anterior", dados['nota_anterior'])}
    {_renderizar_gauge_nota("Nota Nova", dados['nota_atual'])}
  </div>
  <p class="evidencia"><strong>Evidencia (anterior):</strong> {_escapar_html(dados['evidencia_anterior'])}</p>
  <p class="evidencia"><strong>Evidencia (nova):</strong> {_escapar_html(dados['evidencia'])}</p>
</section>"""

        itens_avaliados = dados.get("itens_avaliados", [])
        linhas_itens = "".join(
            f"<tr><td class=\"col-item\">{_escapar_html(i['item'])}</td>"
            f"<td>{_renderizar_badge(i['status'])}</td>"
            f"<td>{_escapar_html(i['justificativa'])}</td></tr>"
            for i in itens_avaliados
        )
        if linhas_itens:
            secao_reanalise = f"""<section class="card">
  <h2 class="eyebrow">Previsto no plano vs. implementado hoje</h2>
  {_renderizar_barra_distribuicao(itens_avaliados)}
  <div class="tabela-scroll">
  <table>
    <thead><tr><th class="col-item">Item</th><th>Status</th><th>Justificativa</th></tr></thead>
    <tbody>{linhas_itens}</tbody>
  </table>
  </div>
</section>"""

    return f"""<!doctype html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_escapar_html(titulo)}</title>
<style>
  :root {{
    color-scheme: light dark;
    --bg:#f6f7f9; --bg-card:#ffffff; --border:#e2e5ea;
    --fg:#1b1f26; --fg-muted:#5b6472;
    --accent:#2563eb; --accent-fg:#ffffff;
    --good:#1a7f4e; --good-bg:#e4f6ec;
    --warn:#9a6400; --warn-bg:#fdf1d9;
    --bad:#b3261e; --bad-bg:#fbe7e6;
    --neutra:#6b7280; --neutra-bg:#eceef1;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg:#0b111a; --bg-card:#131b26; --border:#232d3b;
      --fg:#e6edf3; --fg-muted:#94a3b8;
      --accent:#4c8dff; --accent-fg:#08111f;
      --good:#3ddc84; --good-bg:#0f2c1d;
      --warn:#f2b84b; --warn-bg:#2c2410;
      --bad:#ff6b6b; --bad-bg:#2c1414;
      --neutra:#9aa4b2; --neutra-bg:#1b232f;
    }}
  }}
  * {{ box-sizing: border-box; scrollbar-width: thin; scrollbar-color: var(--accent) var(--bg); }}
  ::-webkit-scrollbar {{ width:4px; height:4px; }}
  ::-webkit-scrollbar-track {{ background: var(--bg); }}
  ::-webkit-scrollbar-thumb {{ background: var(--accent); border-radius:4px; }}
  body {{
    background:var(--bg); color:var(--fg);
    font-family: -apple-system, "Segoe UI", system-ui, sans-serif;
    line-height: 1.5; margin:0; padding: 32px 16px;
  }}
  .pagina {{ max-width: 760px; margin: 0 auto; }}
  h1 {{ font-size: 1.375rem; font-weight: 700; margin: 0 0 4px; letter-spacing: -0.01em; }}
  .subtitulo {{ color: var(--fg-muted); font-size: 0.875rem; margin: 0 0 24px; }}
  .eyebrow {{
    font-size: 0.75rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.05em; color: var(--fg-muted); margin: 0 0 16px;
  }}
  .card {{
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: 12px; padding: 24px; margin-bottom: 16px;
  }}
  .pedido {{ font-size: 0.9375rem; color: var(--fg-muted); margin-bottom: 16px; }}
  .pedido strong {{ color: var(--fg); }}
  .evidencia {{ font-size: 0.8125rem; color: var(--fg-muted); margin: 8px 0 0; }}
  .plano-caminho {{ font-size: 0.8125rem; color: var(--fg-muted); margin: 0 0 16px; word-break: break-all; }}

  .gauge {{ display:flex; align-items:center; gap:12px; margin-bottom: 8px; }}
  .gauge-rotulo {{ flex: 0 0 140px; font-size: 0.8125rem; color: var(--fg-muted); }}
  .gauge-trilho {{ flex: 1; height: 10px; background: var(--border); border-radius: 6px; overflow: hidden; }}
  .gauge-fill {{ height: 100%; border-radius: 6px; }}
  .gauge-fill-neutra {{
    background-image: repeating-linear-gradient(45deg, currentColor 0 6px, transparent 6px 12px);
  }}
  .gauge-good {{ background: var(--good); color: var(--good); }}
  .gauge-warn {{ background: var(--warn); color: var(--warn); }}
  .gauge-bad {{ background: var(--bad); color: var(--bad); }}
  .gauge-neutra {{ background: var(--neutra); color: var(--neutra); }}
  .gauge-valor {{ flex: 0 0 auto; font-weight: 700; font-size: 0.9375rem; min-width: 64px; text-align: right; }}
  .gauge-texto-good {{ color: var(--good); }}
  .gauge-texto-warn {{ color: var(--warn); }}
  .gauge-texto-bad {{ color: var(--bad); }}
  .gauge-texto-neutra {{ color: var(--neutra); }}
  .comparativo-notas {{ margin: 8px 0 4px; }}

  .badge {{
    display: inline-block; padding: 2px 10px; border-radius: 999px;
    font-size: 0.8125rem; font-weight: 600; white-space: nowrap;
  }}
  .badge-good {{ background: var(--good-bg); color: var(--good); }}
  .badge-warn {{ background: var(--warn-bg); color: var(--warn); }}
  .badge-bad {{ background: var(--bad-bg); color: var(--bad); }}
  .badge-neutra {{ background: var(--neutra-bg); color: var(--neutra); }}

  .dist-bar {{ display:flex; height: 10px; border-radius: 6px; overflow: hidden; margin-bottom: 8px; background: var(--border); }}
  .dist-seg {{ height: 100%; }}
  .dist-feito {{ background: var(--good); }}
  .dist-parcial {{ background: var(--warn); }}
  .dist-nao-feito {{ background: var(--bad); }}
  .dist-legenda {{ display:flex; flex-wrap: wrap; gap: 16px; margin-bottom: 20px; }}
  .dist-legenda-item {{ font-size: 0.8125rem; color: var(--fg-muted); display:flex; align-items:center; gap:6px; }}
  .dist-dot {{ width:8px; height:8px; border-radius:50%; display:inline-block; }}
  .dist-dot.dist-feito {{ background: var(--good); }}
  .dist-dot.dist-parcial {{ background: var(--warn); }}
  .dist-dot.dist-nao-feito {{ background: var(--bad); }}

  .tabela-scroll {{ overflow-x: auto; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.875rem; }}
  th {{ text-align: left; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.04em;
       color: var(--fg-muted); font-weight: 600; padding: 8px 12px; border-bottom: 1px solid var(--border); }}
  td {{ padding: 10px 12px; border-bottom: 1px solid var(--border); vertical-align: top; }}
  tr:last-child td {{ border-bottom: none; }}
  .col-item {{ white-space: nowrap; font-variant-numeric: tabular-nums; color: var(--fg-muted); }}

  h2.titulo-secao {{ font-size: 1rem; font-weight: 700; margin: 0 0 12px; }}
  ul {{ margin: 0; padding-left: 20px; }}
  li {{ margin-bottom: 6px; }}
  .status-rodape {{ font-size: 0.8125rem; color: var(--fg-muted); }}
</style>
</head>
<body>
<div class="pagina">
  <h1>Relatorio de Analise Profunda</h1>
  <p class="subtitulo">{_escapar_html(titulo)}</p>

  <section class="card">
    <p class="pedido"><strong>Pedido original:</strong> {_escapar_html(dados['pedido_original'])}</p>
  </section>

  {secao_nota}
  {secao_reanalise}

  <section class="card">
    <h2 class="titulo-secao">Resumo</h2>
    <p>{_escapar_html(dados['resumo'])}</p>
  </section>

  <section class="card">
    <h2 class="titulo-secao">Achados</h2>
    <ul>{achados_html}</ul>
  </section>

  <section class="card">
    <h2 class="titulo-secao">Riscos / Limitacoes</h2>
    <ul>{riscos_html}</ul>
  </section>

  <section class="card">
    <h2 class="titulo-secao">Recomendacao</h2>
    <p>{_escapar_html(dados['recomendacao'])}</p>
  </section>

  <p class="status-rodape"><strong>Status:</strong> {_escapar_html(dados['status'])}</p>
</div>
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
    parser_init.add_argument("--plano-existente", default=None,
                              help="Caminho de um plano ja existente (docs/planos/...) para reanalisar - "
                                   "a nota atual daquele plano/item vira 'nota anterior' no relatorio")
    parser_init.add_argument("--item", default=None,
                              help="Numero/slug/arquivo do item do plano existente a reanalisar "
                                   "(omitir para a nota geral da iniciativa)")
    parser_init.add_argument("--itens-avaliados", nargs="+", default=[],
                              help="Comparacao previsto-vs-implementado por item do plano existente, "
                                   "formato '<item>::<feito|parcial|nao-feito>::<justificativa>'")

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
            plano_existente=args.plano_existente,
            item_relacionado=args.item,
            itens_avaliados=args.itens_avaliados,
        ))


if __name__ == "__main__":
    main()
