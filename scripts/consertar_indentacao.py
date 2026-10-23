from pathlib import Path

def consertar_indentacao(caminho: Path):
    txt = caminho.read_text(encoding='utf-8')
    antigo = '''        def _servir_arquivo(self, caminho_arquivo: str):
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
            self.wfile.write(json.dumps({"error": f"Falha na leitura do arquivo: {e}"}).encode("utf-8"))'''

    novo = '''    def _servir_arquivo(self, caminho_arquivo: str):
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
            self.wfile.write(json.dumps({"error": f"Falha na leitura do arquivo: {e}"}).encode("utf-8"))'''

    if antigo in txt:
        txt = txt.replace(antigo, novo)
        caminho.write_text(txt, encoding='utf-8')
        print(f"Indentação corrigida em {caminho}")

for c in [
    Path('modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/templates/cookiecutter-scaffold/suite/{{cookiecutter.suite_slug}}/server.py.j2'),
    Path('modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise/templates/cookiecutter-scaffold/suite/{{cookiecutter.suite_slug}}/server.py.j2'),
    Path('modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/templates/v2/server.py'),
    Path('modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise/templates/v2/server.py'),
    Path('modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/src/server.py')
]:
    if c.exists():
        consertar_indentacao(c)
