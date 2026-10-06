import http.server, socketserver, json, urllib.parse, os, sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import Database
from core.events import EventBus
from core.openapi import RouteRegistry
from core.webhooks import WebhookDispatcher
from modules.contas.backend.models import init_schema as init_contas
from modules.contas.backend.services import ContasService

PORT = 3002
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
db = Database(f"sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'erp.db')}")
events = EventBus()
webhook_dispatcher = WebhookDispatcher(db)

# Webhooks n8n
events.on("conta_criada", lambda d: webhook_dispatcher.disparar("financeiro.lancamento_criado", d))
events.on("conta_atualizada", lambda d: webhook_dispatcher.disparar("financeiro.lancamento_atualizado", d))
events.on("conta_status_alterado", lambda d: webhook_dispatcher.disparar("financeiro.status_alterado", d))
events.on("conta_excluida", lambda d: webhook_dispatcher.disparar("financeiro.lancamento_excluido", d))

with db.get_connection() as conn:
    init_contas(conn)
    conn.execute("CREATE TABLE IF NOT EXISTS configuracoes (chave TEXT PRIMARY KEY, valor TEXT NOT NULL);")
    conn.commit()

contas_svc = ContasService(db, events)
contas_svc.seed_iniciais()

registry = RouteRegistry()

@registry.get("/api/contas", summary="Lista lançamentos financeiros com busca e filtros", tags=["Financeiro"])
def get_contas(params):
    tipo = params.get("tipo", [None])[0]
    status = params.get("status", [None])[0]
    busca = params.get("busca", [None])[0]
    return contas_svc.listar(tipo, status, busca)

@registry.get("/api/contas/detalhes", summary="Obtém lançamento por ID", tags=["Financeiro"])
def get_conta_detalhes(params):
    cid = int(params.get("id", [0])[0])
    return contas_svc.obter_por_id(cid) or {}

@registry.get("/api/fluxo-caixa", summary="Resumo de fluxo de caixa e DRE em tempo real", tags=["Financeiro"])
def get_fluxo(params):
    return contas_svc.fluxo_caixa_resumo()

@registry.post("/api/contas/salvar", summary="Cria ou Edita lançamento (Full-CRUD)", tags=["Financeiro"])
def post_salvar_conta(data):
    return contas_svc.salvar(data)

@registry.post("/api/contas/alternar-status", summary="Alterna status entre Pago e Pendente em 1 clique", tags=["Financeiro"])
def post_status(data):
    return contas_svc.alternar_status(int(data.get("id", 0)))

@registry.post("/api/contas/deletar", summary="Remove lançamento por ID", tags=["Financeiro"])
def post_deletar_conta(data):
    return contas_svc.deletar(int(data.get("id", 0)))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(p.query)
        if p.path == "/docs/guia":
            with open(os.path.join(STATIC_DIR, "docs.html"), "r", encoding="utf-8") as df:
                self._html(df.read())
        elif p.path == "/docs":
            self._html(registry.get_swagger_html("ERP Financeiro — Swagger REST API"))
        elif p.path == "/openapi.json":
            self._json(registry.generate_openapi_json("ERP Financeiro API", "2.0.0"))
        elif p.path in registry.routes["GET"]:
            self._json(registry.routes["GET"][p.path](params))
        elif p.path == "/favicon.ico":
            self.send_response(204); self.end_headers()
        elif p.path == "/" or p.path == "":
            self.path = "/index.html"; super().do_GET()
        else: super().do_GET()

    def do_POST(self):
        p = urllib.parse.urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
        if p.path in registry.routes["POST"]:
            self._json(registry.routes["POST"][p.path](data))
        else: self.send_error(404)

    def _json(self, data):
        res = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(res)))
        self.end_headers(); self.wfile.write(res)

    def _html(self, h):
        res = h.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(res)))
        self.end_headers(); self.wfile.write(res)

class ThreadedServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True; allow_reuse_address = True

if __name__ == "__main__":
    server = ThreadedServer(("", PORT), Handler)
    print(f"[OK] ERP Financeiro V2 rodando em: http://localhost:{PORT}")
    server.serve_forever()
