import http.server, socketserver, json, urllib.parse, os, sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import Database
from core.events import EventBus
from core.openapi import RouteRegistry
from core.webhooks import WebhookDispatcher
from modules.tickets.backend.models import init_schema as init_tickets
from modules.tickets.backend.services import TicketsService

PORT = 3003
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
db = Database(f"sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'helpdesk.db')}")
events = EventBus()
webhook_dispatcher = WebhookDispatcher(db)

# Webhooks n8n
events.on("ticket_aberto", lambda d: webhook_dispatcher.disparar("helpdesk.ticket_criado", d))
events.on("ticket_atualizado", lambda d: webhook_dispatcher.disparar("helpdesk.ticket_atualizado", d))
events.on("ticket_status_alterado", lambda d: webhook_dispatcher.disparar("helpdesk.status_alterado", d))
events.on("ticket_excluido", lambda d: webhook_dispatcher.disparar("helpdesk.ticket_excluido", d))

with db.get_connection() as conn:
    init_tickets(conn)
    conn.execute("CREATE TABLE IF NOT EXISTS configuracoes (chave TEXT PRIMARY KEY, valor TEXT NOT NULL);")
    conn.commit()

tickets_svc = TicketsService(db, events)
tickets_svc.seed_iniciais()

registry = RouteRegistry()

@registry.get("/api/tickets", summary="Lista tickets de suporte com busca e filtros", tags=["Helpdesk"])
def get_tickets(params):
    st = params.get("status", [None])[0]
    prio = params.get("prioridade", [None])[0]
    busca = params.get("busca", [None])[0]
    return tickets_svc.listar(st, prio, busca)

@registry.get("/api/tickets/detalhes", summary="Obtém ticket por ID", tags=["Helpdesk"])
def get_ticket_detalhes(params):
    tid = int(params.get("id", [0])[0])
    return tickets_svc.obter_por_id(tid) or {}

@registry.post("/api/tickets/salvar", summary="Cria ou Edita um chamado (Full-CRUD)", tags=["Helpdesk"])
def post_salvar_ticket(data):
    return tickets_svc.salvar(data)

@registry.post("/api/tickets/avancar-status", summary="Avança status do chamado (Aberto -> Andamento -> Resolvido)", tags=["Helpdesk"])
def post_avancar(data):
    return tickets_svc.avancar_status(int(data.get("id", 0)))

@registry.post("/api/tickets/deletar", summary="Remove um chamado por ID", tags=["Helpdesk"])
def post_deletar_ticket(data):
    return tickets_svc.deletar(int(data.get("id", 0)))

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
            self._html(registry.get_swagger_html("Helpdesk SLA — Swagger REST API"))
        elif p.path == "/openapi.json":
            self._json(registry.generate_openapi_json("Helpdesk API", "2.0.0"))
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
    print(f"[OK] Helpdesk SLA V2 rodando em: http://localhost:{PORT}")
    server.serve_forever()
