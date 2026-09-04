import http.server, socketserver, json, urllib.parse, os, sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import Database
from core.events import EventBus
from core.openapi import RouteRegistry
from core.webhooks import WebhookDispatcher

# Importação dos Módulos Verticais
from modules.configuracao.backend.models import init_schema as init_cfg_schema
from modules.configuracao.backend.services import ConfigService
from modules.configuracao.backend.routes import registrar_rotas as reg_cfg_routes

from modules.produtos.backend.models import init_schema as init_prod_schema
from modules.produtos.backend.services import ProdutosService
from modules.produtos.backend.routes import registrar_rotas as reg_prod_routes

from modules.pedidos_whatsapp.backend.models import init_schema as init_ped_schema
from modules.pedidos_whatsapp.backend.services import PedidosService
from modules.pedidos_whatsapp.backend.routes import registrar_rotas as reg_ped_routes

PORT = 3000
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
db = Database(f"sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'loja.db')}")
events = EventBus()
webhook_dispatcher = WebhookDispatcher(db)

# Vincular o EventBus ao WebhookDispatcher (Push automático de eventos para n8n)
events.on("pedido_criado", lambda dados: webhook_dispatcher.disparar("pedido.criado", dados))
events.on("produto_salvo", lambda dados: webhook_dispatcher.disparar("produto.atualizado", dados))

# 1. Inicializar Schemas
with db.get_connection() as conn:
    init_cfg_schema(conn)
    init_prod_schema(conn)
    init_ped_schema(conn)

config_svc = ConfigService(db)
config_svc.obter()
config_svc.seed_admin()

produtos_svc = ProdutosService(db, events)
pedidos_svc = PedidosService(db, config_svc, events)

# Seed inicial
with db.get_connection() as conn:
    c = conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
    if c == 0:
        conn.executescript("""
            INSERT INTO produtos (nome, descricao, preco, preco_promo, categoria, thumbnail, destaque) VALUES
            ('Teclado Mecânico Wireless 75%', 'Switches silenciosos, RGB customizável e Bluetooth tri-mode.', 349.90, 299.90, 'Periféricos', 'https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=500', 1),
            ('Mouse Ergonômico Vertical Pro', 'Sensor óptico de alta precisão 4000 DPI.', 189.00, 159.90, 'Periféricos', 'https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=500', 1),
            ('Fone Noise Cancelling Studio', 'Cancelamento ativo de ruído ANC e bateria de 40h.', 499.00, 429.00, 'Áudio', 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500', 1);
        """)
        conn.commit()

# 3. Registrar Rotas
registry = RouteRegistry()
reg_cfg_routes(registry, config_svc)
reg_prod_routes(registry, produtos_svc)
reg_ped_routes(registry, pedidos_svc)

@registry.post("/api/admin/salvar-webhook", summary="Configura URL de Webhook para automação no n8n", tags=["Configuração"])
def post_salvar_webhook(data):
    url = data.get("webhook_url", "")
    with db.get_connection() as conn:
        conn.execute("INSERT OR REPLACE INTO configuracoes (chave, valor) VALUES ('webhook_url', ?)", (url,))
        conn.commit()
    return {"sucesso": True, "webhook_url": url, "mensagem": "Webhook configurado com sucesso para automações n8n!"}

class StoreHandler(http.server.SimpleHTTPRequestHandler):
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
            html = registry.get_swagger_html("Catálogo Modular — Swagger REST & Webhooks")
            self._send_html(html)
        elif path == "/openapi.json":
            spec = registry.generate_openapi_json("Catálogo Modular API & Webhooks", "2.0.0")
            self._send_json(spec)
        elif path in registry.routes["GET"]:
            handler = registry.routes["GET"][path]
            self._send_json(handler(params))
        elif path == "/api/checkout-whatsapp":
            self._send_json({
                "mensagem": "Este endpoint espera um método POST com os itens do pedido.",
                "exemplo_payload_post": {
                    "itens": [{"id": 1, "nome": "Teclado Mecânico", "preco": 299.90, "qtd": 1}],
                    "cliente_nome": "Seu Nome"
                },
                "como_testar": "Abra http://localhost:3000/docs para testar interativamente pelo Swagger!"
            })
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
    server = ThreadedHTTPServer(("", PORT), StoreHandler)
    print(f"[OK] Servidor com Webhooks rodando em: http://localhost:{PORT}")
    print(f"[OK] Swagger Docs com Webhook API em: http://localhost:{PORT}/docs")
    server.serve_forever()
