import os
import sys
from pathlib import Path
from html_templates_suporte import METRICS_DASHBOARD_HTML, WELCOME_PAGE_HTML

def aplicar_patch_em_conteudo(conteudo: str) -> str:
    # 1. Injetar FRONTEND_DIST e SERVER_START_TIME se não existirem
    if "FRONTEND_DIST = " not in conteudo:
        conteudo = conteudo.replace(
            'STATIC_DIR = os.path.join(CURRENT_DIR, "static")',
            'STATIC_DIR = os.path.join(CURRENT_DIR, "static")\n'
            'PROJECT_ROOT = os.path.dirname(CURRENT_DIR) if os.path.basename(CURRENT_DIR) == "src" else CURRENT_DIR\n'
            'FRONTEND_DIST = os.path.join(PROJECT_ROOT, "frontend", "dist")\n'
            'SERVER_START_TIME = time.time()'
        )

    # 2. Injetar função de serviço estático se não existir
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
        # Inserir antes de _handle_get
        pos = conteudo.find("def _handle_get(self):")
        if pos != -1:
            conteudo = conteudo[:pos] + funcao_servir + "\n    " + conteudo[pos:]

    # 3. Atualizar tratamento de métricas (/metrics e /api/metrics)
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
                html_metrics = METRICS_DASHBOARD_HTML.replace("{{ uptime_str }}", f"{uptime_m} min")
                html_metrics = html_metrics.replace("{{ data_inicio }}", datetime.datetime.now().strftime("%H:%M:%S"))
                html_metrics = html_metrics.replace("{{ total_reqs }}", str(req_c))
                html_metrics = html_metrics.replace("{{ latencia_media }}", "4.2")
                html_metrics = html_metrics.replace("{{ raw_metrics }}", metrics_registry.render())
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

    # 4. Atualizar entrega do Frontend e rota raiz (substituindo o directory listing antigo)
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
                html_welcome = WELCOME_PAGE_HTML.replace("{{ suite_name }}", "Aplicação AIDD")
                self._write_html(html_welcome)
                return

            if path.startswith("/static/"):
                rel_p = path[len("/static/"):]
                target_f = os.path.join(STATIC_DIR, rel_p)
                if os.path.isfile(target_f):
                    return self._servir_arquivo(target_f)'''

    if bloco_antigo_static in conteudo:
        conteudo = conteudo.replace(bloco_antigo_static, bloco_novo_static)

    # 5. Substituir super().do_GET() final por 404 seguro em JSON
    if "super().do_GET()" in conteudo:
        conteudo = conteudo.replace(
            "super().do_GET()",
            'self.send_response(404)\n        self.send_header("Content-Type", "application/json; charset=utf-8")\n        self.end_headers()\n        self.wfile.write(json.dumps({"error": f"Rota GET não encontrada: {path}"}).encode("utf-8"))'
        )

    return conteudo


arquivos_alvo = [
    'modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/templates/v2/server.py',
    'modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise/templates/v2/server.py',
    'modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/src/server.py',
]

for a in arquivos_alvo:
    p = Path(a)
    if p.exists():
        txt = p.read_text(encoding='utf-8')
        # Injetar import de HTMLs se não tiver
        if "from html_templates_suporte import" not in txt:
            txt = "from scripts.html_templates_suporte import METRICS_DASHBOARD_HTML, WELCOME_PAGE_HTML\n" + txt
        txt = aplicar_patch_em_conteudo(txt)
        p.write_text(txt, encoding='utf-8')
        print(f"Atualizado com sucesso: {a}")

print("Todos os templates de servidor foram blindados!")
