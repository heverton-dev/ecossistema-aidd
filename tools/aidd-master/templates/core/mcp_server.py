# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.1 Enterprise — Shared Kernel MCP Server (mcp_server.py)
=============================================================================
Servidor MCP nativo sobre o SDK oficial do Model Context Protocol
(`modelcontextprotocol/python-sdk`): transporte, negociação de protocolo e
códigos de erro JSON-RPC 2.0 ficam a cargo do SDK (`mcp.server.fastmcp`).

A classe MCPServer mantém a mesma superfície pública usada por server.py,
webhooks.py, compose_suite.py e pelos gates:
  - register_tool(name, description, input_schema, handler)
  - register_injected_tools(mcp_dir=None) -> int
  - register_module_tools(module_slug, module_name)
  - get_tools_manifest() -> List[dict]
  - execute_tool(name, args) -> dict
  - handle_json_rpc(request_data) -> dict  (camada de compat JSON-RPC 2.0)
  - handle_request  (alias de handle_json_rpc)
  - get_studio_html(title) -> str
  - EnterpriseMCPServer / LogisticaMCPServer / AIDD_EnterpriseMCPServer

Integração SDK oficial: `mcp` (FastMCP) expõe as ferramentas registradas via
`list_tools()` / `call_tool()` assíncronos — protocolo JSON-RPC 2.0, stdio e
HTTP tratados pelo SDK. A camada de compat `handle_json_rpc` permanece para
os pontos de integração HTTP internos (server.py / webhooks.py) e para os
gates que inspecionam o método.
"""

import json
import sqlite3
import sys
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable

# SDK oficial do MCP (modelcontextprotocol/python-sdk).
# Import condicional: o núcleo compartilhado também roda em ambientes onde
# o SDK ainda não foi instalado (ex.: projetos gerados com requirements
# mínimos). Nesses casos o servidor continua 100% funcional via JSON-RPC
# próprio (handle_json_rpc), e o acesso ao SDK fica indisponível (mcp = None).
try:
    from mcp.server.fastmcp import FastMCP
    from mcp.types import TextContent
except ImportError:  # pragma: no cover - ambiente sem o SDK oficial
    FastMCP = None
    TextContent = None


def _sanitize_ident(ident: str) -> str:
    """Valida e sanitiza identificadores de tabelas e colunas."""
    clean = re.sub(r'[^a-zA-Z0-9_]', '', str(ident).strip())
    if not clean:
        raise ValueError(f"Identificador inválido: {ident}")
    return clean


class MCPServer:
    """Servidor Universal Model Context Protocol (MCP) para Monólitos Modulares.

    Registro de ferramentas continua centralizado nesta classe (mesma API de
    antes); o protocolo (list_tools/call_tool/stdio/HTTP) passa a ser served
    pelo SDK oficial via `build_fastmcp()`/`run_stdio_server()`.
    """

    TOOLS = [
        {
            "name": "sistema_saude_status",
            "description": "Retorna o status operacional, versão do framework e módulos ativos no ecossistema.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "detalhado": {"type": "boolean", "description": "Se verdadeiro, inclui métricas de tabelas e contagem de registros"}
                }
            }
        },
        {
            "name": "sistema_executar_consulta",
            "description": "Executa uma consulta SQL segura de leitura (SELECT) no banco de dados SQLite WAL da suíte.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "tabela": {"type": "string", "description": "Nome da tabela a ser consultada"},
                    "limite": {"type": "integer", "description": "Número máximo de registros a retornar (default 50)"}
                },
                "required": ["tabela"]
            }
        }
    ]

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "suite.db")
        self._handlers: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {}
        self.tools: List[Dict[str, Any]] = [t.copy() for t in self.TOOLS]

        self._handlers["sistema_saude_status"] = self._handle_saude_status
        self._handlers["sistema_executar_consulta"] = self._handle_executar_consulta

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def register_tool(self, name: str, description: str, input_schema: Dict[str, Any], handler: Optional[Callable] = None):
        """Registra uma nova ferramenta no servidor MCP."""
        tool_def = {
            "name": name,
            "description": description,
            "inputSchema": input_schema if input_schema and input_schema.get("type") == "object" else {"type": "object", "properties": {}}
        }
        self.tools = [t for t in self.tools if t["name"] != name]
        self.tools.append(tool_def)
        if handler:
            self._handlers[name] = handler

    def register_module_tools(self, module_slug: str, module_name: str):
        """Registra automaticamente ferramentas CRUD para um módulo/fatia vertical."""
        slug = _sanitize_ident(module_slug.lower().strip())
        pascal = module_name

        self.register_tool(
            name=f"{slug}_listar",
            description=f"Lista todos os registros cadastrados no módulo {pascal}.",
            input_schema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "Filtrar por status (ex: ativo, inativo, concluido)"},
                    "apenas_ativos": {"type": "boolean", "description": "Se verdadeiro, filtra apenas itens ativos"}
                }
            },
            handler=lambda args, s=slug: self._generic_listar(s, args)
        )

        self.register_tool(
            name=f"{slug}_obter_por_id",
            description=f"Recupera os detalhes completos de um registro do módulo {pascal} pelo ID.",
            input_schema={
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "description": "ID do registro a consultar"}
                },
                "required": ["id"]
            },
            handler=lambda args, s=slug: self._generic_obter(s, args)
        )

        self.register_tool(
            name=f"{slug}_criar",
            description=f"Cria um novo registro no módulo {pascal} e emite evento no EventBus.",
            input_schema={
                "type": "object",
                "properties": {
                    "titulo": {"type": "string", "description": "Título identificador do item"},
                    "descricao": {"type": "string", "description": "Descrição detalhada"},
                    "status": {"type": "string", "description": "Status inicial (default 'ativo')"},
                    "dados": {"type": "object", "description": "Dados customizados em formato JSON"}
                },
                "required": ["titulo"]
            },
            handler=lambda args, s=slug: self._generic_criar(s, args)
        )

        self.register_tool(
            name=f"{slug}_atualizar",
            description=f"Atualiza as informações de um registro existente no módulo {pascal}.",
            input_schema={
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "description": "ID do registro a atualizar"},
                    "titulo": {"type": "string", "description": "Novo título"},
                    "descricao": {"type": "string", "description": "Nova descrição"},
                    "status": {"type": "string", "description": "Novo status"}
                },
                "required": ["id"]
            },
            handler=lambda args, s=slug: self._generic_atualizar(s, args)
        )

        self.register_tool(
            name=f"{slug}_deletar",
            description=f"Exclui permanentemente um registro do módulo {pascal}.",
            input_schema={
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "description": "ID do registro a remover"}
                },
                "required": ["id"]
            },
            handler=lambda args, s=slug: self._generic_deletar(s, args)
        )

    def _handle_saude_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        detalhado = args.get("detalhado", False)
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tabelas_raw = cur.fetchall()
            tabelas = [r[0] for r in tabelas_raw]
            info_tabelas = {}
            if detalhado:
                for t in tabelas:
                    clean_t = _sanitize_ident(t)
                    count_sql = "SELECT COUNT(*) FROM " + clean_t
                    cur.execute(count_sql)
                    res = cur.fetchone()
                    info_tabelas[t] = res[0] if res else 0

            return {
                "sucesso": True,
                "status": "online",
                "versao": "4.1.0 Enterprise",
                "total_ferramentas_mcp": len(self.tools),
                "tabelas_ativas": tabelas,
                "detalhes": info_tabelas if detalhado else None
            }

    def _handle_executar_consulta(self, args: Dict[str, Any]) -> Dict[str, Any]:
        tabela = _sanitize_ident(args.get("tabela", ""))
        limite = int(args.get("limite", 50))
        if not tabela:
            return {"sucesso": False, "erro": "Nome da tabela é obrigatório"}

        with self._get_conn() as conn:
            cur = conn.cursor()
            query_sql = "SELECT * FROM " + tabela + " LIMIT ?"
            cur.execute(query_sql, (limite,))
            rows = cur.fetchall()
            return {
                "sucesso": True,
                "total": len(rows),
                "registros": [dict(r) for r in rows]
            }

    def _generic_listar(self, slug: str, args: Dict[str, Any]) -> Dict[str, Any]:
        table = "mod_" + _sanitize_ident(slug)
        status = args.get("status")
        apenas_ativos = args.get("apenas_ativos", True)
        with self._get_conn() as conn:
            cur = conn.cursor()
            conditions = ["1=1"]
            params = []
            if apenas_ativos:
                conditions.append("ativo = 1")
            if status:
                conditions.append("status = ?")
                params.append(status)

            where_clause = " AND ".join(conditions)
            sql = "SELECT * FROM " + table + " WHERE " + where_clause + " ORDER BY id DESC"
            try:
                cur.execute(sql, params)
                rows = cur.fetchall()
                return {"sucesso": True, "modulo": slug, "total": len(rows), "itens": [dict(r) for r in rows]}
            except sqlite3.Error as e:
                return {"sucesso": False, "modulo": slug, "erro": str(e)}

    def _generic_obter(self, slug: str, args: Dict[str, Any]) -> Dict[str, Any]:
        table = "mod_" + _sanitize_ident(slug)
        item_id = int(args.get("id", 0))
        with self._get_conn() as conn:
            cur = conn.cursor()
            sql = "SELECT * FROM " + table + " WHERE id = ?"
            try:
                cur.execute(sql, (item_id,))
                row = cur.fetchone()
                if row:
                    return {"sucesso": True, "modulo": slug, "item": dict(row)}
                return {"sucesso": False, "modulo": slug, "erro": "Registro não encontrado"}
            except sqlite3.Error as e:
                return {"sucesso": False, "modulo": slug, "erro": str(e)}

    def _generic_criar(self, slug: str, args: Dict[str, Any]) -> Dict[str, Any]:
        table = "mod_" + _sanitize_ident(slug)
        titulo = args.get("titulo", "").strip()
        descricao = args.get("descricao", "")
        status = args.get("status", "ativo")
        dados = json.dumps(args.get("dados", {}), ensure_ascii=False)
        with self._get_conn() as conn:
            cur = conn.cursor()
            sql = "INSERT INTO " + table + " (titulo, descricao, dados_json, status, ativo) VALUES (?, ?, ?, ?, 1)"
            try:
                cur.execute(sql, (titulo, descricao, dados, status))
                conn.commit()
                return {"sucesso": True, "modulo": slug, "id": cur.lastrowid, "titulo": titulo}
            except sqlite3.Error as e:
                return {"sucesso": False, "modulo": slug, "erro": str(e)}

    def _generic_atualizar(self, slug: str, args: Dict[str, Any]) -> Dict[str, Any]:
        table = "mod_" + _sanitize_ident(slug)
        item_id = int(args.get("id", 0))
        with self._get_conn() as conn:
            cur = conn.cursor()
            sel_sql = "SELECT * FROM " + table + " WHERE id = ?"
            try:
                cur.execute(sel_sql, (item_id,))
                row = cur.fetchone()
                if not row:
                    return {"sucesso": False, "erro": "Registro não encontrado"}
                novo_titulo = args.get("titulo", row["titulo"])
                nova_desc = args.get("descricao", row["descricao"])
                novo_status = args.get("status", row["status"])
                up_sql = "UPDATE " + table + " SET titulo = ?, descricao = ?, status = ?, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?"
                cur.execute(up_sql, (novo_titulo, nova_desc, novo_status, item_id))
                conn.commit()
                return {"sucesso": True, "modulo": slug, "id": item_id, "status": novo_status}
            except sqlite3.Error as e:
                return {"sucesso": False, "modulo": slug, "erro": str(e)}

    def _generic_deletar(self, slug: str, args: Dict[str, Any]) -> Dict[str, Any]:
        table = "mod_" + _sanitize_ident(slug)
        item_id = int(args.get("id", 0))
        with self._get_conn() as conn:
            cur = conn.cursor()
            sql = "DELETE FROM " + table + " WHERE id = ?"
            try:
                cur.execute(sql, (item_id,))
                conn.commit()
                return {"sucesso": True, "modulo": slug, "id": item_id}
            except sqlite3.Error as e:
                return {"sucesso": False, "modulo": slug, "erro": str(e)}

    def get_tools_manifest(self) -> List[Dict[str, Any]]:
        """Retorna o manifesto de ferramentas no formato padrão MCP."""
        return self.tools

    def execute_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Executa uma ferramenta registrada."""
        if name in self._handlers:
            try:
                return self._handlers[name](args)
            except Exception as e:
                return {"sucesso": False, "erro": f"Erro na execução da ferramenta '{name}': {str(e)}"}

        return {"sucesso": False, "erro": f"Ferramenta '{name}' não encontrada no servidor MCP"}

    # =========================================================================
    # SDK oficial do MCP (modelcontextprotocol/python-sdk)
    # =========================================================================

    def build_fastmcp(self):
        """Constrói um servidor FastMCP (SDK oficial) expondo as ferramentas
        registradas nesta instância.

        As ferramentas são expostas com o MESMO inputSchema declarado no
        registro (JSON Schema original), e `call_tool` despacha para os
        handlers existentes via `execute_tool`. Protocolo (JSON-RPC 2.0,
        initialize/ping, stdio/streamable-http) fica a cargo do SDK.
        """
        if FastMCP is None:
            raise ImportError(
                "O SDK oficial do MCP não está instalado. Instale com: pip install mcp"
            )
        server = self

        class _RegistryFastMCP(FastMCP):
            """FastMCP cujo catálogo de ferramentas é o registro vivo do MCPServer."""

            async def list_tools(self):
                from mcp.types import Tool as MCPTool
                return [
                    MCPTool(
                        name=t["name"],
                        description=t.get("description", ""),
                        inputSchema=t.get("inputSchema", {"type": "object", "properties": {}}),
                    )
                    for t in server.get_tools_manifest()
                ]

            async def call_tool(self, name, arguments):
                resultado = server.execute_tool(name, dict(arguments or {}))
                texto = json.dumps(resultado, ensure_ascii=False, indent=2, default=str)
                if TextContent is not None:
                    return [TextContent(type="text", text=texto)]
                return [{"type": "text", "text": texto}]

        return _RegistryFastMCP(
            "aidd-suite",
            instructions="Servidor MCP da suíte AIDD (núcleo compartilhado).",
        )

    # =========================================================================
    # Camada de compatibilidade JSON-RPC 2.0 (HTTP interno e gates)
    # =========================================================================

    def handle_json_rpc(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa requisições JSON-RPC 2.0 (tools/list e tools/call).

        Mantida para os pontos de integração HTTP internos (server.py /
        webhooks.py) que já falam JSON-RPC diretamente e para os gates que
        inspecionam este método. O transporte oficial (stdio / streamable-http)
        usa o SDK via build_fastmcp()/run_stdio_server().
        """
        req_id = request_data.get("id", 1)
        method = request_data.get("method")
        params = request_data.get("params", {})

        if method in ("tools/list", "toolsList"):
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": self.get_tools_manifest()}
            }
        elif method in ("tools/call", "toolsCall"):
            name = params.get("name")
            args = params.get("arguments", {})
            try:
                res = self.execute_tool(name, args)
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(res, ensure_ascii=False, indent=2)}]
                    }
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32603, "message": str(e)}
                }
        elif method in ("initialize", "ping"):
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {"name": "aidd-enterprise-mcp", "version": "4.1.0"},
                    "capabilities": {"tools": {}}
                }
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Método '{method}' não suportado"}
            }

    # Alias para compatibilidade com gates
    handle_request = handle_json_rpc

    def get_studio_html(self, title: str = "AIDD Enterprise — MCP Server Studio") -> str:
        """Gera a interface Web Impeccable para o Studio de Ferramentas MCP (/mcp) sem CDNs externas."""
        tools = self.get_tools_manifest()
        claude_config = {
            "mcpServers": {
                "aidd-suite": {
                    "command": "python",
                    "args": ["-m", "src.core.mcp_server"],
                    "env": {"PYTHONPATH": "."}
                }
            }
        }
        claude_config_json = json.dumps(claude_config, indent=2)

        cards_html = []
        for t in tools:
            schema_json = json.dumps(t.get("inputSchema", {}), indent=2, ensure_ascii=False)
            t_name = t["name"]
            t_desc = t.get("description", "")
            cards_html.append(f"""
                <div class="tool-card" data-name="{t_name.lower()}">
                    <div class="tool-header">
                        <span class="tool-name">{t_name}</span>
                        <span class="badge badge-purple">Tool</span>
                    </div>
                    <p class="tool-desc">{t_desc}</p>
                    <div class="schema-label">Input Schema</div>
                    <pre class="schema-box">{schema_json}</pre>
                    <button class="btn btn-sm btn-outline" onclick="selectTool('{t_name}')">Usar no Console &rarr;</button>
                </div>
            """)
        cards_str = "\n".join(cards_html)

        _html = (Path(__file__).parent / "mcp_studio.html").read_text(encoding="utf-8")
        _html = _html.replace("__TITLE__", str(title))
        _html = _html.replace("__TOOLS_COUNT__", str(len(tools)))
        _html = _html.replace("__CLAUDE_CONFIG_JSON__", str(claude_config_json))
        _html = _html.replace("__CARDS_STR__", str(cards_str))
        _html = _html.replace("__TOOLS_JSON__", str(json.dumps(tools, ensure_ascii=False)))
        return _html


# Aliases para compatibilidade reversa
EnterpriseMCPServer = MCPServer
LogisticaMCPServer = MCPServer
AIDD_EnterpriseMCPServer = MCPServer


def run_stdio_server(db_path: str):
    """Executa o servidor MCP via Standard I/O (STDIO) sobre o SDK oficial.

    Antes: loop JSON-RPC manual sobre sys.stdin. Agora: o próprio SDK oficial
    (mcp.server.fastmcp) implementa o transporte stdio e o protocolo JSON-RPC
    2.0 completo (initialize, ping, tools/list, tools/call, códigos de erro).
    Se o SDK não estiver disponível, cai no loop JSON-RPC manual legado.
    """
    server = MCPServer(db_path)
    if FastMCP is not None:
        fastmcp = server.build_fastmcp()
        fastmcp.run(transport="stdio")
        return

    # Fallback legado (ambiente sem o SDK oficial instalado)
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line)
            resp = server.handle_json_rpc(req)
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
        except Exception as e:
            err = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": f"Parse error: {str(e)}"}}
            sys.stdout.write(json.dumps(err) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "suite.db")
    run_stdio_server(db_file)
