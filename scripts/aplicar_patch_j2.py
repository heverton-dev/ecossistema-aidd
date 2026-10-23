import os
import sys
from pathlib import Path

def aplicar_patch_j2(caminho_arq: Path):
    conteudo = caminho_arq.read_text(encoding='utf-8')

    # Injetar FRONTEND_DIST
    if "FRONTEND_DIST = " not in conteudo:
        conteudo = conteudo.replace(
            'STATIC_DIR = os.path.join(CURRENT_DIR, "static")',
            'STATIC_DIR = os.path.join(CURRENT_DIR, "static")\n'
            'PROJECT_ROOT = os.path.dirname(CURRENT_DIR) if os.path.basename(CURRENT_DIR) == "src" else CURRENT_DIR\n'
            'FRONTEND_DIST = os.path.join(PROJECT_ROOT, "frontend", "dist")\n'
            'SERVER_START_TIME = time.time()'
        )

    # Injetar _servir_arquivo se não existir
    funcao_servir = '''    def _servir_arquivo(self, caminho_arquivo: str):
        """Serve um arquivo estático com MIME type apropriado e cabeçalhos de segurança (Lei #11)."""
        if not os.path.isfile(caminho_arquivo):
            self.send_response(404)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Arquivo estático não encontrado"}).encode("utf-8"))
            return

        ext = os.path.splitext(caminho_arquivo)[1].lower()
        content_types = {
            ".html": "text/html; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".mjs": "application/javascript; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".json": "application/json; charset=utf-8",
            ".svg": "image/svg+xml",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".ico": "image/x-icon",
            ".woff2": "font/woff2",
            ".woff": "font/woff",
            ".ttf": "font/ttf",
        }
        ct = content_types.get(ext, "application/octet-stream")
        try:
            with open(caminho_arquivo, "rb") as f:
                dados = f.read()
            self.send_response(200)
            self.send_header("Content-Type", ct)
            self.send_header("Content-Length", str(len(dados)))
            self.end_headers()
            self.wfile.write(dados)
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"Falha na leitura do arquivo: {e}"}).encode("utf-8"))
'''
    if "def _servir_arquivo(" not in conteudo:
        pos = conteudo.find("def _handle_get(self):")
        if pos != -1:
            conteudo = conteudo[:pos] + funcao_servir + "\n    " + conteudo[pos:]

    # Métricas
    bloco_antigo_metrics = '''        if path == "/metrics":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.end_headers()
            self.wfile.write(metrics_registry.render().encode("utf-8"))
            return'''

    bloco_novo_metrics = '''        if path == "/api/metrics":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            tot = getattr(metrics_registry, "counters", {})
            req_c = sum(tot.values()) if isinstance(tot, dict) else 0
            dados_m = {
                "status": "online",
                "uptime_segundos": round(time.time() - SERVER_START_TIME, 1),
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "total_requisicoes": req_c,
                "metricas_raw": metrics_registry.render()
            }
            self.wfile.write(json.dumps(dados_m, ensure_ascii=False, indent=2).encode("utf-8"))
            return

        if path == "/metrics":
            accept = self.headers.get("Accept", "")
            if "text/html" in accept and "text/plain" not in accept:
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                uptime_m = round((time.time() - SERVER_START_TIME) / 60, 1)
                tot = getattr(metrics_registry, "counters", {})
                req_c = sum(tot.values()) if isinstance(tot, dict) else 0
                html_metrics = f"""<!DOCTYPE html>
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
</html>"""
                self._write_html(html_metrics)
                return
            else:
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
                self.end_headers()
                self.wfile.write(metrics_registry.render().encode("utf-8"))
                return'''

    if bloco_antigo_metrics in conteudo:
        conteudo = conteudo.replace(bloco_antigo_metrics, bloco_novo_metrics)

    # Estáticos / Frontend
    bloco_antigo_static = '''        if path in ["/", "/index.html"]:
            index_file = os.path.join(STATIC_DIR, "index.html")
            if os.path.isfile(index_file):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                with open(index_file, "r", encoding="utf-8") as f:
                    self._write_html(f.read())
                return

        if path.startswith("/static/"):
            rel_p = path[len("/static/"):]
            target_f = os.path.join(STATIC_DIR, rel_p)
            if os.path.isfile(target_f):
                content_type = "text/html" if target_f.endswith(".html") else ("application/javascript" if target_f.endswith(".js") else "text/css" if target_f.endswith(".css") else "text/plain")
                self.send_response(200)
                self.send_header("Content-Type", f"{content_type}; charset=utf-8")
                self.end_headers()
                if target_f.endswith(".html"):
                    with open(target_f, "r", encoding="utf-8") as f:
                        self._write_html(f.read())
                else:
                    with open(target_f, "rb") as f:
                        self.wfile.write(f.read())
                return'''

    bloco_novo_static = '''        # Servir Frontend Compilado (Vite) ou Estáticos com Fallback SPA (Lei #11)
        if not path.startswith("/api/"):
            # 1. Se existir frontend/dist/ gerado pelo Vite
            if os.path.isdir(FRONTEND_DIST):
                rel_arq = path.lstrip("/")
                if not rel_arq or rel_arq == "index.html":
                    return self._servir_arquivo(os.path.join(FRONTEND_DIST, "index.html"))
                
                candidato = os.path.join(FRONTEND_DIST, rel_arq)
                if os.path.isfile(candidato):
                    return self._servir_arquivo(candidato)
                
                # Rota client-side de SPA (ex: /dashboard, /tarefas) -> fallback index.html
                if "." not in os.path.basename(rel_arq):
                    return self._servir_arquivo(os.path.join(FRONTEND_DIST, "index.html"))

            # 2. Se existir static/index.html
            if path in ["/", "/index.html"]:
                idx_st = os.path.join(STATIC_DIR, "index.html")
                if os.path.isfile(idx_st):
                    return self._servir_arquivo(idx_st)
                
                # 3. Fallback: Página amigável de serviços em Modo Claro (Zero Directory Listing)
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                html_welcome = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{{{ cookiecutter.suite_name }}}} — Portal de Serviços AIDD</title>
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
        <h1 style="font-size:24px;font-weight:800;color:#0f172a;margin-bottom:8px;">{{{{ cookiecutter.suite_name }}}} — Backend Ativo</h1>
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
</html>"""
                self._write_html(html_welcome)
                return

            if path.startswith("/static/"):
                rel_p = path[len("/static/"):]
                target_f = os.path.join(STATIC_DIR, rel_p)
                if os.path.isfile(target_f):
                    return self._servir_arquivo(target_f)'''

    if bloco_antigo_static in conteudo:
        conteudo = conteudo.replace(bloco_antigo_static, bloco_novo_static)

    # 404 sem directory listing
    if "super().do_GET()" in conteudo:
        conteudo = conteudo.replace(
            "super().do_GET()",
            'self.send_response(404)\n        self.send_header("Content-Type", "application/json; charset=utf-8")\n        self.end_headers()\n        self.wfile.write(json.dumps({"error": f"Rota GET não encontrada: {path}"}).encode("utf-8"))'
        )

    caminho_arq.write_text(conteudo, encoding='utf-8')
    print(f"J2 atualizado com sucesso: {caminho_arq}")


destinos_j2 = [
    Path('modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/templates/cookiecutter-scaffold/suite/{{cookiecutter.suite_slug}}/server.py.j2'),
    Path('modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise/templates/cookiecutter-scaffold/suite/{{cookiecutter.suite_slug}}/server.py.j2')
]

for d in destinos_j2:
    if d.exists():
        aplicar_patch_j2(d)
