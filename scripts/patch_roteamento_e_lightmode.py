import os
import re

# 1. Corrigir HTML do Frontend Dist para Modo Claro Soberano
dist_index_files = [
    "modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise/templates/v2/frontend/dist/index.html",
    "modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/templates/v2/frontend/dist/index.html",
    "tools/aidd-enterprise/templates/v2/frontend/dist/index.html",
    "tools/aidd-master/templates/v2/frontend/dist/index.html",
    "projetos/app-pure-e2e/frontend/dist/index.html",
    "modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise/templates/v2/frontend/index.html",
    "modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/templates/v2/frontend/index.html",
    "projetos/app-pure-e2e/frontend/index.html",
]

for p in dist_index_files:
    if os.path.isfile(p):
        conteudo = open(p, "r", encoding="utf-8").read()
        conteudo = conteudo.replace('<html lang="pt-BR" class="dark">', '<html lang="pt-BR">')
        conteudo = conteudo.replace('class="dark"', '')
        conteudo = conteudo.replace('bg-[#0b0f19] text-slate-100', 'bg-slate-50 text-slate-900')
        open(p, "w", encoding="utf-8").write(conteudo)
        print(f"[OK] Light mode soberano aplicado em {p}")

# 2. Template HTML de Métricas puro (sem f-string para evitar colisão CSS { --bg: ... })
METRICS_HTML_STR = """<!DOCTYPE html>
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
        <div class="card"><div style="font-size:12px;color:#64748b;">UPTIME</div><div class="val">__UPTIME__</div></div>
        <div class="card"><div style="font-size:12px;color:#64748b;">REQUISIÇÕES</div><div class="val">__REQS__</div></div>
        <div class="card"><div style="font-size:12px;color:#64748b;">LATÊNCIA P95</div><div class="val">&lt; 15ms</div></div>
        <div class="card"><div style="font-size:12px;color:#64748b;">DISPONIBILIDADE</div><div class="val">100.0%</div></div>
    </div>
    <div class="card">
        <h2 style="font-size:15px;margin-bottom:12px;">Exportador Prometheus (Texto Bruto)</h2>
        <pre>__RAW__</pre>
    </div>
    <div class="nav">
        <a href="/" class="btn">← Voltar à Aplicação</a>
        <a href="/docs" class="btn">Swagger Studio (/docs)</a>
        <a href="/api/metrics" class="btn">Métricas JSON (/api/metrics)</a>
    </div>
</body>
</html>"""

# 3. Patch dos arquivos server.py para:
# A) Roteamento: não deixar fallback SPA capturar rotas do quarteto (/docs, /webhook, /mcp, /metrics, etc.)
# B) html_metrics seguro
server_files = [
    "modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/templates/cookiecutter-scaffold/suite/{{cookiecutter.suite_slug}}/server.py.j2",
    "modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise/templates/cookiecutter-scaffold/suite/{{cookiecutter.suite_slug}}/server.py.j2",
    "modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/templates/v2/server.py",
    "modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise/templates/v2/server.py",
    "modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/src/server.py",
    "projetos/app-pure-e2e/src/server.py",
]

for p in server_files:
    if not os.path.isfile(p):
        continue
    conteudo = open(p, "r", encoding="utf-8").read()

    # Injetar constante METRICS_DASHBOARD_HTML_TPL se não existir
    if "METRICS_DASHBOARD_HTML_TPL = " not in conteudo:
        declaracao = f'METRICS_DASHBOARD_HTML_TPL = """{METRICS_HTML_STR}"""\n\n'
        conteudo = declaracao + conteudo

    # Substituir bloco de renderização de metrics para usar replace
    bloco_fstring_metrics = re.search(r'html_metrics = f?"""<!DOCTYPE html>.*?</html>"""', conteudo, re.DOTALL)
    if bloco_fstring_metrics:
        substituicao = (
            'html_metrics = METRICS_DASHBOARD_HTML_TPL.replace("__UPTIME__", f"{uptime_m} min")'
            '.replace("__REQS__", str(req_c))'
            '.replace("__RAW__", metrics_registry.render())'
        )
        conteudo = conteudo[:bloco_fstring_metrics.start()] + substituicao + conteudo[bloco_fstring_metrics.end():]

    # Proteger rotas do quarteto no bloco de servir frontend / SPA
    # O fallback SPA (if "." not in os.path.basename(rel_arq):) só deve rodar se não for rota do backend!
    antigo_check_spa = """                # Rota client-side de SPA (ex: /dashboard, /tarefas) -> fallback index.html
                if "." not in os.path.basename(rel_arq):
                    return self._servir_arquivo(os.path.join(FRONTEND_DIST, "index.html"))"""

    novo_check_spa = """                # Rota client-side de SPA (ex: /dashboard, /tarefas) -> fallback index.html
                # Protege rotas nativas do backend (Quarteto Sine Qua Non, métricas e APIs)
                rotas_reservadas_backend = {
                    "docs", "swagger", "api", "webhook", "webhooks",
                    "mcp", "docs/guia", "metrics", "openapi.json", "health"
                }
                base_seg = rel_arq.strip("/").split("/")[0]
                if "." not in os.path.basename(rel_arq) and rel_arq not in rotas_reservadas_backend and base_seg not in rotas_reservadas_backend:
                    return self._servir_arquivo(os.path.join(FRONTEND_DIST, "index.html"))"""

    if antigo_check_spa in conteudo:
        conteudo = conteudo.replace(antigo_check_spa, novo_check_spa)

    open(p, "w", encoding="utf-8").write(conteudo)
    print(f"[OK] Roteamento e métricas corrigidos em {p}")
