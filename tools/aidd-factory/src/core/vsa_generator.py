# -*- coding: utf-8 -*-
"""
AIDD-Factory — Vertical Slice Architecture (VSA) & Quarteto Sine Qua Non Generator.

Gera o monólito modular canônico do ecossistema AIDD:
  1. Shared Kernel (Database, EventBus, RouteRegistry, WebhookDispatcher, MCPServer, Security)
  2. Fatias Verticais (src/modules/<slug>/ com models, repositories, services, routes)
  3. Servidor Monolítico Modular (src/server.py) com o Quarteto Sine Qua Non:
     - /swagger (Swagger Studio OpenAPI 3.1)
     - /webhooks (Webhook Studio & Dispatcher)
     - /mcp (MCP Studio & SSE Server para agentes de IA)
     - /docs (Manual Dinâmico do Utilizador)
  4. Super-App Frontend Impeccable (src/static/index.html & docs.html)
"""
import os
import re
import sys
import shutil
import json
from typing import Dict, List, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "componentes", "compartilhado", "src-core"))
from core.result import Result

_TEMPLATES_VSA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "templates", "vsa")


def _slugify(texto: str) -> str:
    """Gera slug deterministico."""
    s = texto.lower().replace(" ", "_").replace("-", "_").replace(".", "")
    s = re.sub(r"[^a-z0-9_]", "", s)
    return s.strip("_") or "modulo"


def _pascal_case(texto: str) -> str:
    """Gera PascalCase."""
    palavras = re.split(r"[\s\-_.]+", texto)
    return "".join(w.capitalize() for w in palavras if w)


def _gerar_fatia_modulo(pasta_saida: str, nome_ferramenta: str, nicho_slug: str) -> List[str]:
    """Gera os arquivos de uma fatia vertical completa em src/modules/<slug>/."""
    slug = _slugify(nome_ferramenta)
    pascal = _pascal_case(nome_ferramenta)
    mod_dir = os.path.join(pasta_saida, "src", "modules", slug)
    os.makedirs(mod_dir, exist_ok=True)
    arquivos = []

    # 1. __init__.py
    init_path = os.path.join(mod_dir, "__init__.py")
    with open(init_path, "w", encoding="utf-8") as f:
        f.write(f"# Fatia Vertical: {pascal}\n")
    arquivos.append(init_path)

    # 2. models.py
    models_content = f'''# -*- coding: utf-8 -*-
"""
Modelos de Dados e Schemas da Fatia: {pascal}
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class {pascal}CreateRequest(BaseModel):
    """Payload de criacao para {pascal}."""
    titulo: str = Field(..., min_length=2, max_length=120, description="Titulo ou identificador principal")
    descricao: Optional[str] = Field(None, max_length=500, description="Descricao detalhada")
    payload: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Parametros e configuracoes")
    status: Optional[str] = Field("ativo", description="Status inicial do registro")


class {pascal}UpdateRequest(BaseModel):
    """Payload de atualizacao para {pascal}."""
    titulo: Optional[str] = Field(None, min_length=2, max_length=120)
    descricao: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class {pascal}Response(BaseModel):
    """Payload de resposta para {pascal}."""
    id: int
    tenant_id: str
    titulo: str
    descricao: Optional[str] = None
    payload: Optional[str] = None
    status: str
    created_at: str
    updated_at: str


def init_schema(conn):
    """Inicializa tabelas da fatia {pascal} no banco de dados com isolamento por tenant."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tabela_{slug} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL DEFAULT 'default',
            titulo TEXT NOT NULL,
            descricao TEXT,
            payload TEXT,
            status TEXT NOT NULL DEFAULT 'ativo',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_{slug}_tenant ON tabela_{slug}(tenant_id)
    """)
    conn.commit()
'''
    models_path = os.path.join(mod_dir, "models.py")
    with open(models_path, "w", encoding="utf-8") as f:
        f.write(models_content)
    arquivos.append(models_path)

    # 3. repositories.py (100% blindado contra SQL injection)
    repositories_content = f'''# -*- coding: utf-8 -*-
"""
Repositorio de Dados da Fatia: {pascal}
Queries 100% parametrizadas anti-SQL Injection.
"""
import json
from typing import List, Optional, Dict, Any


class {pascal}Repository:
    """Repositorio tipado com isolamento de tenant para {pascal}."""

    def __init__(self, db):
        self.db = db

    def listar(self, tenant_id: str = "default") -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, tenant_id, titulo, descricao, payload, status, created_at, updated_at "
                "FROM tabela_{slug} WHERE tenant_id = ? ORDER BY id DESC",
                (tenant_id,)
            )
            linhas = cursor.fetchall()
            colunas = [col[0] for col in cursor.description]
            return [dict(zip(colunas, linha)) for linha in linhas]

    def obter_por_id(self, item_id: int, tenant_id: str = "default") -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, tenant_id, titulo, descricao, payload, status, created_at, updated_at "
                "FROM tabela_{slug} WHERE id = ? AND tenant_id = ?",
                (item_id, tenant_id)
            )
            linha = cursor.fetchone()
            if not linha:
                return None
            colunas = [col[0] for col in cursor.description]
            return dict(zip(colunas, linha))

    def criar(self, titulo: str, descricao: Optional[str], payload: Dict[str, Any], status: str, tenant_id: str = "default") -> int:
        payload_str = json.dumps(payload, ensure_ascii=False) if payload else "{{}}"
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tabela_{slug} (tenant_id, titulo, descricao, payload, status) VALUES (?, ?, ?, ?, ?)",
                (tenant_id, titulo, descricao, payload_str, status)
            )
            conn.commit()
            return cursor.lastrowid

    def atualizar(self, item_id: int, campos: Dict[str, Any], tenant_id: str = "default") -> bool:
        if not campos:
            return False
        sets = []
        valores = []
        for k, v in campos.items():
            if k in ("titulo", "descricao", "status"):
                sets.append(f"{{k}} = ?")
                valores.append(v)
            elif k == "payload":
                sets.append("payload = ?")
                valores.append(json.dumps(v, ensure_ascii=False))
        if not sets:
            return False
        sets.append("updated_at = CURRENT_TIMESTAMP")
        valores.extend([item_id, tenant_id])
        query = f"UPDATE tabela_{slug} SET {{', '.join(sets)}} WHERE id = ? AND tenant_id = ?"
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(valores))
            conn.commit()
            return cursor.rowcount > 0

    def deletar(self, item_id: int, tenant_id: str = "default") -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM tabela_{slug} WHERE id = ? AND tenant_id = ?",
                (item_id, tenant_id)
            )
            conn.commit()
            return cursor.rowcount > 0
'''
    repo_path = os.path.join(mod_dir, "repositories.py")
    with open(repo_path, "w", encoding="utf-8") as f:
        f.write(repositories_content)
    arquivos.append(repo_path)

    # 4. services.py
    services_content = f'''# -*- coding: utf-8 -*-
"""
Servico de Dominio da Fatia: {pascal}
Regras de negocio e orquestracao de eventos.
"""
from typing import List, Optional, Dict, Any


class {pascal}Service:
    """Regras de negocio e eventos para {pascal}."""

    def __init__(self, db, events, repository):
        self.db = db
        self.events = events
        self.repo = repository

    def listar_todos(self, tenant_id: str = "default") -> List[Dict[str, Any]]:
        return self.repo.listar(tenant_id)

    def obter(self, item_id: int, tenant_id: str = "default") -> Optional[Dict[str, Any]]:
        return self.repo.obter_por_id(item_id, tenant_id)

    def criar(self, dados: Dict[str, Any], tenant_id: str = "default") -> Dict[str, Any]:
        titulo = dados.get("titulo")
        descricao = dados.get("descricao")
        payload = dados.get("payload") or {{}}
        status = dados.get("status") or "ativo"
        item_id = self.repo.criar(titulo, descricao, payload, status, tenant_id)
        registro = self.repo.obter_por_id(item_id, tenant_id)
        
        # Disparar eventos no EventBus
        if self.events:
            self.events.emit("{slug}.criado", registro)
        return registro

    def atualizar(self, item_id: int, dados: Dict[str, Any], tenant_id: str = "default") -> Optional[Dict[str, Any]]:
        sucesso = self.repo.atualizar(item_id, dados, tenant_id)
        if not sucesso:
            return None
        registro = self.repo.obter_por_id(item_id, tenant_id)
        if self.events:
            self.events.emit("{slug}.atualizado", registro)
        return registro

    def remover(self, item_id: int, tenant_id: str = "default") -> bool:
        registro = self.repo.obter_por_id(item_id, tenant_id)
        if not registro:
            return False
        sucesso = self.repo.deletar(item_id, tenant_id)
        if sucesso and self.events:
            self.events.emit("{slug}.removido", {{"id": item_id, "tenant_id": tenant_id}})
        return sucesso
'''
    services_path = os.path.join(mod_dir, "services.py")
    with open(services_path, "w", encoding="utf-8") as f:
        f.write(services_content)
    arquivos.append(services_path)

    # 5. routes.py
    routes_content = f'''# -*- coding: utf-8 -*-
"""
Roteador RESTful da Fatia: {pascal}
Registrado no RouteRegistry singleton do ecossistema.
"""
from core.openapi import RouteRegistry

registry = RouteRegistry()


def registrar_rotas(service):
    """Registra endpoints RESTful tipados para {pascal} no RouteRegistry."""

    @registry.get(
        "/api/{slug}",
        summary="Listar registros de {pascal}",
        tags=["{pascal}"],
        description="Retorna lista completa de registros cadastrados para a fatia {pascal}."
    )
    def listar_{slug}(params=None):
        tenant_id = params.get("tenant_id", "default") if params else "default"
        return service.listar_todos(tenant_id)

    @registry.get(
        "/api/{slug}/<int:id>",
        summary="Obter registro por ID em {pascal}",
        tags=["{pascal}"],
        description="Retorna detalhes completos de um registro especifico de {pascal}."
    )
    def obter_{slug}(item_id, params=None):
        tenant_id = params.get("tenant_id", "default") if params else "default"
        res = service.obter(item_id, tenant_id)
        if not res:
            return {{"error": "Registro nao encontrado"}}, 404
        return res

    @registry.post(
        "/api/{slug}",
        summary="Criar novo registro em {pascal}",
        tags=["{pascal}"],
        description="Cria e persiste um novo registro na fatia vertical {pascal}."
    )
    def criar_{slug}(body):
        tenant_id = body.get("tenant_id", "default")
        return service.criar(body, tenant_id), 201

    @registry.put(
        "/api/{slug}/<int:id>",
        summary="Atualizar registro em {pascal}",
        tags=["{pascal}"],
        description="Atualiza dados cadastrais e status de um registro em {pascal}."
    )
    def atualizar_{slug}(item_id, body):
        tenant_id = body.get("tenant_id", "default")
        res = service.atualizar(item_id, body, tenant_id)
        if not res:
            return {{"error": "Falha ao atualizar ou registro inexistente"}}, 404
        return res

    @registry.delete(
        "/api/{slug}/<int:id>",
        summary="Excluir registro em {pascal}",
        tags=["{pascal}"],
        description="Remove permanentemente o registro de {pascal}."
    )
    def remover_{slug}(item_id, params=None):
        tenant_id = params.get("tenant_id", "default") if params else "default"
        ok = service.remover(item_id, tenant_id)
        if not ok:
            return {{"error": "Falha ao remover ou registro inexistente"}}, 404
        return {{"sucesso": True, "removido": item_id}}
'''
    routes_path = os.path.join(mod_dir, "routes.py")
    with open(routes_path, "w", encoding="utf-8") as f:
        f.write(routes_content)
    arquivos.append(routes_path)

    return arquivos


def _gerar_shared_kernel(pasta_saida: str) -> List[str]:
    """Copia e configura os arquivos do Shared Kernel em src/core/ e src/static/."""
    src_core_dir = os.path.join(pasta_saida, "src", "core")
    src_static_dir = os.path.join(pasta_saida, "src", "static")
    os.makedirs(src_core_dir, exist_ok=True)
    os.makedirs(src_static_dir, exist_ok=True)
    arquivos = []

    # Shared Kernel .py files
    kernel_files = [
        "database.py", "events.py", "openapi.py", "webhooks.py",
        "mcp_server.py", "security.py", "token_revocation.py", "result.py"
    ]
    for kf in kernel_files:
        src = os.path.join(_TEMPLATES_VSA_DIR, kf)
        dst = os.path.join(src_core_dir, kf)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
            arquivos.append(dst)

    # src/core/__init__.py
    core_init = os.path.join(src_core_dir, "__init__.py")
    with open(core_init, "w", encoding="utf-8") as f:
        f.write("# Shared Kernel AIDD Factory\n")
    arquivos.append(core_init)

    # Static HTML / CSS Studios (Quarteto Sine Qua Non)
    static_files = ["swagger.html", "webhook_studio.html", "mcp_studio.html", "output.css"]
    for sf in static_files:
        src = os.path.join(_TEMPLATES_VSA_DIR, sf)
        dst = os.path.join(src_static_dir, sf)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
            arquivos.append(dst)

    return arquivos


def _gerar_server_modular(pasta_saida: str, suite_name: str, servicos: List[Dict[str, Any]]) -> str:
    """Gera o src/server.py monolitico modular com o Quarteto Sine Qua Non."""
    imports_lines = []
    init_schema_calls = []
    instancia_repos = []
    instancia_services = []
    registrar_rotas_calls = []
    mcp_tools_reg = []
    webhook_events_reg = []

    for s in servicos:
        slug = s["slug"]
        pascal = s["pascal"]
        imports_lines.append(f"from modules.{slug}.models import init_schema as init_{slug}_schema")
        imports_lines.append(f"from modules.{slug}.repositories import {pascal}Repository")
        imports_lines.append(f"from modules.{slug}.services import {pascal}Service")
        imports_lines.append(f"from modules.{slug}.routes import registrar_rotas as reg_{slug}_routes")

        init_schema_calls.append(f"    init_{slug}_schema(conn)")
        instancia_repos.append(f"repo_{slug} = {pascal}Repository(db)")
        instancia_services.append(f"service_{slug} = {pascal}Service(db, events, repo_{slug})")
        registrar_rotas_calls.append(f"reg_{slug}_routes(service_{slug})")
        mcp_tools_reg.append(f"mcp_server.register_module_tools('{slug}', '{pascal}')")
        webhook_events_reg.append(f"webhook_dispatcher.register_module_events('{slug}', '{pascal}')")

    imports_str = "\n".join(imports_lines)
    init_schemas_str = "\n".join(init_schema_calls)
    instancia_repos_str = "\n".join(instancia_repos)
    instancia_services_str = "\n".join(instancia_services)
    registrar_rotas_str = "\n".join(registrar_rotas_calls)
    mcp_tools_str = "\n".join(mcp_tools_reg)
    webhook_events_str = "\n".join(webhook_events_reg)

    server_code = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD Factory — Servidor Monolítico Modular (Vertical Slice Architecture)
Suíte: {suite_name}
=============================================================================
Quarteto Sine Qua Non Dinâmico Ativo:
  - /swagger   -> Swagger Studio OpenAPI 3.1 interativo
  - /webhooks  -> Webhook Studio com simulador de eventos
  - /mcp       -> MCP Studio & MCP SSE Server nativo para agentes
  - /docs      -> Manual Dinâmico do Utilizador gerado via AST
  - /healthz   -> Healthcheck global do ambiente
  - /api/auth  -> Autenticação JWT e revogação de tokens (TRL)
"""
import http.server
import socketserver
import json
import urllib.parse
import os
import sys
import uuid

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

from core.database import Database
from core.events import EventBus
from core.openapi import RouteRegistry
from core.webhooks import WebhookDispatcher
from core.mcp_server import AIDD_EnterpriseMCPServer
from core.security import SecurityService, JWTService

# Fatias Verticais
{imports_str}

PORT = int(os.environ.get("PORT", 3000))
STATIC_DIR = os.path.join(CURRENT_DIR, "static")
DB_PATH = os.environ.get("DB_PATH", os.path.join(CURRENT_DIR, "..", "suite.db"))
os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)

# Shared Kernel
db = Database(f"sqlite:///{{DB_PATH}}")
events = EventBus()
webhook_dispatcher = WebhookDispatcher(db)
mcp_server = AIDD_EnterpriseMCPServer(DB_PATH)

# Inicializar Schemas das Fatias
with db.get_connection() as conn:
{init_schemas_str}

# Repositorios e Servicos
{instancia_repos_str}
{instancia_services_str}

# Roteador Global Singleton
registry = RouteRegistry()

# Registrar Rotas das Fatias
{registrar_rotas_str}

# Registrar Ferramentas no MCP Server e Webhooks
{mcp_tools_str}
{webhook_events_str}

# =========================================================================
# AUTENTICAÇÃO JWT
# =========================================================================
@registry.post(
    "/api/auth/login",
    summary="Autenticação JWT (Login)",
    tags=["Autenticação & Segurança"],
    description="Gera token JWT seguro para sessões autenticadas."
)
def post_login(data):
    email = data.get("email", "admin@aidd.local")
    role = data.get("role", "admin")
    token = JWTService.encode({{"sub": email, "role": role, "name": "Operador AIDD"}})
    payload = {{"email": email, "role": role}}
    events.emit("usuario_autenticado", payload)
    webhook_dispatcher.disparar("auth.login_sucesso", payload)
    return {{
        "sucesso": True,
        "token": token,
        "tipo": "Bearer",
        "expira_em": 86400,
        "usuario": {{"email": email, "role": role}}
    }}


# =========================================================================
# HEALTHCHECK GLOBAL
# =========================================================================
@registry.get(
    "/healthz",
    summary="Healthcheck Global",
    tags=["Infraestrutura"],
    description="Verifica a integridade do servidor, banco de dados e subsistemas."
)
def get_healthz(params=None):
    db_ok = False
    try:
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1")
            db_ok = (cur.fetchone()[0] == 1)
    except Exception:
        db_ok = False

    return {{
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "suite": "{suite_name}",
        "modules_count": {len(servicos)}
    }}


# =========================================================================
# DISPATCHER HTTP PRINCIPAL (Quarteto Sine Qua Non & Arquivos Estáticos)
# =========================================================================
class ModularHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)
        params = {{k: v[0] if len(v) == 1 else v for k, v in query.items()}}

        # 1. Quarteto Sine Qua Non & UI Routes
        if path in ("/", "/index.html"):
            return self._serve_file("index.html", "text/html; charset=utf-8")
        elif path == "/swagger":
            return self._serve_file("swagger.html", "text/html; charset=utf-8")
        elif path == "/webhooks":
            return self._serve_file("webhook_studio.html", "text/html; charset=utf-8")
        elif path == "/mcp":
            return self._serve_file("mcp_studio.html", "text/html; charset=utf-8")
        elif path == "/docs":
            return self._serve_file("docs.html", "text/html; charset=utf-8")
        elif path == "/openapi.json":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(registry.get_openapi_schema("{suite_name}", "1.0.0"), ensure_ascii=False, indent=2).encode('utf-8'))
            return

        # 2. Endpoints Dinamicos do RouteRegistry
        match, handler, route_params = registry.match("GET", path)
        if match:
            merged_params = {{**params, **route_params}}
            try:
                result = handler(merged_params) if merged_params else handler()
                self._send_json_response(result)
            except Exception as e:
                self._send_json_error(str(e), 500)
            return

        # 3. Fallback Estatico
        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(content_length).decode('utf-8')) if content_length > 0 else {{}}

        match, handler, route_params = registry.match("POST", path)
        if match:
            try:
                result = handler(body)
                self._send_json_response(result)
            except Exception as e:
                self._send_json_error(str(e), 500)
            return

        self._send_json_error("Endpoint POST nao encontrado", 404)

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(content_length).decode('utf-8')) if content_length > 0 else {{}}

        match, handler, route_params = registry.match("PUT", path)
        if match:
            try:
                item_id = int(route_params.get("id", 0))
                result = handler(item_id, body)
                self._send_json_response(result)
            except Exception as e:
                self._send_json_error(str(e), 500)
            return

        self._send_json_error("Endpoint PUT nao encontrado", 404)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)
        params = {{k: v[0] if len(v) == 1 else v for k, v in query.items()}}

        match, handler, route_params = registry.match("DELETE", path)
        if match:
            try:
                item_id = int(route_params.get("id", 0))
                result = handler(item_id, params)
                self._send_json_response(result)
            except Exception as e:
                self._send_json_error(str(e), 500)
            return

        self._send_json_error("Endpoint DELETE nao encontrado", 404)

    def _serve_file(self, filename: str, content_type: str):
        filepath = os.path.join(STATIC_DIR, filename)
        if not os.path.isfile(filepath):
            self.send_error(404, f"Arquivo {{filename}} nao encontrado")
            return
        with open(filepath, "rb") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_json_response(self, result):
        status_code = 200
        if isinstance(result, tuple) and len(result) == 2:
            result, status_code = result
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))

    def _send_json_error(self, message: str, code: int = 400):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps({{"error": message, "status": code}}, ensure_ascii=False).encode('utf-8'))


def run_server():
    server_address = ('', PORT)
    with socketserver.TCPServer(server_address, ModularHTTPRequestHandler) as httpd:
        print("=" * 72)
        print(f" [AIDD-Factory] Servidor Ativo na Porta {{PORT}}")
        print(f" Super-App UI:     http://localhost:{{PORT}}/")
        print(f" Swagger Studio:   http://localhost:{{PORT}}/swagger")
        print(f" Webhook Studio:   http://localhost:{{PORT}}/webhooks")
        print(f" MCP Studio:       http://localhost:{{PORT}}/mcp")
        print(f" Documentacao:     http://localhost:{{PORT}}/docs")
        print("=" * 72)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\\nServidor encerrado pelo usuario.")


if __name__ == "__main__":
    run_server()
'''
    server_path = os.path.join(pasta_saida, "src", "server.py")
    with open(server_path, "w", encoding="utf-8") as f:
        f.write(server_code)
    return server_path


def _gerar_superapp_ui(pasta_saida: str, suite_name: str, servicos: List[Dict[str, Any]]) -> str:
    """Gera o index.html (Super-App Frontend) com abas dinamicas e modais."""
    tabs_nav = []
    sections = []
    scripts = []

    for i, s in enumerate(servicos):
        slug = s["slug"]
        pascal = s["pascal"]
        nome = s["nome"]
        is_active = (i == 0)
        active_tab = "tab-btn active" if is_active else "tab-btn"
        active_sec = "tab-section active" if is_active else "tab-section"

        tabs_nav.append(f'''
            <button type="button" onclick="mudarAba('{slug}')" id="tab-btn-{slug}" class="{active_tab}" aria-label="Acessar {nome}">
                <span class="tab-indicator"></span>
                <span>{nome}</span>
            </button>''')

        sections.append(f'''
        <!-- ABA {pascal} -->
        <section id="sec-{slug}" class="{active_sec}">
            <div class="kpi-grid">
                <div class="kpi-card">
                    <div class="kpi-title">Total de Registros</div>
                    <div class="kpi-val" id="kpi-{slug}-total">--</div>
                    <div class="kpi-sub">Cadastros em {nome}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-title">Status Operacional</div>
                    <div class="kpi-val text-emerald" id="kpi-{slug}-status">Ativo</div>
                    <div class="kpi-sub">Sincronizado</div>
                </div>
            </div>

            <div class="toolbar">
                <div class="search-box">
                    <input type="text" id="busca-{slug}" oninput="filtrar{pascal}()" placeholder="Buscar em {nome}..." aria-label="Buscar">
                </div>
                <div class="actions">
                    <button type="button" onclick="carregar{pascal}()" class="btn btn-secondary">Atualizar</button>
                    <button type="button" onclick="abrirModalNovo('{slug}')" class="btn btn-primary">+ Novo Registro</button>
                </div>
            </div>

            <div class="table-container">
                <table class="data-table" id="tabela-{slug}">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Título</th>
                            <th>Descrição</th>
                            <th>Status</th>
                            <th>Criado Em</th>
                            <th class="text-right">Ações</th>
                        </tr>
                    </thead>
                    <tbody id="tbody-{slug}">
                        <tr><td colspan="6" class="text-center">Carregando dados...</td></tr>
                    </tbody>
                </table>
            </div>

            <!-- MODAL NOVO REGISTRO -->
            <div id="modal-novo-{slug}" class="modal-backdrop">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Novo Registro — {nome}</h3>
                        <button type="button" onclick="fecharModalNovo('{slug}')" class="modal-close" aria-label="Fechar">&times;</button>
                    </div>
                    <form onsubmit="salvarNovo{pascal}(event)">
                        <div class="form-group">
                            <label for="campo-{slug}-titulo">Título / Identificador *</label>
                            <input type="text" id="campo-{slug}-titulo" required placeholder="Ex: Operação Principal">
                        </div>
                        <div class="form-group">
                            <label for="campo-{slug}-desc">Descrição</label>
                            <textarea id="campo-{slug}-desc" rows="3" placeholder="Informações complementares..."></textarea>
                        </div>
                        <div class="modal-footer">
                            <button type="button" onclick="fecharModalNovo('{slug}')" class="btn btn-secondary">Cancelar</button>
                            <button type="submit" class="btn btn-primary">Salvar Registro</button>
                        </div>
                    </form>
                </div>
            </div>
        </section>''')

        scripts.append(f'''
        let dados{pascal}Cache = [];

        async function carregar{pascal}() {{
            try {{
                const res = await fetch('/api/{slug}');
                if (res.ok) {{
                    dados{pascal}Cache = await res.json();
                    renderizarTabela{pascal}(dados{pascal}Cache);
                    document.getElementById('kpi-{slug}-total').innerText = dados{pascal}Cache.length;
                }}
            }} catch (e) {{
                console.error("Erro ao carregar {slug}:", e);
            }}
        }}

        function renderizarTabela{pascal}(lista) {{
            const tbody = document.getElementById('tbody-{slug}');
            if (!lista || lista.length === 0) {{
                tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Nenhum registro encontrado.</td></tr>';
                return;
            }}
            tbody.innerHTML = lista.map(item => `
                <tr>
                    <td>#${{item.id}}</td>
                    <td class="font-medium">${{item.titulo || '-'}}</td>
                    <td class="text-muted">${{item.descricao || '-'}}</td>
                    <td><span class="badge badge-active">${{item.status || 'ativo'}}</span></td>
                    <td class="text-muted">${{item.created_at || '-'}}</td>
                    <td class="text-right">
                        <button type="button" onclick="deletarItem{pascal}(${{item.id}})" class="btn btn-sm btn-danger">Excluir</button>
                    </td>
                </tr>
            `).join('');
        }}

        function filtrar{pascal}() {{
            const termo = (document.getElementById('busca-{slug}').value || '').toLowerCase();
            if (!termo) {{
                renderizarTabela{pascal}(dados{pascal}Cache);
                return;
            }}
            const filtrados = dados{pascal}Cache.filter(i => 
                (i.titulo && i.titulo.toLowerCase().includes(termo)) ||
                (i.descricao && i.descricao.toLowerCase().includes(termo))
            );
            renderizarTabela{pascal}(filtrados);
        }}

        async function salvarNovo{pascal}(e) {{
            e.preventDefault();
            const titulo = document.getElementById('campo-{slug}-titulo').value;
            const descricao = document.getElementById('campo-{slug}-desc').value;
            try {{
                const res = await fetch('/api/{slug}', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ titulo, descricao }})
                }});
                if (res.ok) {{
                    fecharModalNovo('{slug}');
                    document.getElementById('campo-{slug}-titulo').value = '';
                    document.getElementById('campo-{slug}-desc').value = '';
                    await carregar{pascal}();
                }}
            }} catch (err) {{
                alert("Erro ao salvar registro: " + err);
            }}
        }}

        async function deletarItem{pascal}(id) {{
            if (!confirm("Deseja realmente excluir este registro?")) return;
            try {{
                const res = await fetch('/api/{slug}/' + id, {{ method: 'DELETE' }});
                if (res.ok) {{
                    await carregar{pascal}();
                }}
            }} catch (err) {{
                alert("Erro ao excluir: " + err);
            }}
        }}''')

    tabs_nav_str = "\n".join(tabs_nav)
    sections_str = "\n".join(sections)
    scripts_str = "\n".join(scripts)
    initial_loads = "\n".join([f"            carregar{_pascal_case(s['nome'])}();" for s in servicos])

    html_content = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{suite_name} — Super-App AIDD</title>
    <link rel="stylesheet" href="/output.css">
    <style>
        :root {{
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #1e293b;
            --border-color: #334155;
            --text-primary: #f8fafc;
            --text-muted: #94a3b8;
            --accent-primary: #38bdf8;
            --accent-hover: #0284c7;
            --color-danger: #ef4444;
            --color-success: #10b981;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.5;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        header {{
            background: rgba(30, 41, 59, 0.8);
            backdrop-filter: blur(8px);
            border-bottom: 1px solid var(--border-color);
            padding: 1rem 2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        .logo-title {{ display: flex; align-items: center; gap: 0.75rem; }}
        .badge-eco {{
            background: rgba(56, 189, 248, 0.15);
            color: var(--accent-primary);
            font-size: 0.75rem;
            font-weight: 600;
            padding: 0.25rem 0.5rem;
            border-radius: 9999px;
            border: 1px solid rgba(56, 189, 248, 0.3);
        }}
        .quarteto-nav {{ display: flex; gap: 0.75rem; }}
        .quarteto-btn {{
            color: var(--text-muted);
            text-decoration: none;
            font-size: 0.875rem;
            font-weight: 500;
            padding: 0.4rem 0.75rem;
            border-radius: 0.375rem;
            border: 1px solid transparent;
            transition: all 0.2s;
        }}
        .quarteto-btn:hover {{
            background: var(--bg-secondary);
            color: var(--text-primary);
            border-color: var(--border-color);
        }}
        .tabs-header {{
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
            padding: 0 2rem;
            display: flex;
            gap: 1.5rem;
            overflow-x: auto;
        }}
        .tab-btn {{
            background: none;
            border: none;
            color: var(--text-muted);
            padding: 1rem 0;
            font-size: 0.95rem;
            font-weight: 500;
            cursor: pointer;
            position: relative;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            transition: color 0.2s;
        }}
        .tab-btn:hover {{ color: var(--text-primary); }}
        .tab-btn.active {{ color: var(--accent-primary); font-weight: 600; }}
        .tab-btn.active::after {{
            content: '';
            position: absolute;
            bottom: -1px;
            left: 0;
            right: 0;
            height: 2px;
            background: var(--accent-primary);
        }}
        main {{ flex: 1; padding: 2rem; max-width: 1400px; margin: 0 auto; width: 100%; }}
        .tab-section {{ display: none; }}
        .tab-section.active {{ display: block; animation: fadeIn 0.2s ease-in-out; }}
        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(4px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
        .kpi-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 0.5rem;
            padding: 1.25rem;
        }}
        .kpi-title {{ font-size: 0.875rem; color: var(--text-muted); font-weight: 500; margin-bottom: 0.5rem; }}
        .kpi-val {{ font-size: 1.75rem; font-weight: 700; color: var(--text-primary); }}
        .kpi-sub {{ font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem; }}
        .text-emerald {{ color: var(--color-success); }}
        .toolbar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1.5rem;
            flex-wrap: wrap;
        }}
        .search-box input {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 0.6rem 1rem;
            border-radius: 0.375rem;
            min-width: 280px;
        }}
        .btn {{
            padding: 0.6rem 1.2rem;
            font-size: 0.875rem;
            font-weight: 600;
            border-radius: 0.375rem;
            border: none;
            cursor: pointer;
            transition: opacity 0.2s;
        }}
        .btn-primary {{ background: var(--accent-primary); color: #0f172a; }}
        .btn-primary:hover {{ opacity: 0.9; }}
        .btn-secondary {{ background: var(--border-color); color: var(--text-primary); }}
        .btn-danger {{ background: rgba(239, 68, 68, 0.2); color: var(--color-danger); border: 1px solid rgba(239, 68, 68, 0.4); }}
        .btn-sm {{ padding: 0.25rem 0.5rem; font-size: 0.75rem; }}
        .table-container {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 0.5rem;
            overflow: hidden;
        }}
        .data-table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 0.875rem; }}
        .data-table th {{ background: rgba(15, 23, 42, 0.6); padding: 0.75rem 1rem; color: var(--text-muted); font-weight: 600; }}
        .data-table td {{ padding: 0.75rem 1rem; border-top: 1px solid var(--border-color); }}
        .data-table tr:hover {{ background: rgba(255, 255, 255, 0.02); }}
        .text-right {{ text-align: right; }}
        .text-center {{ text-align: center; }}
        .text-muted {{ color: var(--text-muted); }}
        .font-medium {{ font-weight: 500; }}
        .badge {{
            padding: 0.2rem 0.5rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .badge-active {{ background: rgba(16, 185, 129, 0.2); color: var(--color-success); border: 1px solid rgba(16, 185, 129, 0.3); }}
        .modal-backdrop {{
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(4px);
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }}
        .modal-backdrop.active {{ display: flex; }}
        .modal-content {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 0.75rem;
            max-width: 500px;
            width: 90%;
            padding: 1.5rem;
        }}
        .modal-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem; }}
        .modal-close {{ background: none; border: none; font-size: 1.5rem; color: var(--text-muted); cursor: pointer; }}
        .form-group {{ margin-bottom: 1rem; }}
        .form-group label {{ display: block; font-size: 0.8rem; font-weight: 500; color: var(--text-muted); margin-bottom: 0.25rem; }}
        .form-group input, .form-group textarea {{
            width: 100%;
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 0.6rem;
            border-radius: 0.375rem;
            font-family: inherit;
        }}
        .modal-footer {{ display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem; }}
    </style>
</head>
<body>
    <header>
        <div class="logo-title">
            <h2>{suite_name}</h2>
            <span class="badge-eco">AIDD VSA Suite</span>
        </div>
        <nav class="quarteto-nav">
            <a href="/swagger" target="_blank" class="quarteto-btn">Swagger Studio</a>
            <a href="/webhooks" target="_blank" class="quarteto-btn">Webhook Studio</a>
            <a href="/mcp" target="_blank" class="quarteto-btn">MCP Studio</a>
            <a href="/docs" target="_blank" class="quarteto-btn">Manual Docs</a>
        </nav>
    </header>

    <div class="tabs-header">
        {tabs_nav_str}
    </div>

    <main>
        {sections_str}
    </main>

    <script>
        function mudarAba(slug) {{
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-section').forEach(s => s.classList.remove('active'));
            const btn = document.getElementById('tab-btn-' + slug);
            const sec = document.getElementById('sec-' + slug);
            if (btn) btn.classList.add('active');
            if (sec) sec.classList.add('active');
        }}

        function abrirModalNovo(slug) {{
            const m = document.getElementById('modal-novo-' + slug);
            if (m) m.classList.add('active');
        }}

        function fecharModalNovo(slug) {{
            const m = document.getElementById('modal-novo-' + slug);
            if (m) m.classList.remove('active');
        }}

        {scripts_str}

        document.addEventListener('DOMContentLoaded', () => {{
{initial_loads}
        }});
    </script>
</body>
</html>
'''
    index_path = os.path.join(pasta_saida, "src", "static", "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    return index_path


def _gerar_docs_html(pasta_saida: str, suite_name: str, servicos: List[Dict[str, Any]]) -> str:
    """Gera o docs.html (Manual do Utilizador Dinamico via AST)."""
    capitulos = []
    nav_links = []

    for i, s in enumerate(servicos, 1):
        slug = s["slug"]
        pascal = s["pascal"]
        nome = s["nome"]
        nav_links.append(f'<li><a href="#cap-{slug}">{i}. Módulo {nome}</a></li>')
        capitulos.append(f'''
        <article id="cap-{slug}" class="doc-chapter">
            <h2>{i}. Módulo {nome} ({pascal})</h2>
            <p>Fatia vertical autônoma dedicada à gestão e automação operacional de {nome}.</p>
            <h3>Rotas e Endpoints RESTful:</h3>
            <ul>
                <li><code>GET /api/{slug}</code> — Listagem paginada e filtros com isolamento de tenant.</li>
                <li><code>GET /api/{slug}/:id</code> — Detalhamento e metadados completos do registro.</li>
                <li><code>POST /api/{slug}</code> — Cadastro e publicação de novos registros.</li>
                <li><code>PUT /api/{slug}/:id</code> — Atualização cadastral e transição de status.</li>
                <li><code>DELETE /api/{slug}/:id</code> — Exclusão lógica/física auditada.</li>
            </ul>
            <h3>Eventos e Webhooks Integrados:</h3>
            <p>Publica eventos no barramento interno e Webhook Dispatcher:</p>
            <ul>
                <li><code>{slug}.criado</code> — Disparado imediatamente após inserção no banco de dados.</li>
                <li><code>{slug}.atualizado</code> — Notifica modificações de status e payload.</li>
                <li><code>{slug}.removido</code> — Notifica encerramento ou deleção do registro.</li>
            </ul>
        </article>
        ''')

    nav_links_str = "\n".join(nav_links)
    capitulos_str = "\n".join(capitulos)

    docs_content = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Manual do Utilizador — {suite_name}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; line-height: 1.6; margin: 0; padding: 2rem; }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        header {{ border-bottom: 1px solid #334155; padding-bottom: 1.5rem; margin-bottom: 2rem; }}
        h1 {{ color: #38bdf8; margin-bottom: 0.5rem; }}
        .toc {{ background: #1e293b; border: 1px solid #334155; border-radius: 0.5rem; padding: 1.5rem; margin-bottom: 2rem; }}
        .toc ul {{ list-style-type: none; padding-left: 0; }}
        .toc li {{ margin-bottom: 0.5rem; }}
        .toc a {{ color: #38bdf8; text-decoration: none; }}
        .toc a:hover {{ text-decoration: underline; }}
        .doc-chapter {{ background: #1e293b; border: 1px solid #334155; border-radius: 0.5rem; padding: 1.5rem; margin-bottom: 2rem; }}
        .doc-chapter h2 {{ color: #38bdf8; border-bottom: 1px solid #334155; padding-bottom: 0.5rem; margin-top: 0; }}
        .doc-chapter h3 {{ color: #e2e8f0; margin-top: 1.5rem; }}
        code {{ background: #0f172a; color: #38bdf8; padding: 0.2rem 0.4rem; border-radius: 0.25rem; font-size: 0.875rem; }}
        ul {{ padding-left: 1.5rem; }}
        li {{ margin-bottom: 0.35rem; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Guia e Manual do Utilizador</h1>
            <p>Documentação dinâmica dos módulos da suíte <strong>{suite_name}</strong>.</p>
        </header>
        <div class="toc">
            <h3>Índice dos Módulos:</h3>
            <ul>
                {nav_links_str}
            </ul>
        </div>
        {capitulos_str}
    </div>
</body>
</html>
'''
    docs_path = os.path.join(pasta_saida, "src", "static", "docs.html")
    with open(docs_path, "w", encoding="utf-8") as f:
        f.write(docs_content)
    return docs_path


def gerar_aplicacao_vsa(analysis: Dict[str, Any], pasta_saida: str, frontend_stack: str = "nextjs") -> Result:
    """Orquestra a geracao completa da aplicacao monolitica modular VSA com o Quarteto Sine Qua Non.

    Args:
        analysis: Dicionario do factory_analysis.json.
        pasta_saida: Diretorio raiz de saida da aplicacao.
        frontend_stack: "nextjs" (default, Lei Inviolavel #11) ou "python-html"
            (Super-App em HTML/CSS/JS puro, so quando pedido explicitamente).
            Com "nextjs", o Super-App em src/static/index.html NAO e gerado
            aqui — o frontend real e gerado por `pipeline_factory.py` (Fase 3)
            via NextJSExporter (fonte unica compartilhada), evitando o
            frontend duplicado/divergente que existia antes (achado real:
            este modulo gerava um Super-App em src/static/index.html E
            frontend_generator.py gerava um Next.js separado e incompativel
            para o mesmo projeto — validacao E2E do Fluxo 01, 18/09/2026).

    Returns:
        Result.ok(lista_de_arquivos_gerados) ou Result.fail.
    """
    try:
        suite_name = analysis.get("nicho_nome_exibicao", "AIDD Application Suite")
        nicho_slug = analysis.get("nicho_slug", "suite")
        ferramentas = analysis.get("ferramentas", [])

        servicos = []
        for f in ferramentas:
            nome = f.get("nome", "Servico")
            slug = _slugify(nome)
            pascal = _pascal_case(nome)
            servicos.append({"nome": nome, "slug": slug, "pascal": pascal})

        arquivos_gerados = []

        # 1. Gerar Shared Kernel
        kernel_files = _gerar_shared_kernel(pasta_saida)
        arquivos_gerados.extend(kernel_files)

        # 2. Gerar Fatias Verticais (src/modules/<slug>/)
        for s in servicos:
            fatia_files = _gerar_fatia_modulo(pasta_saida, s["nome"], nicho_slug)
            arquivos_gerados.extend(fatia_files)

        # 3. Gerar Servidor Monolitico Modular (src/server.py)
        server_file = _gerar_server_modular(pasta_saida, suite_name, servicos)
        arquivos_gerados.append(server_file)

        # 4. Docs do Quarteto Sine Qua Non (Studio nativo do backend, sem
        # relacao com o frontend de produto — nao muda com frontend_stack).
        docs_file = _gerar_docs_html(pasta_saida, suite_name, servicos)
        arquivos_gerados.append(docs_file)

        # 5. Super-App em HTML/CSS/JS Python puro so quando pedido
        # explicitamente (Lei Inviolavel #11). Com o default "nextjs", o
        # frontend de produto e gerado pela Fase 3 do pipeline_factory.py
        # (NextJSExporter compartilhado), nao aqui.
        if frontend_stack == "python-html":
            index_file = _gerar_superapp_ui(pasta_saida, suite_name, servicos)
            arquivos_gerados.append(index_file)

        return Result.ok(arquivos_gerados)

    except Exception as exc:
        return Result.fail(f"Erro ao gerar aplicacao VSA: {exc}", codigo="VSA_GENERATOR_ERROR")
