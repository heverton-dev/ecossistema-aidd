#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador determinístico de HTML para aidd-anatomy, seguindo o padrão visual de docs/mapas-visuais/.
"""

import sys
from pathlib import Path

HTML_TEMPLATE = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Anatomia Técnica: {nome_alvo}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700;12..96,800&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root {{
  --paper:#EEF1F4; --surface:#FFFFFF; --ink:#16202B; --muted:#5A6878; --line:#D3DAE2;
  --brick:#F2B705; --brick-ink:#3B2C00;
  --c-pensa:#7048E8; --c-trabalha:#2F6FDB; --c-regra:#0E9384; --c-guarda:#D92D20; --c-liga:#C4620A;
  --ok:#12805C; --ok-bg:#E3F4EC; --falha:#C0261B; --falha-bg:#FCE7E5; --fach:#A15C00; --fach-bg:#FDF0DC;
  --tint:#E4E9EF;
  --display:"Bricolage Grotesque", "Segoe UI", system-ui, sans-serif;
  --body:"IBM Plex Sans", "Segoe UI", system-ui, sans-serif;
  --mono:"IBM Plex Mono", ui-monospace, Consolas, monospace;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    color-scheme:dark;
    --paper:#0F141A; --surface:#17202A; --ink:#E6EBF0; --muted:#95A3B2; --line:#2A3642;
    --brick:#F5C542; --brick-ink:#2A1F00;
    --c-pensa:#A48BFF; --c-trabalha:#79A4FF; --c-regra:#3CCBB4; --c-guarda:#FF7A70; --c-liga:#FFAA55;
    --ok:#4FD1A0; --ok-bg:#12302A; --falha:#FF8A80; --falha-bg:#3A1A18; --fach:#FFBE5C; --fach-bg:#3A2A10;
    --tint:#1D2833;
  }}
}}
* {{ box-sizing:border-box }}
body {{ margin:0; background:var(--paper); color:var(--ink); font-family:var(--body); font-size:16px; line-height:1.55; padding-inline:16px; padding-block:0 64px }}
.wrap {{ max-width:1040px; margin:0 auto }}
h1,h2,h3 {{ font-family:var(--display); text-wrap:balance; margin:0; line-height:1.1 }}
h1 {{ font-size:clamp(2.0rem,5vw,3.0rem); font-weight:800; letter-spacing:-.02em }}
h2 {{ font-size:clamp(1.3rem,3vw,1.8rem); font-weight:700; letter-spacing:-.01em; margin-top:16px }}
h3 {{ font-size:1.1rem; font-weight:700 }}
p {{ margin:0; max-width:75ch }}
code {{ font-family:var(--mono); font-size:.86em; background:var(--tint); padding:.08em .35em; border-radius:4px }}
pre {{ margin:0; font-family:var(--mono); font-size:.82rem; background:var(--tint); border-radius:8px; padding:14px 16px; overflow-x:auto }}
.eyebrow {{ font-family:var(--mono); font-size:.75rem; letter-spacing:.12em; text-transform:uppercase; color:var(--muted) }}
header {{ display:flex; flex-direction:column; gap:12px; padding-block:28px 24px }}
section {{ display:flex; flex-direction:column; gap:16px; padding-block:32px; border-top:1px solid var(--line) }}
.box {{ background:var(--surface); border:1px solid var(--line); border-radius:8px; padding:18px; display:flex; flex-direction:column; gap:10px }}
.grid2 {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px }}
@media (max-width:680px) {{ .grid2 {{ grid-template-columns:1fr }} }}
.chip {{ display:inline-block; font-family:var(--mono); font-size:.72rem; letter-spacing:.04em; text-transform:uppercase; padding:3px 8px; border-radius:999px; background:var(--tint); color:var(--muted) }}
.chip.ok {{ color:var(--ok); background:var(--ok-bg) }}
.chip.falha {{ color:var(--falha); background:var(--falha-bg) }}
.chip.aviso {{ color:var(--fach); background:var(--fach-bg) }}
.chip.lei {{ color:var(--brick-ink); background:var(--brick) }}
.passos {{ counter-reset:passo; display:flex; flex-direction:column; gap:10px; margin:0; padding:0; list-style:none }}
.passos li {{ counter-increment:passo; display:grid; grid-template-columns:36px 1fr; gap:12px; align-items:start; background:var(--surface); border:1px solid var(--line); border-radius:8px; padding:14px 16px }}
.passos li::before {{ content:counter(passo); font-family:var(--display); font-weight:800; font-size:1.3rem; color:var(--c-trabalha); line-height:1.2 }}
.passos li div {{ display:flex; flex-direction:column; gap:6px }}
.bloco-esteira {{ display:flex; flex-direction:column; gap:10px; background:var(--surface); border:1px solid var(--line); border-radius:8px; padding:16px }}
.esteira-passo {{ display:grid; grid-template-columns:120px 1fr; gap:12px; align-items:center; padding-block:6px; border-bottom:1px dashed var(--line) }}
.esteira-passo:last-child {{ border-bottom:none }}
.esteira-tag {{ font-family:var(--mono); font-size:.75rem; font-weight:600; text-transform:uppercase; color:var(--muted) }}
.alert {{ border-radius:8px; padding:14px 16px; font-size:.92rem; display:flex; flex-direction:column; gap:6px }}
.alert.warning {{ background:var(--falha-bg); border-left:4px solid var(--falha); color:var(--ink) }}
.alert.tip {{ background:var(--ok-bg); border-left:4px solid var(--ok); color:var(--ink) }}
.alert-title {{ font-weight:700; font-family:var(--display); font-size:1.0rem }}
.cartao-tabela {{ width:100%; border-collapse:collapse; font-size:.9rem }}
.cartao-tabela td, .cartao-tabela th {{ padding:8px 12px; border:1px solid var(--line); text-align:left }}
.cartao-tabela th {{ background:var(--tint); font-family:var(--mono); font-weight:600; width:25% }}
</style>
</head>
<body>
<div class="wrap">
<header>
  <div class="eyebrow">Ecossistema AIDD • Anatomia Técnica</div>
  <h1>{nome_alvo}</h1>
  <p class="lead">{finalidade}</p>
</header>

<section>
  <h2>Cartão de Identidade</h2>
  <table class="cartao-tabela">
    <tr><th>Nome do Alvo</th><td><code>{nome_alvo}</code></td></tr>
    <tr><th>Finalidade</th><td>{finalidade}</td></tr>
    <tr><th>Nível de Maturidade</th><td><span class="chip {classe_maturidade}">{nivel_maturidade}</span></td></tr>
    <tr><th>Trava Principal</th><td>{trava_principal}</td></tr>
    <tr><th>Comando Acionador</th><td><code>{comando_acionador}</code></td></tr>
    <tr><th>Localização</th><td><code>{localizacao}</code></td></tr>
  </table>
</section>

<section>
  <h2>Fluxo de Execução</h2>
  <ol class="passos">
    {passos_html}
  </ol>
</section>

<section>
  <h2>Esteira Visual de Blocos</h2>
  <div class="bloco-esteira">
    <div class="esteira-passo"><span class="esteira-tag">Entrada</span><div>{bloco_entrada}</div></div>
    <div class="esteira-passo"><span class="esteira-tag">Processo</span><div>{bloco_processo}</div></div>
    <div class="esteira-passo"><span class="esteira-tag">Trava (Gate)</span><div>{bloco_trava}</div></div>
    <div class="esteira-passo"><span class="esteira-tag">Saída</span><div>{bloco_saida}</div></div>
  </div>
</section>

<section>
  <h2>Defeitos e Limitações</h2>
  <div class="box">
    <ul>
      {defeitos_html}
    </ul>
  </div>

  <div class="alert warning">
    <div class="alert-title">Aviso de Ponto Crítico / Risco</div>
    <div>{alerta_warning}</div>
  </div>

  <div class="alert tip">
    <div class="alert-title">Recomendação Prática de Uso</div>
    <div>{alerta_tip}</div>
  </div>
</section>

</div>
</body>
</html>
"""

def salvar_anatomia_html(caminho_saida: Path, dados: dict) -> None:
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    html = HTML_TEMPLATE.format(**dados)
    caminho_saida.write_text(html, encoding="utf-8")
    print(f"[ANATOMIA HTML] Gerado em: {caminho_saida}")
