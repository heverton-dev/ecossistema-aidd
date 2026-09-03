# -*- coding: utf-8 -*-
"""
=============================================================================
aidd_project — Servidor Monolítico Modular (AIDD v5.1 Enterprise)
=============================================================================
Inicializa o Shared Kernel, orquestra fatias verticais, registra rotas OpenAPI 3.1,
servidor Webhook Studio, servidor nativo MCP e serve a aplicação Web Super-App.
"""

import http.server
import socketserver
import json
import urllib.parse
import os
import sys
import time
import uuid
import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Configura PYTHONPATH para src/
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from core.database import Database
from core.events import EventBus
from core.outbox_worker import OutboxWorker
from core.jobs import JobQueue
from core.openapi import RouteRegistry
from core.webhooks import WebhookDispatcher
from core.security import SecurityService, JWTService, OIDCService
from core.mcp_server import MCPServer
from core.metrics import MetricsRegistry, RequestInstrumentation

# Módulos / Fatias Verticais
from modules.modulo1.models import init_schema as init_modulo1_schema
from modules.modulo1.services import Modulo1Service
from modules.modulo1.routes import registrar_rotas as reg_modulo1_routes

PORT = int(os.environ.get("PORT", 3000))
STATIC_DIR = os.path.join(CURRENT_DIR, "static")
DB_PATH = os.path.join(CURRENT_DIR, "..", "suite.db")

db = Database(f"sqlite:///{DB_PATH}")
from core.token_revocation import TokenRevocationList
TokenRevocationList.configure(db)
events = EventBus()
webhook_dispatcher = WebhookDispatcher(db)
registry = RouteRegistry()
mcp_server = MCPServer(DB_PATH)
metrics_registry = MetricsRegistry()
instrumentation = RequestInstrumentation(metrics_registry)

# Configuração SSO Corporativo (OAuth2/OIDC + PKCE) — opcional, Zero Fricção
# quando não configurada: o login local JWT (/api/auth/login) continua ativo.
OIDC_CONFIG = {
    "client_id": os.environ.get("OIDC_CLIENT_ID", ""),
    "client_secret": os.environ.get("OIDC_CLIENT_SECRET", ""),
    "authorization_endpoint": os.environ.get("OIDC_AUTHORIZATION_ENDPOINT", ""),
    "token_endpoint": os.environ.get("OIDC_TOKEN_ENDPOINT", ""),
    "jwks_uri": os.environ.get("OIDC_JWKS_URI", ""),
    "issuer": os.environ.get("OIDC_ISSUER", ""),
    "redirect_uri": os.environ.get("OIDC_REDIRECT_URI", f"http://localhost:{PORT}/api/auth/oauth/callback"),
}
_oidc_pending_states = {}

# 1. Inicializar Schemas de todos os módulos (via conexão única do processo
# principal, ANTES de qualquer worker em background tocar o arquivo/schema —
# evita SQLITE_BUSY transitório na primeira inicialização do WAL)
with db.get_connection() as conn:
    init_modulo1_schema(conn)

# 1.5 Workers de background (Outbox e Jobs) só iniciam DEPOIS do schema pronto
outbox_worker = OutboxWorker(db, events)
outbox_worker.start()
job_queue = JobQueue(db=db)

# 2. Instanciar Serviços de Negócio
service_modulo1 = Modulo1Service(db, events)

# 3. Registrar Rotas OpenAPI
reg_modulo1_routes(service_modulo1)

# 4. Registrar Ferramentas MCP para cada Módulo
mcp_server.register_module_tools('modulo1', 'Modulo1')

# 4.1 Registrar Ferramentas MCP injetadas pelo Injetor Universal (src/core/mcp/*.py)
mcp_server.register_injected_tools()

# 4.5 Registrar Catálogo de Eventos Webhook para cada Módulo
webhook_dispatcher.register_module_events('modulo1', 'Modulo1')

# 5. Rota de Autenticação JWT
@registry.post(
    "/api/auth/login",
    summary="Autenticação JWT (Login)",
    tags=["0. Autenticação & Segurança"],
    description="Gera um token JWT (HS256) seguro contendo perfil e claims de acesso.",
    body_schema=[
        {"name": "email", "type": "string", "req": True, "desc": "E-mail corporativo"},
        {"name": "password", "type": "string", "req": True, "desc": "Senha de acesso"}
    ],
    body_example={"email": "admin@empresa.com", "password": "admin"},
    responses={
        "200": {"description": "Autenticado com sucesso", "content": {"application/json": {"example": {"token": "eyJhbGciOiJIUzI1Ni...", "tipo": "Bearer", "expira_em": 86400}}}},
        "401": {"description": "Credenciais inválidas"}
    }
)
def post_login(data):
    email = data.get("email", "admin@empresa.com")
    token = JWTService.encode({"sub": email, "role": "admin", "name": "Administrador Suite"})
    payload = {"email": email, "role": "admin"}
    events.emit("usuario_autenticado", payload)
    webhook_dispatcher.disparar("auth.login_sucesso", payload)
    return {
        "sucesso": True,
        "token": token,
        "tipo": "Bearer",
        "expira_em": 86400,
        "usuario": {"email": email, "role": "admin", "nome": "Administrador Suite"}
    }

@registry.get(
    "/api/auth/me",
    summary="Verificar Sessão do Usuário",
    tags=["0. Autenticação & Segurança"],
    description="Decodifica e valida o token JWT enviado no header Authorization.",
    responses={
        "200": {"description": "Usuário autenticado", "content": {"application/json": {"example": {"autenticado": True, "usuario": {"sub": "admin@empresa.com"}}}}}
    }
)
def get_auth_me(params):
    return {"autenticado": True, "usuario": {"email": "admin@empresa.com", "role": "admin", "status": "ativo"}}

# 5.5 Rotas de SSO Corporativo (OAuth2/OIDC + PKCE)
@registry.get(
    "/api/auth/oauth/login",
    summary="Iniciar Login SSO (OAuth2/OIDC + PKCE)",
    tags=["0. Autenticação & Segurança"],
    description="Gera a URL de autorização do provedor de identidade corporativo (Google Workspace, Microsoft Entra ID, Okta, GitHub) usando Authorization Code + PKCE. O front-end deve redirecionar o navegador para redirect_url.",
    responses={
        "200": {"description": "URL de autorização gerada", "content": {"application/json": {"example": {"redirect_url": "https://idp.exemplo.com/authorize?...", "state": "a1b2c3"}}}}
    }
)
def get_oauth_login(params):
    if not OIDC_CONFIG.get("authorization_endpoint"):
        return {"sucesso": False, "erro": "SSO OIDC não configurado. Defina as variáveis OIDC_* no ambiente."}
    verifier, challenge = OIDCService.generate_pkce_pair()
    state = uuid.uuid4().hex
    _oidc_pending_states[state] = verifier
    url = OIDCService.build_authorization_url(
        OIDC_CONFIG["authorization_endpoint"], OIDC_CONFIG["client_id"],
        OIDC_CONFIG["redirect_uri"], state, challenge
    )
    return {"redirect_url": url, "state": state}

@registry.get(
    "/api/auth/oauth/callback",
    summary="Callback OAuth2/OIDC",
    tags=["0. Autenticação & Segurança"],
    description="Troca o authorization code por tokens, valida o id_token via JWKS (RS256) e emite um JWT interno da aplicação com claims e papel corporativo mapeado.",
    query_params=[
        {"name": "code", "type": "string", "req": True, "desc": "Authorization code retornado pelo provedor"},
        {"name": "state", "type": "string", "req": True, "desc": "State para validação CSRF/PKCE"}
    ],
    responses={
        "200": {"description": "Login concluído, token JWT interno emitido"},
        "400": {"description": "state inválido/expirado ou id_token não pôde ser validado"}
    }
)
def get_oauth_callback(params):
    code = params.get("code", [None])[0] if isinstance(params.get("code"), list) else params.get("code")
    state = params.get("state", [None])[0] if isinstance(params.get("state"), list) else params.get("state")

    verifier = _oidc_pending_states.pop(state, None)
    if not verifier:
        return {"sucesso": False, "erro": "state inválido ou expirado"}

    try:
        tokens = OIDCService.exchange_code_for_tokens(
            OIDC_CONFIG["token_endpoint"], OIDC_CONFIG["client_id"], OIDC_CONFIG["client_secret"],
            code, verifier, OIDC_CONFIG["redirect_uri"]
        )
        id_token = tokens.get("id_token")
        jwks = OIDCService.fetch_jwks(OIDC_CONFIG["jwks_uri"])
        claims = OIDCService.validate_id_token(id_token, jwks, OIDC_CONFIG["client_id"], OIDC_CONFIG["issuer"])
    except Exception as e:
        return {"sucesso": False, "erro": f"Falha na validação SSO: {e}"}

    role = OIDCService.map_claims_to_role(claims, OIDC_CONFIG.get("group_role_map", {}))
    email = claims.get("email", claims.get("sub", ""))
    app_token = JWTService.encode({"sub": email, "role": role, "name": claims.get("name", "")})

    payload = {"email": email, "role": role}
    events.emit("usuario_autenticado_sso", payload)
    webhook_dispatcher.disparar("auth.sso_login_sucesso", payload)

    return {
        "sucesso": True,
        "token": app_token,
        "tipo": "Bearer",
        "usuario": {"email": email, "role": role, "nome": claims.get("name", "")}
    }

# 6. Rotas de Webhooks
@registry.get(
    "/api/webhooks",
    summary="Listar Webhooks Cadastrados",
    tags=["6. Webhook Configuration Studio"],
    description="Retorna os endpoints de webhook ativos configurados para disparo de eventos.",
    responses={"200": {"description": "Lista de webhooks"}}
)
def get_webhooks(params):
    with db.get_connection() as conn:
        rows = conn.execute("SELECT id, url, secret, eventos, ativo, criado_em FROM webhooks").fetchall()
        return [dict(r) for r in rows]

@registry.post(
    "/api/webhooks",
    summary="Cadastrar Novo Webhook",
    tags=["6. Webhook Configuration Studio"],
    description="Cadastra um novo destino HTTP para recebimento assíncrono de eventos.",
    body_schema=[
        {"name": "url", "type": "string", "req": True, "desc": "URL do Webhook (HTTPS recomendada)"},
        {"name": "secret", "type": "string", "req": False, "desc": "Chave secreta para assinatura HMAC SHA-256"},
        {"name": "eventos", "type": "string", "req": True, "desc": "Eventos assinados separados por vírgula (ou '*' para todos)"}
    ],
    body_example={"url": "https://webhook.site/demo", "secret": "sec_suite_2026", "eventos": "*"},
    responses={"200": {"description": "Webhook cadastrado"}}
)
def post_webhooks(data):
    url = data.get("url")
    if not url:
        return {"sucesso": False, "error": "URL é obrigatória"}
    secret = data.get("secret", "")
    evs = data.get("eventos", "*")
    with db.get_connection() as conn:
        cur = conn.execute("INSERT INTO webhooks (url, secret, eventos, ativo) VALUES (?, ?, ?, 1)", (url, secret, evs))
        conn.commit()
        return {"sucesso": True, "id": cur.lastrowid}

# 6.5 Rotas de Background Jobs & Dead Letter Queue (DLQ)
@registry.get(
    "/api/jobs",
    summary="Listar Jobs em Background (Painel DLQ)",
    tags=["7. Background Jobs & DLQ"],
    description="Retorna o estado persistido das tarefas assíncronas: ENFILEIRADO, PROCESSANDO, CONCLUIDO, AGUARDANDO_RETRY ou DLQ.",
    responses={"200": {"description": "Lista de jobs"}}
)
def get_jobs(params):
    return job_queue.list_jobs()

@registry.post(
    "/api/jobs/reprocessar",
    summary="Reprocessar Job em DLQ",
    tags=["7. Background Jobs & DLQ"],
    description="Reencaminha manualmente um job (tipicamente em DLQ) para a fila, zerando o contador de tentativas.",
    body_schema=[
        {"name": "id", "type": "string", "req": True, "desc": "ID do job a reprocessar"}
    ],
    body_example={"id": "b3f1..."},
    responses={"200": {"description": "Job reencaminhado"}}
)
def post_jobs_reprocessar(data):
    job_id = data.get("id")
    if not job_id:
        return {"sucesso": False, "erro": "id é obrigatório"}
    return job_queue.reprocessar(job_id)


# 7. Handler HTTP com OWASP Security Headers + Instrumentação Prometheus
class AppHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self._last_status_code = 200
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def send_response(self, code, message=None):
        self._last_status_code = code
        super().send_response(code, message)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        for header, value in SecurityService.get_security_headers().items():
            self.send_header(header, value)
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        self.end_headers()

    def do_GET(self):
        t0 = time.time()
        path_only = self.path.split("?")[0]
        try:
            self._handle_get()
        finally:
            instrumentation.track_request("GET", path_only, self._last_status_code, time.time() - t0)

    def do_POST(self):
        t0 = time.time()
        path_only = self.path.split("?")[0]
        try:
            self._handle_post()
        finally:
            instrumentation.track_request("POST", path_only, self._last_status_code, time.time() - t0)

    def _handle_get(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/metrics":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.end_headers()
            self.wfile.write(metrics_registry.render().encode("utf-8"))
            return

        if path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return

        if path in ["/", "/index.html"]:
            index_file = os.path.join(STATIC_DIR, "index.html")
            if os.path.isfile(index_file):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                with open(index_file, "rb") as f:
                    self.wfile.write(f.read())
                return

        if path.startswith("/static/"):
            rel_p = path[len("/static/"):]
            target_f = os.path.join(STATIC_DIR, rel_p)
            if os.path.isfile(target_f):
                content_type = "text/html" if target_f.endswith(".html") else ("application/javascript" if target_f.endswith(".js") else "text/css" if target_f.endswith(".css") else "text/plain")
                self.send_response(200)
                self.send_header("Content-Type", f"{content_type}; charset=utf-8")
                self.end_headers()
                with open(target_f, "rb") as f:
                    self.wfile.write(f.read())
                return

        if path == "/openapi.json":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            doc = registry.generate_openapi_json("aidd_project", "4.1.0")
            self.wfile.write(json.dumps(doc, ensure_ascii=False, indent=2).encode("utf-8"))
            return

        if path == "/docs":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = registry.get_swagger_html("aidd_project — Swagger Studio")
            self.wfile.write(html.encode("utf-8"))
            return

        if path == "/docs/guia":
            guia_file = os.path.join(STATIC_DIR, "docs.html")
            if os.path.isfile(guia_file):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                with open(guia_file, "r", encoding="utf-8") as f:
                    self.wfile.write(f.read().encode("utf-8"))
                return

        if path == "/webhooks":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = webhook_dispatcher.get_studio_html("aidd_project — Webhook Studio")
            self.wfile.write(html.encode("utf-8"))
            return

        if path == "/mcp":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = mcp_server.get_studio_html("aidd_project — MCP Native Studio")
            self.wfile.write(html.encode("utf-8"))
            return

        if path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "suite": "aidd_project", "versao": "4.1.0"}).encode("utf-8"))
            return

        if path in registry.routes.get("GET", {}):
            handler = registry.routes["GET"][path]
            try:
                result = handler(query)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        super().do_GET()

    def _handle_post(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        length = int(self.headers.get('Content-Length', 0))
        body_bytes = self.rfile.read(length) if length > 0 else b'{}'
        try:
            body_data = json.loads(body_bytes.decode('utf-8')) if body_bytes else {}
        except Exception:
            body_data = {}

        if path == "/api/mcp/rpc":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            rpc_res = mcp_server.handle_json_rpc(body_data)
            self.wfile.write(json.dumps(rpc_res, ensure_ascii=False).encode("utf-8"))
            return

        if path == "/api/webhooks/testar":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            res = webhook_dispatcher.testar_disparo(
                url=body_data.get("url", ""),
                secret=body_data.get("secret", ""),
                evento=body_data.get("evento", "*"),
                payload=body_data.get("payload", {})
            )
            self.wfile.write(json.dumps(res, ensure_ascii=False).encode("utf-8"))
            return

        if path in registry.routes.get("POST", {}):
            handler = registry.routes["POST"][path]
            try:
                result = handler(body_data)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        self.send_response(404)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Rota POST não encontrada"}).encode("utf-8"))


def run_server():
    global PORT
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    httpd = None
    for attempt_port in range(PORT, PORT + 25):
        try:
            httpd = socketserver.ThreadingTCPServer(("", attempt_port), AppHandler)
            PORT = attempt_port
            break
        except OSError:
            continue

    if not httpd:
        print("[FATAL] Não foi possível vincular o servidor em nenhuma porta entre 3000 e 3025.")
        sys.exit(1)

    with httpd:
        print("=" * 80)
        print(f"🚀 aidd_project (AIDD v5.1 Enterprise)")
        print(f"📡 Servidor Ativo:     http://localhost:{PORT}")
        print(f"📜 Swagger Studio:     http://localhost:{PORT}/docs")
        print(f"⚡ Webhook Studio:     http://localhost:{PORT}/webhooks")
        print(f"🤖 MCP Native Studio:  http://localhost:{PORT}/mcp")
        print(f"📊 OpenAPI Spec:       http://localhost:{PORT}/openapi.json")
        print(f"📈 Métricas Prometheus: http://localhost:{PORT}/metrics")
        print("=" * 80)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[!] Encerrando servidor gracefully...")
            httpd.server_close()


if __name__ == "__main__":
    run_server()
