from pathlib import Path

def consertar_j2(caminho: Path):
    txt = caminho.read_text(encoding='utf-8')
    # Substituir os blocos HTML inline por strings limpas com {% raw %} ou sem chaves duplas
    antigo = '''                html_metrics = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Métricas do Sistema — Prometheus Dashboard</title>
    <style>
        :root {{ --bg: #f8fafc; --surface: #ffffff; --border: #e2e8f0; --title: #0f172a; --text: #334155; --primary: #0F766E; }}
        body {{ font-family: system-ui, sans-serif; background: var(--bg); color: var(--text); padding: 32px 20px; max-width: 1000px; margin: 0 auto; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 16px; margin-bottom: 24px; }}
        .badge {{ background: #f0fdfa; color: var(--primary); border: 1px solid var(--primary); padding: 4px 10px; border-radius: 9999px; font-weight: 600; font-size: 12px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; }}
        .card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }}
        .val {{ font-size: 26px; font-weight: 800; color: var(--title); margin: 6px 0; }}
        pre {{ background: #f1f5f9; padding: 16px; border-radius: 8px; border: 1px solid var(--border); font-family: monospace; font-size: 12px; max-height: 350px; overflow-y: auto; }}
        .nav {{ display: flex; gap: 12px; margin-top: 20px; }}
        .btn {{ padding: 8px 14px; border: 1px solid var(--border); border-radius: 8px; background: #fff; text-decoration: none; color: var(--title); font-weight: 600; font-size: 13px; }}
    </style>
</head>
<body>
    <div class="header">
        <div><h1 style="font-size:22px;color:#0f172a;">Painel de Métricas & Saúde do Sistema</h1><p style="font-size:13px;color:#64748b;">Telemetria ativa em tempo real</p></div>
        <span class="badge">STATUS: OPERACIONAL</span>
    </div>
    <div class="grid">
        <div class="card"><div style="font-size:12px;color:#64748b;">UPTIME</div><div class="val">{uptime_m} min</div></div>
        <div class="card"><div style="font-size:12px;color:#64748b;">REQUISIÇÕES</div><div class="val">{req_c}</div></div>
        <div class="card"><div style="font-size:12px;color:#64748b;">LATÊNCIA P95</div><div class="val">&lt; 15ms</div></div>
        <div class="card"><div style="font-size:12px;color:#64748b;">DISPONIBILIDADE</div><div class="val">100.0%</div></div>
    </div>
    <div class="card">
        <h2 style="font-size:15px;margin-bottom:12px;">Exportador Prometheus (Texto Bruto)</h2>
        <pre>{metrics_registry.render()}</pre>
    </div>
    <div class="nav">
        <a href="/" class="btn">← Voltar à Aplicação</a>
        <a href="/docs" class="btn">Swagger Studio (/docs)</a>
        <a href="/api/metrics" class="btn">Métricas JSON (/api/metrics)</a>
    </div>
</body>
</html>"""'''

    novo = '''                {% raw %}html_metrics = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Métricas do Sistema — Prometheus Dashboard</title>
    <style>
        :root { --bg: #f8fafc; --surface: #ffffff; --border: #e2e8f0; --title: #0f172a; --text: #334155; --primary: #0F766E; }
        body { font-family: system-ui, sans-serif; background: var(--bg); color: var(--text); padding: 32px 20px; max-width: 1000px; margin: 0 auto; }
        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 16px; margin-bottom: 24px; }
        .badge { background: #f0fdfa; color: var(--primary); border: 1px solid var(--primary); padding: 4px 10px; border-radius: 9999px; font-weight: 600; font-size: 12px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; }
        .card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }
        .val { font-size: 26px; font-weight: 800; color: var(--title); margin: 6px 0; }
        pre { background: #f1f5f9; padding: 16px; border-radius: 8px; border: 1px solid var(--border); font-family: monospace; font-size: 12px; max-height: 350px; overflow-y: auto; }
        .nav { display: flex; gap: 12px; margin-top: 20px; }
        .btn { padding: 8px 14px; border: 1px solid var(--border); border-radius: 8px; background: #fff; text-decoration: none; color: var(--title); font-weight: 600; font-size: 13px; }
    </style>
</head>
<body>
    <div class="header">
        <div><h1 style="font-size:22px;color:#0f172a;">Painel de Métricas & Saúde do Sistema</h1><p style="font-size:13px;color:#64748b;">Telemetria ativa em tempo real</p></div>
        <span class="badge">STATUS: OPERACIONAL</span>
    </div>
    <div class="grid">
        <div class="card"><div style="font-size:12px;color:#64748b;">UPTIME</div><div class="val">{uptime_m} min</div></div>
        <div class="card"><div style="font-size:12px;color:#64748b;">REQUISIÇÕES</div><div class="val">{req_c}</div></div>
        <div class="card"><div style="font-size:12px;color:#64748b;">LATÊNCIA P95</div><div class="val">&lt; 15ms</div></div>
        <div class="card"><div style="font-size:12px;color:#64748b;">DISPONIBILIDADE</div><div class="val">100.0%</div></div>
    </div>
    <div class="card">
        <h2 style="font-size:15px;margin-bottom:12px;">Exportador Prometheus (Texto Bruto)</h2>
        <pre>{metrics_registry.render()}</pre>
    </div>
    <div class="nav">
        <a href="/" class="btn">← Voltar à Aplicação</a>
        <a href="/docs" class="btn">Swagger Studio (/docs)</a>
        <a href="/api/metrics" class="btn">Métricas JSON (/api/metrics)</a>
    </div>
</body>
</html>"""{% endraw %}'''

    if antigo in txt:
        txt = txt.replace(antigo, novo)
        print("Substituído bloco antigo de html_metrics com raw.")

    antigo_welcome = '''                html_welcome = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ cookiecutter.suite_name }} — Portal de Serviços AIDD</title>
    <style>
        :root {{ --bg: #f8fafc; --surface: #ffffff; --border: #e2e8f0; --title: #0f172a; --text: #334155; --primary: #0F766E; }}
        body {{ font-family: system-ui, sans-serif; background: var(--bg); color: var(--text); padding: 40px 20px; max-width: 900px; margin: 0 auto; }}
        .hero {{ background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 32px; margin-bottom: 24px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; }}
        .card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px; text-decoration: none; color: inherit; transition: all 0.2s; }}
        .card:hover {{ border-color: var(--primary); transform: translateY(-2px); }}
        .title {{ font-size: 15px; font-weight: 700; color: var(--title); margin-bottom: 4px; }}
        .desc {{ font-size: 12px; color: #64748b; }}
    </style>
</head>
<body>
    <div class="hero">
        <h1 style="font-size:24px;font-weight:800;color:#0f172a;margin-bottom:8px;">{{ cookiecutter.suite_name }} — Backend Ativo</h1>
        <p style="font-size:14px;color:#64748b;margin-bottom:16px;">O servidor monolítico modular Python + SQLite WAL está em execução com o Quarteto Dinâmico ativo.</p>
        <div style="background:#f1f5f9;border-left:4px solid var(--primary);padding:12px;border-radius:6px;font-size:13px;">
            <strong>Frontend em Desenvolvimento / Compilação:</strong><br>
            Execute <code>cd frontend && npm install && npm run build</code> para gerar a UI de produção servida na raiz.
        </div>
    </div>
    <div class="grid">
        <a href="/docs" class="card"><div class="title">📜 Swagger Studio (/docs)</div><div class="desc">Contratos OpenAPI 3.1</div></a>
        <a href="/webhook" class="card"><div class="title">⚡ Webhook Studio (/webhook)</div><div class="desc">Eventos e HMAC SHA-256</div></a>
        <a href="/mcp" class="card"><div class="title">🤖 MCP Studio (/mcp)</div><div class="desc">Model Context Protocol</div></a>
        <a href="/docs/guia" class="card"><div class="title">📖 Guia do Usuário (/docs/guia)</div><div class="desc">Documentação técnica</div></a>
        <a href="/metrics" class="card"><div class="title">📈 Métricas (/metrics)</div><div class="desc">Dashboard Prometheus</div></a>
        <a href="/openapi.json" class="card"><div class="title">📊 OpenAPI Spec (/openapi.json)</div><div class="desc">JSON OpenAPI 3.1</div></a>
    </div>
</body>
</html>"""'''

    novo_welcome = '''                {% raw %}html_welcome = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% endraw %}{{ cookiecutter.suite_name }}{% raw %} — Portal de Serviços AIDD</title>
    <style>
        :root { --bg: #f8fafc; --surface: #ffffff; --border: #e2e8f0; --title: #0f172a; --text: #334155; --primary: #0F766E; }
        body { font-family: system-ui, sans-serif; background: var(--bg); color: var(--text); padding: 40px 20px; max-width: 900px; margin: 0 auto; }
        .hero { background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 32px; margin-bottom: 24px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; }
        .card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px; text-decoration: none; color: inherit; transition: all 0.2s; }
        .card:hover { border-color: var(--primary); transform: translateY(-2px); }
        .title { font-size: 15px; font-weight: 700; color: var(--title); margin-bottom: 4px; }
        .desc { font-size: 12px; color: #64748b; }
    </style>
</head>
<body>
    <div class="hero">
        <h1 style="font-size:24px;font-weight:800;color:#0f172a;margin-bottom:8px;">{% endraw %}{{ cookiecutter.suite_name }}{% raw %} — Backend Ativo</h1>
        <p style="font-size:14px;color:#64748b;margin-bottom:16px;">O servidor monolítico modular Python + SQLite WAL está em execução com o Quarteto Dinâmico ativo.</p>
        <div style="background:#f1f5f9;border-left:4px solid var(--primary);padding:12px;border-radius:6px;font-size:13px;">
            <strong>Frontend em Desenvolvimento / Compilação:</strong><br>
            Execute <code>cd frontend && npm install && npm run build</code> para gerar a UI de produção servida na raiz.
        </div>
    </div>
    <div class="grid">
        <a href="/docs" class="card"><div class="title">📜 Swagger Studio (/docs)</div><div class="desc">Contratos OpenAPI 3.1</div></a>
        <a href="/webhook" class="card"><div class="title">⚡ Webhook Studio (/webhook)</div><div class="desc">Eventos e HMAC SHA-256</div></a>
        <a href="/mcp" class="card"><div class="title">🤖 MCP Studio (/mcp)</div><div class="desc">Model Context Protocol</div></a>
        <a href="/docs/guia" class="card"><div class="title">📖 Guia do Usuário (/docs/guia)</div><div class="desc">Documentação técnica</div></a>
        <a href="/metrics" class="card"><div class="title">📈 Métricas (/metrics)</div><div class="desc">Dashboard Prometheus</div></a>
        <a href="/openapi.json" class="card"><div class="title">📊 OpenAPI Spec (/openapi.json)</div><div class="desc">JSON OpenAPI 3.1</div></a>
    </div>
</body>
</html>"""{% endraw %}'''

    if antigo_welcome in txt:
        txt = txt.replace(antigo_welcome, novo_welcome)
        print("Substituído bloco antigo de html_welcome com raw.")

    caminho.write_text(txt, encoding='utf-8')
    print(f"Template corrigido: {caminho}")

for c in [
    Path('modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/templates/cookiecutter-scaffold/suite/{{cookiecutter.suite_slug}}/server.py.j2'),
    Path('modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise/templates/cookiecutter-scaffold/suite/{{cookiecutter.suite_slug}}/server.py.j2')
]:
    if c.exists():
        consertar_j2(c)
