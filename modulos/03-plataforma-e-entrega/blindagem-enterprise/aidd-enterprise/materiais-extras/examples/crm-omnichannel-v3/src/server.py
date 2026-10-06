import http.server, socketserver, json, urllib.parse, os, sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import Database
from core.events import EventBus
from core.openapi import RouteRegistry
from core.webhooks import WebhookDispatcher
from modules.leads.backend.models import init_schema as init_leads
from modules.leads.backend.services import LeadsService
from modules.pipeline.backend.services import PipelineService

PORT = 3001
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
db = Database(f"sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'crm.db')}")
events = EventBus()
webhook_dispatcher = WebhookDispatcher(db)

# Disparo de Webhooks em tempo real para n8n
events.on("lead_criado", lambda d: webhook_dispatcher.disparar("lead.criado", d))
events.on("lead_atualizado", lambda d: webhook_dispatcher.disparar("lead.atualizado", d))
events.on("lead_movido_pipeline", lambda d: webhook_dispatcher.disparar("lead.estagio_alterado", d))
events.on("lead_excluido", lambda d: webhook_dispatcher.disparar("lead.excluido", d))

with db.get_connection() as conn:
    init_leads(conn)
    conn.execute("CREATE TABLE IF NOT EXISTS configuracoes (chave TEXT PRIMARY KEY, valor TEXT NOT NULL);")
    conn.commit()

leads_svc = LeadsService(db, events)
pipeline_svc = PipelineService(db, events)
leads_svc.seed_iniciais()

registry = RouteRegistry()

@registry.get("/api/leads", summary="Lista todos os leads com busca e filtros", tags=["Leads"])
def get_leads(params):
    st = params.get("status", [None])[0]
    busca = params.get("busca", [None])[0]
    return leads_svc.listar(st, busca)

@registry.get("/api/leads/detalhes", summary="Obtém detalhes de um lead por ID", tags=["Leads"])
def get_lead_detalhes(params):
    lid = int(params.get("id", [0])[0])
    return leads_svc.obter_por_id(lid) or {}

@registry.get("/api/pipeline", summary="Obtém quadro Kanban do funil de vendas", tags=["Pipeline"])
def get_pipeline(params):
    return pipeline_svc.obter_kanban()

@registry.post("/api/leads/salvar", summary="Cria ou Edita um lead (Full-CRUD)", tags=["Leads"])
def post_salvar_lead(data):
    return leads_svc.salvar(data)

@registry.post("/api/leads/deletar", summary="Remove um lead por ID", tags=["Leads"])
def post_deletar_lead(data):
    return leads_svc.deletar(int(data.get("id", 0)))

@registry.post("/api/pipeline/mover", summary="Move lead entre colunas do Kanban via Drag & Drop", tags=["Pipeline"])
def post_mover(data):
    return pipeline_svc.mover_lead(int(data.get("lead_id", 0)), data.get("novo_status", "qualificado"))

@registry.post("/api/admin/salvar-webhook", summary="Configura URL de Webhook para o n8n", tags=["Configuração"])
def post_webhook(data):
    url = data.get("webhook_url", "")
    with db.get_connection() as conn:
        conn.execute("INSERT OR REPLACE INTO configuracoes (chave, valor) VALUES ('webhook_url', ?)", (url,))
        conn.commit()
    return {"sucesso": True, "webhook_url": url, "mensagem": "Webhook configurado com sucesso!"}

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
            self._html(registry.get_swagger_html("CRM Omnichannel — Swagger REST API"))
        elif p.path == "/openapi.json":
            self._json(registry.generate_openapi_json("CRM Omnichannel API", "2.0.0"))
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
    print(f"[OK] CRM Enterprise V2 rodando em: http://localhost:{PORT}")
    print(f"[OK] Swagger Docs em: http://localhost:{PORT}/docs")
    server.serve_forever()
