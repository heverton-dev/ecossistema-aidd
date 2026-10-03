# -*- coding: utf-8 -*-
from pathlib import Path
from aidd_forge.core.mobbin_client import executar_busca

# Busca referência corporativa complexa e moderna em MODO CLARO (LIGHT)
print("[1/3] Buscando tela real corporativa em MODO CLARO no Mobbin...")
res = executar_busca(query="saas b2b analytics dashboard clean light", platform="web", mode="standard", limit=1)
tela = res["screens"][0]

img_url = tela.get("image_url") or tela.get("image", {}).get("url")
app_name = tela.get("app_name", "Stripe / Linear Light")

print(f"      App: {app_name}")
print(f"      Imagem: {img_url}")

# Constrói o benchmark 50/50 em MODO CLARO refinado (padrão Stripe/Linear Light)
html_split_light = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Benchmark Visual — Referência Mobbin vs Geração Autoral (Modo Claro)</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
  <style>
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      background: #f8fafc;
      color: #0f172a;
      font-family: 'Public Sans', -apple-system, sans-serif;
      height: 100vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }}

    /* Topbar do Benchmark */
    .benchmark-header {{
      height: 52px;
      background: #ffffff;
      border-bottom: 1px solid #e2e8f0;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 24px;
      z-index: 100;
    }}

    .benchmark-title {{
      font-size: 13px;
      font-weight: 700;
      color: #0f172a;
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .tag-engine {{
      background: #eff6ff;
      border: 1px solid #bfdbfe;
      color: #2563eb;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 11px;
      font-family: 'JetBrains Mono', monospace;
      font-weight: 600;
    }}

    /* Container 50% / 50% */
    .split-container {{
      flex: 1;
      display: flex;
      width: 100%;
      height: calc(100vh - 52px);
    }}

    .pane {{
      flex: 1;
      height: 100%;
      overflow-y: auto;
      position: relative;
    }}

    .pane-left {{
      border-right: 2px solid #e2e8f0;
      background: #f1f5f9;
    }}

    .pane-right {{
      background: #f8fafc;
    }}

    .pane-badge {{
      position: sticky;
      top: 12px;
      left: 12px;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 700;
      font-family: 'JetBrains Mono', monospace;
      z-index: 50;
      box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }}

    .badge-ref {{
      background: #ffffff;
      border: 1px solid #cbd5e1;
      color: #475569;
    }}

    .badge-gen {{
      background: #ffffff;
      border: 1px solid #3b82f6;
      color: #1d4ed8;
    }}

    .ref-img {{
      width: 100%;
      height: auto;
      display: block;
      padding: 16px;
      border-radius: 8px;
    }}

    /* ==========================================================================
       PAINEL DIREITO: INTERFACE REAL COMPLEXA EM MODO CLARO (ESTILO STRIPE/LINEAR)
       ========================================================================== */
    .app-shell {{
      padding: 28px;
      display: flex;
      flex-direction: column;
      gap: 24px;
    }}

    .sub-topbar {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid #e2e8f0;
      padding-bottom: 18px;
    }}

    .terminal-title h1 {{
      font-size: 24px;
      font-weight: 800;
      color: #0f172a;
      letter-spacing: -0.02em;
    }}

    .terminal-title p {{
      font-size: 13px;
      color: #64748b;
      margin-top: 3px;
    }}

    .terminal-controls {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .btn-outline {{
      background: #ffffff;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      padding: 7px 14px;
      font-size: 12px;
      color: #334155;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s ease;
    }}

    .btn-outline:hover {{
      background: #f8fafc;
      border-color: #94a3b8;
    }}

    .btn-solid {{
      background: #0f172a;
      border: 1px solid #0f172a;
      border-radius: 6px;
      padding: 7px 16px;
      font-size: 12px;
      color: #ffffff;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.15s ease;
    }}

    .btn-solid:hover {{
      background: #1e293b;
    }}

    /* Grid Analítico de 4 Indicadores Estruturais */
    .analytics-grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
    }}

    .stat-card {{
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 18px;
      display: flex;
      flex-direction: column;
      gap: 4px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }}

    .stat-card .label {{
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      font-family: 'JetBrains Mono', monospace;
      color: #64748b;
    }}

    .stat-card .val {{
      font-size: 26px;
      font-weight: 800;
      font-family: 'JetBrains Mono', monospace;
      color: #0f172a;
      letter-spacing: -0.02em;
    }}

    .stat-card .delta {{
      font-size: 12px;
      font-weight: 600;
      font-family: 'JetBrains Mono', monospace;
    }}

    .delta-up {{ color: #059669; }}
    .delta-neutral {{ color: #64748b; }}

    /* Layout Central em 2 Colunas */
    .complex-layout {{
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 16px;
    }}

    .main-table-box {{
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }}

    .box-header {{
      padding: 14px 18px;
      border-bottom: 1px solid #e2e8f0;
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: #f8fafc;
    }}

    .box-title {{
      font-size: 13px;
      font-weight: 700;
      color: #0f172a;
    }}

    table.dataTable {{
      width: 100%;
      border-collapse: collapse;
      text-align: left;
      font-size: 13px;
    }}

    table.dataTable thead th {{
      background: #f8fafc;
      padding: 11px 16px;
      color: #64748b;
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      text-transform: uppercase;
      border-bottom: 1px solid #e2e8f0;
      font-weight: 600;
    }}

    table.dataTable tbody td {{
      padding: 14px 16px;
      border-bottom: 1px solid #f1f5f9;
      color: #334155;
    }}

    table.dataTable tbody tr:hover {{
      background: #f8fafc;
    }}

    /* Lateral: Feed de Telemetria */
    .side-telemetry {{
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 18px;
      display: flex;
      flex-direction: column;
      gap: 14px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }}

    .event-item {{
      border-left: 3px solid #2563eb;
      padding-left: 10px;
      display: flex;
      flex-direction: column;
      gap: 2px;
    }}

    .event-time {{
      font-size: 11px;
      font-family: 'JetBrains Mono', monospace;
      color: #64748b;
    }}

    .event-desc {{
      font-size: 12px;
      font-weight: 600;
      color: #0f172a;
    }}

    .tag-pill {{
      display: inline-flex;
      padding: 3px 8px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 600;
      font-family: 'JetBrains Mono', monospace;
    }}

    .pill-green {{ background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; }}
    .pill-blue {{ background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }}
    .pill-amber {{ background: #fffbeb; color: #b45309; border: 1px solid #fde68a; }}
  </style>
</head>
<body>

  <!-- Topbar do Benchmark -->
  <div class="benchmark-header">
    <div class="benchmark-title">
      <span>BENCHMARK VISUAL AIDD (MODO CLARO)</span>
      <span class="tag-engine">MOBBIN LIGHT vs PRODUÇÃO AUTORAL</span>
    </div>
    <div style="font-size: 12px; color: #64748b; font-family: 'JetBrains Mono', monospace;">
      Inspeção Lado a Lado (50% / 50%)
    </div>
  </div>

  <!-- Área Dividida -->
  <div class="split-container">

    <!-- LADO ESQUERDO: Referência Real do Mobbin -->
    <div class="pane pane-left">
      <div class="pane-badge badge-ref">
        <span>REFERÊNCIA MOBBIN: {app_name.upper()}</span>
      </div>
      <img src="{img_url}" alt="Referência Mobbin" class="ref-img" />
    </div>

    <!-- LADO DIREITO: Sistema Complexo Gerado em Modo Claro -->
    <div class="pane pane-right">
      <div class="pane-badge badge-gen">
        <span>PRODUÇÃO AUTORAL: SOVEREIGN OPERATIONAL TERMINAL</span>
      </div>

      <div class="app-shell">
        <div class="sub-topbar">
          <div class="terminal-title">
            <h1>Despacho & Alocação de Frota</h1>
            <p>Telemetria em tempo real, roteamento neural e auditoria de SLAs</p>
          </div>
          <div class="terminal-controls">
            <button type="button" class="btn-outline">Recalcular Malha</button>
            <button type="button" class="btn-solid">Novo Despacho</button>
          </div>
        </div>

        <!-- 4 Indicadores Estruturais em Modo Claro -->
        <div class="analytics-grid">
          <div class="stat-card">
            <span class="label">Taxa de Conclusão</span>
            <span class="val">99.8%</span>
            <span class="delta delta-up">+1.4% vs meta</span>
          </div>
          <div class="stat-card">
            <span class="label">Rotas Ativas</span>
            <span class="val">58 / 60</span>
            <span class="delta delta-neutral">96.6% alocadas</span>
          </div>
          <div class="stat-card">
            <span class="label">Permanência Média</span>
            <span class="val">3m 12s</span>
            <span class="delta delta-up">-42s economia</span>
          </div>
          <div class="stat-card">
            <span class="label">Volume Liquidado</span>
            <span class="val">R$ 148.920</span>
            <span class="delta delta-up">100% conciliado</span>
          </div>
        </div>

        <!-- Layout Composto: Tabela + Telemetria -->
        <div class="complex-layout">

          <div class="main-table-box">
            <div class="box-header">
              <span class="box-title">Matriz Transacional de Rotas</span>
              <span style="font-size: 11px; color: #64748b; font-family: 'JetBrains Mono', monospace;">58 nós auditados</span>
            </div>

            <table class="dataTable">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>MOTORISTA</th>
                  <th>ZONA</th>
                  <th>PARADAS</th>
                  <th>ESTADO</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td style="font-family: 'JetBrains Mono', monospace; font-weight: 700; color: #0f172a;">RT-901</td>
                  <td><strong>Carlos Silva</strong> (Lisboa)</td>
                  <td>Lisboa Centro (1000)</td>
                  <td style="font-family: 'JetBrains Mono', monospace;">38 / 40</td>
                  <td><span class="tag-pill pill-green">Janela Cumprida</span></td>
                </tr>
                <tr>
                  <td style="font-family: 'JetBrains Mono', monospace; font-weight: 700; color: #0f172a;">RT-902</td>
                  <td><strong>Manuel Antunes</strong> (Porto)</td>
                  <td>Porto Boavista (4000)</td>
                  <td style="font-family: 'JetBrains Mono', monospace;">22 / 35</td>
                  <td><span class="tag-pill pill-blue">Em Trânsito</span></td>
                </tr>
                <tr>
                  <td style="font-family: 'JetBrains Mono', monospace; font-weight: 700; color: #0f172a;">RT-903</td>
                  <td><strong>Tiago Fernandes</strong> (Coimbra)</td>
                  <td>Coimbra Polo II (3000)</td>
                  <td style="font-family: 'JetBrains Mono', monospace;">14 / 15</td>
                  <td><span class="tag-pill pill-amber">Atenção Tráfego</span></td>
                </tr>
                <tr>
                  <td style="font-family: 'JetBrains Mono', monospace; font-weight: 700; color: #0f172a;">RT-904</td>
                  <td><strong>Rui Barbosa</strong> (Braga)</td>
                  <td>Braga Sé (4700)</td>
                  <td style="font-family: 'JetBrains Mono', monospace;">29 / 30</td>
                  <td><span class="tag-pill pill-green">Janela Cumprida</span></td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Feed de Telemetria Lateral -->
          <div class="side-telemetry">
            <div style="font-size: 13px; font-weight: 700; color: #0f172a; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;">
              Fluxo de Eventos em Tempo Real
            </div>

            <div class="event-item">
              <span class="event-time">14:32:05 · RT-901</span>
              <span class="event-desc">Parada 38 confirmada via chave biométrica</span>
            </div>

            <div class="event-item" style="border-color: #f59e0b;">
              <span class="event-time">14:30:11 · RT-903</span>
              <span class="event-desc">Alerta de congestionamento em A1 Norte (+8m)</span>
            </div>

            <div class="event-item" style="border-color: #10b981;">
              <span class="event-time">14:28:44 · RT-904</span>
              <span class="event-desc">Liquidação de fatura automática via webhook</span>
            </div>
          </div>

        </div>

      </div>
    </div>

  </div>

</body>
</html>
"""

arquivo_comparativo = Path(r"C:\Users\trcnologia\Desktop\wt_impeccable_mobbin\componentes\compartilhado\mcps\mobbin_mcp\comparativo_benchmark.html")
arquivo_comparativo.write_text(html_split_light, encoding="utf-8")
print(f"[3/3] Benchmark em MODO CLARO gerado com sucesso: {arquivo_comparativo}")
