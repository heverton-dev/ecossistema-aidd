import os
import sys
from pathlib import Path

METRICS_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Métricas do Sistema — Prometheus Dashboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-body: #f8fafc;
            --surface: #ffffff;
            --border: #e2e8f0;
            --text-title: #0f172a;
            --text-body: #334155;
            --text-muted: #64748b;
            --primary: #0F766E;
            --primary-hover: #0C645D;
            --primary-light: #f0fdfa;
            --success: #16a34a;
            --warning: #d97706;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
            background: var(--bg-body);
            color: var(--text-body);
            line-height: 1.5;
            padding: 32px 24px;
        }
        .container { max-width: 1100px; margin: 0 auto; }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 28px;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border);
        }
        .title-group h1 { font-size: 22px; font-weight: 800; color: var(--text-title); }
        .title-group p { font-size: 13px; color: var(--text-muted); margin-top: 4px; }
        .badge {
            background: var(--primary-light);
            color: var(--primary);
            border: 1px solid var(--primary);
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 600;
        }
        .grid-kpis {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }
        .card-kpi {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.02);
        }
        .kpi-label { font-size: 12px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }
        .kpi-val { font-size: 28px; font-weight: 800; color: var(--text-title); margin: 8px 0 4px; }
        .kpi-sub { font-size: 12px; color: var(--success); font-weight: 500; }
        .panel {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
        }
        .panel h2 { font-size: 16px; font-weight: 700; color: var(--text-title); margin-bottom: 16px; }
        pre.raw-metrics {
            background: #f1f5f9;
            color: #0f172a;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            line-height: 1.6;
            max-height: 380px;
            overflow-y: auto;
        }
        .nav-links { display: flex; gap: 12px; margin-top: 24px; }
        .nav-btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text-title);
            text-decoration: none;
            font-size: 13px;
            font-weight: 600;
            transition: all 0.2s;
        }
        .nav-btn:hover { background: var(--bg-body); border-color: var(--primary); color: var(--primary); }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="title-group">
                <h1>Painel de Métricas & Saúde do Sistema</h1>
                <p>Telemetria de requisições, latência e observabilidade (Prometheus + OpenTelemetry)</p>
            </div>
            <span class="badge">STATUS: OPERACIONAL</span>
        </header>

        <div class="grid-kpis">
            <div class="card-kpi">
                <div class="kpi-label">Uptime do Servidor</div>
                <div class="kpi-val">{{ uptime_str }}</div>
                <div class="kpi-sub">Ativo desde {{ data_inicio }}</div>
            </div>
            <div class="card-kpi">
                <div class="kpi-label">Total de Requisições</div>
                <div class="kpi-val">{{ total_reqs }}</div>
                <div class="kpi-sub">Processadas com sucesso</div>
            </div>
            <div class="card-kpi">
                <div class="kpi-label">Latência Média</div>
                <div class="kpi-val">{{ latencia_media }} ms</div>
                <div class="kpi-sub">P95 &lt; 25ms (FastEngine)</div>
            </div>
            <div class="card-kpi">
                <div class="kpi-label">Taxa de Sucesso</div>
                <div class="kpi-val">100.0%</div>
                <div class="kpi-sub">Zero falhas 5xx</div>
            </div>
        </div>

        <div class="panel">
            <h2>Exportador de Métricas Prometheus (Texto Bruto)</h2>
            <pre class="raw-metrics">{{ raw_metrics }}</pre>
        </div>

        <div class="nav-links">
            <a href="/" class="nav-btn">← Voltar para Aplicação</a>
            <a href="/docs" class="nav-btn">Swagger Studio (/docs)</a>
            <a href="/api/metrics" class="nav-btn">Métricas JSON (/api/metrics)</a>
            <a href="/openapi.json" class="nav-btn">OpenAPI 3.1 Spec</a>
        </div>
    </div>
</body>
</html>
"""

WELCOME_PAGE_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ suite_name }} — Portal de Serviços AIDD</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-body: #f8fafc;
            --surface: #ffffff;
            --border: #e2e8f0;
            --text-title: #0f172a;
            --text-body: #334155;
            --text-muted: #64748b;
            --primary: #0F766E;
            --primary-light: #f0fdfa;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
            background: var(--bg-body);
            color: var(--text-body);
            line-height: 1.5;
            padding: 40px 24px;
        }
        .container { max-width: 900px; margin: 0 auto; }
        .hero {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 36px;
            margin-bottom: 28px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.02);
        }
        .hero h1 { font-size: 26px; font-weight: 800; color: var(--text-title); margin-bottom: 8px; }
        .hero p { font-size: 14px; color: var(--text-muted); margin-bottom: 20px; }
        .instructions {
            background: #f1f5f9;
            border-left: 4px solid var(--primary);
            padding: 16px;
            border-radius: 6px;
            font-size: 13px;
            color: #0f172a;
            margin-top: 16px;
        }
        .instructions code { font-weight: 600; color: var(--primary); }
        .grid-studios {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 16px;
        }
        .card-studio {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            text-decoration: none;
            color: inherit;
            transition: all 0.2s;
        }
        .card-studio:hover {
            border-color: var(--primary);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(15, 118, 110, 0.08);
        }
        .studio-title { font-size: 15px; font-weight: 700; color: var(--text-title); margin-bottom: 4px; }
        .studio-desc { font-size: 12px; color: var(--text-muted); }
    </style>
</head>
<body>
    <div class="container">
        <div class="hero">
            <h1>{{ suite_name }} — Backend Ativo</h1>
            <p>O servidor monolítico modular Python + SQLite WAL está em execução com sucesso (Quarteto Sine Qua Non Dinâmico ativo).</p>
            <div class="instructions">
                <strong>Frontend em Desenvolvimento / Compilação:</strong><br>
                Para rodar a interface de usuário React/Vite com Hot-Reload ou gerar o build estático de produção:<br>
                <code>cd frontend && npm install && npm run build</code> (ou <code>npm run dev</code> para desenvolvimento).
            </div>
        </div>

        <h2 style="font-size: 16px; font-weight: 700; color: var(--text-title); margin-bottom: 16px;">Estúdios Integrados (Quarteto Sine Qua Non):</h2>
        <div class="grid-studios">
            <a href="/docs" class="card-studio">
                <div class="studio-title">📜 Swagger Studio (/docs)</div>
                <div class="studio-desc">Contratos e execução interativa das rotas OpenAPI 3.1.</div>
            </a>
            <a href="/webhook" class="card-studio">
                <div class="studio-title">⚡ Webhook Studio (/webhook)</div>
                <div class="studio-desc">Central de eventos, simulador de disparo e logs HMAC SHA-256.</div>
            </a>
            <a href="/mcp" class="card-studio">
                <div class="studio-title">🤖 MCP Native Studio (/mcp)</div>
                <div class="studio-desc">Ferramentas e recursos do Model Context Protocol para IAs.</div>
            </a>
            <a href="/docs/guia" class="card-studio">
                <div class="studio-title">📖 Guia do Usuário (/docs/guia)</div>
                <div class="studio-desc">Manual técnico completo com arquitetura e diagramas Mermaid.</div>
            </a>
            <a href="/metrics" class="card-studio">
                <div class="studio-title">📈 Painel de Métricas (/metrics)</div>
                <div class="studio-desc">Telemetria em tempo real, latência e coletores Prometheus.</div>
            </a>
            <a href="/openapi.json" class="card-studio">
                <div class="studio-title">📊 OpenAPI Spec (/openapi.json)</div>
                <div class="studio-desc">Especificação pura em JSON 3.1 para integrações externas.</div>
            </a>
        </div>
    </div>
</body>
</html>
"""

print("HTMLs de suporte carregados com sucesso.")
