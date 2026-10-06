import http.server, socketserver, json, urllib.parse, os, sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services import LojaService

PORT = 3000
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "loja.db")
service = LojaService(db_path)
service.seed_dados_iniciais()

class StoreHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        if path == "/api/config":
            self._send_json(service.obter_configuracoes())
        elif path == "/api/produtos":
            cat = params.get("categoria", [None])[0]
            busca = params.get("busca", [None])[0]
            admin = params.get("admin", ["0"])[0] == "1"
            produtos = service.listar_produtos(cat, busca, apenas_ativos=not admin)
            self._send_json(produtos)
        elif path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
        elif path == "/" or path == "":
            self.path = "/index.html"
            super().do_GET()
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        data = json.loads(body) if body else {}

        if parsed.path == "/api/login-admin":
            res = service.autenticar_admin(data.get("email", ""), data.get("senha", ""))
            self._send_json(res)
        elif parsed.path == "/api/checkout-whatsapp":
            res = service.gerar_link_whatsapp(data.get("itens", []), data.get("cliente_nome", "Cliente"))
            self._send_json(res)
        elif parsed.path == "/api/admin/salvar-produto":
            res = service.salvar_produto(data)
            self._send_json(res)
        elif parsed.path == "/api/admin/deletar-produto":
            res = service.deletar_produto(int(data.get("id", 0)))
            self._send_json(res)
        elif parsed.path == "/api/admin/salvar-config":
            res = service.salvar_configuracoes(data)
            self._send_json(res)
        else:
            self.send_error(404, "Endpoint nao encontrado")

    def _send_json(self, data, status=200):
        res = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(res)))
        self.end_headers()
        self.wfile.write(res)

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

def start_server():
    server = ThreadedHTTPServer(("", PORT), StoreHandler)
    print(f"[OK] Loja Digital rodando com sucesso em: http://localhost:{PORT}")
    server.serve_forever()

if __name__ == "__main__":
    start_server()
