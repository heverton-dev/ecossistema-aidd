import http.server, socketserver, json, urllib.parse, os, sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import Database
from core.events import EventBus
from core.openapi import RouteRegistry
from core.webhooks import WebhookDispatcher

# Import dos Módulos Verticais
from modules.auth.backend.models import init_schema as init_auth_schema
from modules.auth.backend.services import AuthService
from modules.auth.backend.routes import registrar_rotas as reg_auth_routes

from modules.assinaturas.backend.models import init_schema as init_ass_schema
from modules.assinaturas.backend.services import AssinaturasService
from modules.assinaturas.backend.routes import registrar_rotas as reg_ass_routes

from modules.cursos.backend.models import init_schema as init_cur_schema
from modules.cursos.backend.services import CursosService
from modules.cursos.backend.routes import registrar_rotas as reg_cur_routes

from modules.progresso.backend.models import init_schema as init_prog_schema
from modules.progresso.backend.services import ProgressoService
from modules.progresso.backend.routes import registrar_rotas as reg_prog_routes

PORT = 3000
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
db = Database(f"sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'banco_membros.db')}")
events = EventBus()
webhook_dispatcher = WebhookDispatcher(db)

# Event-Driven Webhook Dispatcher para n8n
events.on("usuario_cadastrado", lambda d: webhook_dispatcher.disparar("aluno.cadastrado", d))
events.on("assinatura_ativada", lambda d: webhook_dispatcher.disparar("assinatura.ativada", d))
events.on("progresso_atualizado", lambda d: webhook_dispatcher.disparar("aula.concluida", d))

# 1. Inicializar Schemas
with db.get_connection() as conn:
    init_auth_schema(conn)
    init_ass_schema(conn)
    init_cur_schema(conn)
    init_prog_schema(conn)
    conn.execute("CREATE TABLE IF NOT EXISTS configuracoes (chave TEXT PRIMARY KEY, valor TEXT NOT NULL);")
    conn.commit()

auth_svc = AuthService(db, events)
ass_svc = AssinaturasService(db, events)
cursos_svc = CursosService(db, events)
prog_svc = ProgressoService(db, events)

ass_svc.seed_planos()
cursos_svc.seed_iniciais()

# Seed admin de teste
auth_svc.cadastrar("Heverton Peres", "admin@aidd.com", "123456")
cursos_svc.matricular(1, 1)

# 2. Registrar Rotas OpenAPI
registry = RouteRegistry()
reg_auth_routes(registry, auth_svc)
reg_ass_routes(registry, ass_svc)
reg_cur_routes(registry, cursos_svc)
reg_prog_routes(registry, prog_svc)

@registry.post("/api/admin/salvar-webhook", summary="Configura URL de Webhook para automação no n8n", tags=["Configuração"])
def post_salvar_webhook(data):
    url = data.get("webhook_url", "")
    with db.get_connection() as conn:
        conn.execute("INSERT OR REPLACE INTO configuracoes (chave, valor) VALUES ('webhook_url', ?)", (url,))
        conn.commit()
    return {"sucesso": True, "webhook_url": url, "mensagem": "Webhook configurado com sucesso para automações n8n!"}

class PlatformHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        if path == "/docs/guia":
            with open(os.path.join(STATIC_DIR, "docs.html"), "r", encoding="utf-8") as df:
                self._send_html(df.read())
        elif path == "/docs":
            html = registry.get_swagger_html("Plataforma de Membros & Assinaturas — Swagger API")
            self._send_html(html)
        elif path == "/openapi.json":
            spec = registry.generate_openapi_json("Plataforma de Assinaturas API", "2.0.0")
            self._send_json(spec)
        elif path in registry.routes["GET"]:
            handler = registry.routes["GET"][path]
            self._send_json(handler(params))
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

        if parsed.path in registry.routes["POST"]:
            handler = registry.routes["POST"][parsed.path]
            self._send_json(handler(data))
        else:
            self.send_error(404, "Endpoint não encontrado")

    def _send_json(self, data, status=200):
        res = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Content-Length", str(len(res)))
        self.end_headers()
        self.wfile.write(res)

    def _send_html(self, html):
        res = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(res)))
        self.end_headers()
        self.wfile.write(res)

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

if __name__ == "__main__":
    server = ThreadedHTTPServer(("", PORT), PlatformHandler)
    print(f"[OK] Plataforma de Membros & Assinaturas rodando em: http://localhost:{PORT}")
    print(f"[OK] Swagger Docs em: http://localhost:{PORT}/docs")
    server.serve_forever()
