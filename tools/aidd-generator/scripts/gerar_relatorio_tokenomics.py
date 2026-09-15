#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GERADOR DE RELATÓRIO HTML DE TOKENOMICS — Dashboard de comprovação.

Lê o JSON do benchmark_tokenomics.py e gera um HTML autocontido com:
- Tabela de economia por fase (legado vs otimizado)
- Gráfico de barras (CSS puro, sem JS externo)
- Custo em dólares
- Status de qualidade (testes)
- Assinatura SHA-256 para auditoria

Uso:
    python scripts/gerar_relatorio_tokenomics.py
    python scripts/gerar_relatorio_tokenomics.py --benchmark benchmarks/benchmark_2026-09-11.json
    python scripts/gerar_relatorio_tokenomics.py --gerar-e-abrir

Exit: 0 = relatório gerado, 1 = falha.
"""

import argparse
import json
import os
import sys
import webbrowser
from pathlib import Path
from typing import Any, Dict, Optional

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

SCRIPTS_DIR = Path(__file__).resolve().parent
GENERATOR_DIR = SCRIPTS_DIR.parent
BENCHMARKS_DIR = GENERATOR_DIR / 'benchmarks'
REPORTS_DIR = GENERATOR_DIR / 'reports'
REPORTS_DIR.mkdir(exist_ok=True)


def _encontrar_ultimo_benchmark() -> Optional[Path]:
    """Encontra o benchmark JSON mais recente."""
    if not BENCHMARKS_DIR.exists():
        return None
    jsons = sorted(BENCHMARKS_DIR.glob('benchmark_*.json'), reverse=True)
    return jsons[0] if jsons else None


def _barra_css(pct: float, cor: str) -> str:
    """Gera HTML de barra de progresso CSS pura."""
    return (
        f'<div style="background:#1a1a2e;border-radius:6px;height:28px;width:100%;position:relative;overflow:hidden">'
        f'<div style="background:{cor};height:100%;width:{min(pct, 100):.1f}%;'
        f'border-radius:6px;transition:width 0.5s ease"></div>'
        f'<span style="position:absolute;right:8px;top:50%;transform:translateY(-50%);'
        f'color:#fff;font-size:13px;font-weight:600">{pct:.1f}%</span>'
        f'</div>'
    )


def _cor_economia(pct: float) -> str:
    if pct >= 50:
        return '#00c853'
    elif pct >= 30:
        return '#2196f3'
    elif pct >= 10:
        return '#ff9800'
    return '#f44336'


def gerar_html(dados: Dict[str, Any]) -> str:
    """Gera o HTML do relatório a partir dos dados do benchmark."""
    fases = dados.get('fases', [])
    total_leg = dados.get('tokens_total_legado', 0)
    total_otim = dados.get('tokens_total_otimizado', 0)
    economia_total = dados.get('economia_total_pct', 0)
    custo_leg = dados.get('custo_legado_usd', 0)
    custo_otim = dados.get('custo_otimizado_usd', 0)
    economia_usd = dados.get('economia_custo_usd', 0)
    qualidade = dados.get('qualidade_testes')
    sha256 = dados.get('sha256_relatorio', 'N/A')
    timestamp = dados.get('timestamp', 'N/A')
    ideia = dados.get('ideia', 'N/A')

    # Linhas da tabela
    linhas_tabela = ''
    for f in fases:
        cor = _cor_economia(f.get('economia_pct', 0))
        linhas_tabela += f'''
        <tr>
            <td style="padding:12px 16px;border-bottom:1px solid #2a2a4a;font-weight:600">{f.get('nome', '')}</td>
            <td style="padding:12px 16px;border-bottom:1px solid #2a2a4a;text-align:right;font-family:monospace">
                {f.get('tokens_legado', 0):,}
            </td>
            <td style="padding:12px 16px;border-bottom:1px solid #2a2a4a;text-align:right;font-family:monospace">
                {f.get('tokens_otimizado', 0):,}
            </td>
            <td style="padding:12px 16px;border-bottom:1px solid #2a2a4a;text-align:right;font-family:monospace;color:{cor};font-weight:700">
                {f.get('economia_tokens', 0):,}
            </td>
            <td style="padding:12px 16px;border-bottom:1px solid #2a2a4a;width:200px">
                {_barra_css(f.get('economia_pct', 0), cor)}
            </td>
            <td style="padding:12px 16px;border-bottom:1px solid #2a2a4a;font-size:12px;color:#aaa;max-width:250px">
                {f.get('descricao', '')}
            </td>
        </tr>'''

    # Status de qualidade
    if qualidade is True:
        badge_qualidade = '<span style="background:#00c853;color:#fff;padding:6px 16px;border-radius:20px;font-weight:700">✅ TODOS OS TESTES PASSARAM</span>'
    elif qualidade is False:
        badge_qualidade = '<span style="background:#f44336;color:#fff;padding:6px 16px;border-radius:20px;font-weight:700">❌ TESTES FALHARAM</span>'
    else:
        badge_qualidade = '<span style="background:#666;color:#fff;padding:6px 16px;border-radius:20px">⚪ NÃO TESTADO</span>'

    # Gráfico de barras comparativo (CSS puro)
    max_tokens = max(total_leg, 1)
    barra_legado_h = max(20, int(300 * total_leg / max_tokens))
    barra_otim_h = max(20, int(300 * total_otim / max_tokens))

    html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Tokenomics — aidd-generator</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            padding: 40px 20px;
            line-height: 1.6;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{
            text-align: center;
            padding: 40px 0;
            border-bottom: 2px solid #21262d;
            margin-bottom: 40px;
        }}
        .header h1 {{
            font-size: 2.2em;
            color: #58a6ff;
            margin-bottom: 8px;
        }}
        .header .subtitle {{ color: #8b949e; font-size: 1.1em; }}
        .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 40px; }}
        .card {{
            background: #161b22;
            border: 1px solid #21262d;
            border-radius: 12px;
            padding: 24px;
            text-align: center;
        }}
        .card .label {{ color: #8b949e; font-size: 0.9em; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }}
        .card .value {{ font-size: 2em; font-weight: 700; font-family: 'JetBrains Mono', monospace; }}
        .card .value.green {{ color: #00c853; }}
        .card .value.blue {{ color: #58a6ff; }}
        .card .value.orange {{ color: #ff9800; }}
        .card .value.red {{ color: #f44336; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: #161b22;
            border-radius: 12px;
            overflow: hidden;
            margin-bottom: 40px;
        }}
        th {{
            background: #21262d;
            padding: 14px 16px;
            text-align: left;
            font-size: 0.85em;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #8b949e;
        }}
        th:nth-child(n+2) {{ text-align: right; }}
        th:last-child {{ text-align: left; }}
        .chart-section {{
            background: #161b22;
            border: 1px solid #21262d;
            border-radius: 12px;
            padding: 32px;
            margin-bottom: 40px;
        }}
        .chart-title {{ font-size: 1.2em; font-weight: 600; margin-bottom: 24px; color: #58a6ff; }}
        .bar-group {{ display: flex; align-items: center; margin-bottom: 16px; gap: 16px; }}
        .bar-label {{ width: 120px; text-align: right; font-size: 0.9em; color: #8b949e; }}
        .bar {{ height: 36px; border-radius: 8px; display: flex; align-items: center; padding: 0 12px; font-weight: 600; font-size: 0.85em; color: #fff; min-width: 60px; }}
        .bar.legado {{ background: linear-gradient(90deg, #f44336, #ff6b6b); }}
        .bar.otimizado {{ background: linear-gradient(90deg, #00c853, #69f0ae); }}
        .footer {{
            text-align: center;
            padding: 32px 0;
            border-top: 1px solid #21262d;
            color: #484f58;
            font-size: 0.85em;
        }}
        .footer .sha {{ font-family: monospace; font-size: 0.8em; word-break: break-all; margin-top: 8px; color: #30363d; }}
        .technique-tag {{
            display: inline-block;
            background: #1f6feb22;
            color: #58a6ff;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.8em;
            margin: 2px;
            border: 1px solid #1f6feb44;
        }}
    </style>
</head>
<body>
<div class="container">

    <div class="header">
        <h1>Relatório de Tokenomics</h1>
        <div class="subtitle">aidd-generator — Medição Real de Economia de Tokens</div>
        <div style="margin-top:12px;color:#484f58;font-size:0.9em">
            Ideia: <strong>{ideia}</strong> &nbsp;|&nbsp; Data: <strong>{timestamp}</strong>
        </div>
    </div>

    <!-- CARDS RESUMO -->
    <div class="cards">
        <div class="card">
            <div class="label">Tokens Legado</div>
            <div class="value red">{total_leg:,}</div>
        </div>
        <div class="card">
            <div class="label">Tokens Otimizado</div>
            <div class="value green">{total_otim:,}</div>
        </div>
        <div class="card">
            <div class="label">Economia Total</div>
            <div class="value green">{economia_total:.1f}%</div>
        </div>
        <div class="card">
            <div class="label">Economia (tokens)</div>
            <div class="value blue">{total_leg - total_otim:,}</div>
        </div>
        <div class="card">
            <div class="label">Custo Legado (est.)</div>
            <div class="value orange">${custo_leg:.4f}</div>
        </div>
        <div class="card">
            <div class="label">Custo Otimizado (est.)</div>
            <div class="value green">${custo_otim:.4f}</div>
        </div>
        <div class="card">
            <div class="label">Economia USD</div>
            <div class="value green">${economia_usd:.4f}</div>
        </div>
        <div class="card">
            <div class="label">Qualidade (pytest)</div>
            <div>{badge_qualidade}</div>
        </div>
    </div>

    <!-- GRÁFICO COMPARATIVO -->
    <div class="chart-section">
        <div class="chart-title">Comparação Legado vs Otimizado</div>
        <div class="bar-group">
            <div class="bar-label">Legado</div>
            <div class="bar legado" style="width:{min(100, 100)}%">{total_leg:,} tokens</div>
        </div>
        <div class="bar-group">
            <div class="bar-label">Otimizado</div>
            <div class="bar otimizado" style="width:{min(100, total_otim / max(total_leg, 1) * 100):.1f}%">{total_otim:,} tokens</div>
        </div>
    </div>

    <!-- TABELA DETALHADA -->
    <table>
        <thead>
            <tr>
                <th>Fase</th>
                <th>Legado</th>
                <th>Otimizado</th>
                <th>Economia</th>
                <th>Redução</th>
                <th>Técnica Aplicada</th>
            </tr>
        </thead>
        <tbody>
            {linhas_tabela}
        </tbody>
    </table>

    <!-- TÉCNICAS APLICADAS -->
    <div class="chart-section">
        <div class="chart-title">Técnicas de Engenharia Agêntica Aplicadas</div>
        <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:16px">
            <span class="technique-tag">Subagentes Efêmeros (SubagentPurger)</span>
            <span class="technique-tag">Context-Purge Engine</span>
            <span class="technique-tag">Prompt por Composição Modular</span>
            <span class="technique-tag">Fix-loop Cirúrgico (diff + traceback)</span>
            <span class="technique-tag">Orçamento de Tokens por Fase</span>
            <span class="technique-tag">Top-K + Campos Seletos</span>
            <span class="technique-tag">Reparo JSON Determinístico Zero-LLM</span>
            <span class="technique-tag">Hermeticidade Verificável (gate AST)</span>
            <span class="technique-tag">Tríade Caveman Ultra</span>
            <span class="technique-tag">Zero-Token (fases 1 e 5)</span>
            <span class="technique-tag">Medição Honesta (autodeclarado vs medido_api)</span>
            <span class="technique-tag">Middleware de Compressão (LLMLingua-2)</span>
        </div>
    </div>

    <!-- ASSINATURA -->
    <div class="footer">
        <div>Relatório gerado automaticamente pelo benchmark_tokenomics.py</div>
        <div>Medição: tiktoken cl100k_base (real, não estimativa)</div>
        <div>Modelo de custo referência: GPT-4o ($2.50/1M input, $10/1M output)</div>
        <div class="sha">SHA-256: {sha256}</div>
        <div style="margin-top:16px;color:#30363d">
            Este relatório é autocontido (HTML + CSS, sem dependências externas).
            A assinatura SHA-256 permite verificação de integridade.
        </div>
    </div>

</div>
</body>
</html>'''
    return html


def gerar_relatorio_de_benchmark(caminho_benchmark: Optional[Path] = None) -> Path:
    """Lê um benchmark JSON e gera o relatório HTML."""
    if caminho_benchmark is None:
        caminho_benchmark = _encontrar_ultimo_benchmark()

    if caminho_benchmark is None or not caminho_benchmark.exists():
        print("❌ Nenhum benchmark encontrado. Rode benchmark_tokenomics.py primeiro.")
        sys.exit(1)

    print(f"📊 Lendo benchmark: {caminho_benchmark}")
    dados = json.loads(caminho_benchmark.read_text(encoding='utf-8'))

    html = gerar_html(dados)

    # Salvar
    ts = dados.get('timestamp', 'unknown').replace(':', '-').replace('T', '_')
    caminho_html = REPORTS_DIR / f'relatorio_tokenomics_{ts}.html'
    caminho_html.write_text(html, encoding='utf-8')
    print(f"✅ Relatório gerado: {caminho_html}")

    return caminho_html


def main():
    parser = argparse.ArgumentParser(description='Gerador de relatório HTML de Tokenomics')
    parser.add_argument('--benchmark', type=str, default=None,
                        help='Caminho para o JSON do benchmark')
    parser.add_argument('--gerar-e-abrir', action='store_true',
                        help='Gera e abre no navegador')
    args = parser.parse_args()

    caminho = Path(args.benchmark) if args.benchmark else None
    caminho_html = gerar_relatorio_de_benchmark(caminho)

    if args.gerar_e_abrir:
        webbrowser.open(str(caminho_html))
        print(f"🌐 Abrindo no navegador: {caminho_html}")


if __name__ == '__main__':
    main()
