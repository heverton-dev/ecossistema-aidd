# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.1 Enterprise — Shared Kernel MCP Server (mcp_server.py)
=============================================================================
Servidor nativo Model Context Protocol (MCP) compatível com JSON-RPC 2.0.
Permite integração direta com Claude Desktop, Cursor, Antigravity e agentes autônomos.
Suporta registro dinâmico de ferramentas para módulos e fatias verticais.
"""

import json
import sqlite3
import sys
import os
import re
from typing import Dict, List, Any, Optional, Callable


def _sanitize_ident(ident: str) -> str:
    """Valida e sanitiza identificadores de tabelas e colunas."""
    clean = re.sub(r'[^a-zA-Z0-9_]', '', str(ident).strip())
    if not clean:
        raise ValueError(f"Identificador inválido: {ident}")
    return clean


class MCPServer:
    """Servidor Universal Model Context Protocol (MCP) para Monólitos Modulares."""

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
            except Exception as e:
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
            except Exception as e:
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
            except Exception as e:
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
            except Exception as e:
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
            except Exception as e:
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

    def handle_json_rpc(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa requisições JSON-RPC 2.0 (tools/list e tools/call)."""
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

        return f"""<!DOCTYPE html>
<html lang="pt-BR" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        :root {{
            --bg-base: #020617;
            --bg-surface: #0f172a;
            --bg-card: #090d16;
            --border: #1e293b;
            --border-highlight: #334155;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --primary: #7c3aed;
            --primary-hover: #6d28d9;
            --sky: #38bdf8;
            --emerald: #10b981;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background-color: var(--bg-base);
            color: var(--text-main);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        ::-webkit-scrollbar {{ width: 4px; height: 4px; }}
        ::-webkit-scrollbar-track {{ background: var(--bg-base); }}
        ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 2px; }}
        
        header {{
            height: 56px;
            background: rgba(15, 23, 42, 0.95);
            border-bottom: 1px solid var(--border);
            padding: 0 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 50;
        }}
        .brand {{ display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 14px; color: #fff; }}
        .pulse-dot {{ width: 8px; height: 8px; background: var(--emerald); border-radius: 50%; }}
        .badge {{ display: inline-flex; align-items: center; padding: 2px 8px; border-radius: 9999px; font-size: 11px; font-weight: 700; }}
        .badge-purple {{ background: rgba(168,85,247,.15); color: #c084fc; border: 1px solid rgba(168,85,247,.3); }}
        .badge-blue {{ background: rgba(56,189,248,.15); color: #38bdf8; border: 1px solid rgba(56,189,248,.3); }}
        .badge-green {{ background: rgba(16,185,129,.15); color: #34d399; border: 1px solid rgba(16,185,129,.3); }}
        
        .nav-links {{ display: flex; gap: 8px; }}
        .nav-links a {{ color: var(--text-muted); text-decoration: none; font-size: 12px; padding: 6px 12px; border-radius: 6px; border: 1px solid transparent; }}
        .nav-links a:hover, .nav-links a.active {{ color: #fff; background: #1e293b; border-color: var(--border-highlight); }}
        
        main {{ max-width: 1300px; width: 100%; margin: 0 auto; padding: 28px 24px; flex: 1; display: flex; flex-direction: column; gap: 20px; }}
        
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; }}
        .stat-card {{ background: var(--bg-surface); border: 1px solid var(--border); border-radius: 10px; padding: 16px; }}
        .stat-card .title {{ font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--text-muted); letter-spacing: .5px; }}
        .stat-card .val {{ font-size: 22px; font-weight: 800; color: #fff; margin-top: 4px; }}
        
        .panel {{ background: var(--bg-surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px; display: flex; flex-direction: column; gap: 14px; }}
        .panel-header {{ display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--border); padding-bottom: 12px; }}
        .panel-title {{ font-size: 14px; font-weight: 700; color: #fff; }}
        
        .grid-2col {{ display: grid; grid-template-columns: 1.2fr 1fr; gap: 20px; }}
        @media(max-width:960px){{ .grid-2col {{ grid-template-columns: 1fr; }} }}
        
        .search-bar {{ width: 100%; padding: 10px 14px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; color: #fff; font-size: 13px; outline: none; }}
        .search-bar:focus {{ border-color: var(--primary); }}
        
        .tools-container {{ display: grid; grid-template-columns: 1fr; gap: 12px; max-height: 540px; overflow-y: auto; padding-right: 4px; }}
        .tool-card {{ background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 14px; display: flex; flex-direction: column; gap: 8px; }}
        .tool-header {{ display: flex; align-items: center; justify-content: space-between; }}
        .tool-name {{ font-family: ui-monospace, monospace; font-size: 13px; font-weight: 700; color: #c084fc; }}
        .tool-desc {{ font-size: 12px; color: var(--text-muted); line-height: 1.4; }}
        .schema-label {{ font-size: 10px; font-weight: 700; text-transform: uppercase; color: #64748b; }}
        .schema-box {{ background: #020617; border: 1px solid var(--border); border-radius: 6px; padding: 8px; font-family: ui-monospace, monospace; font-size: 11px; color: var(--text-muted); overflow-x: auto; max-height: 80px; }}
        
        .btn {{ display: inline-flex; align-items: center; justify-content: center; padding: 8px 16px; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; border: none; }}
        .btn-primary {{ background: var(--primary); color: #fff; }}
        .btn-primary:hover {{ background: var(--primary-hover); }}
        .btn-outline {{ background: transparent; border: 1px solid var(--border-highlight); color: #cbd5e1; }}
        .btn-outline:hover {{ background: #1e293b; color: #fff; }}
        .btn-sm {{ padding: 4px 10px; font-size: 11px; }}
        
        .form-group {{ display: flex; flex-direction: column; gap: 6px; }}
        .form-group label {{ font-size: 11px; font-weight: 600; color: var(--text-muted); }}
        .form-control {{ padding: 8px 12px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 6px; color: #fff; font-size: 12px; font-family: inherit; outline: none; }}
        .form-control:focus {{ border-color: var(--primary); }}
        textarea.form-control {{ font-family: ui-monospace, monospace; min-height: 120px; }}
        .console-output {{ background: #020617; border: 1px solid var(--border); border-radius: 6px; padding: 12px; min-height: 150px; max-height: 260px; overflow-y: auto; font-family: ui-monospace, monospace; font-size: 11px; color: var(--sky); white-space: pre-wrap; }}
        .config-box {{ background: var(--bg-card); border: 1px solid var(--border); border-radius: 6px; padding: 12px; font-family: ui-monospace, monospace; font-size: 11px; color: var(--text-muted); overflow-x: auto; }}
    </style>
</head>
<body>
    <header>
        <div class="brand"><span class="pulse-dot"></span> {title} <span class="badge badge-purple">v5.1</span></div>
        <div class="nav-links">
            <a href="/">App</a>
            <a href="/docs">Swagger</a>
            <a href="/webhooks">Webhooks</a>
            <a href="/mcp" class="active">MCP Studio</a>
            <a href="/metrics">Metrics</a>
        </div>
    </header>
    <main>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="title">Ferramentas Registradas</div>
                <div class="val">{len(tools)} Tools</div>
            </div>
            <div class="stat-card">
                <div class="title">Protocolo Nativo</div>
                <div class="val">JSON-RPC 2.0</div>
            </div>
            <div class="stat-card">
                <div class="title">Transportes</div>
                <div class="val">HTTP & STDIO</div>
            </div>
            <div class="stat-card">
                <div class="title">Conexão LLM</div>
                <div class="val">Claude & Cursor</div>
            </div>
        </div>

        <div class="panel">
            <div class="panel-header">
                <span class="panel-title">Configuração Claude Desktop & Cursor (claude_desktop_config.json)</span>
                <button class="btn btn-sm btn-outline" onclick="copiarConfig()">Copiar JSON</button>
            </div>
            <pre class="config-box" id="claude-config-text">{claude_config_json}</pre>
        </div>

        <div class="grid-2col">
            <div class="panel">
                <div class="panel-header">
                    <span class="panel-title">Catálogo de Ferramentas ({len(tools)})</span>
                </div>
                <input type="text" class="search-bar" placeholder="Filtrar ferramentas..." oninput="filtrarTools(this.value)">
                <div class="tools-container" id="tools-list">
                    {cards_str}
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">
                    <span class="panel-title">Console Interativo JSON-RPC 2.0</span>
                    <span class="badge badge-green" id="rpc-status">Pronto</span>
                </div>
                <div class="form-group">
                    <label>Ferramenta</label>
                    <select class="form-control" id="tool-select" onchange="onToolChange(this.value)">
                    </select>
                </div>
                <div class="form-group">
                    <label>Argumentos (JSON)</label>
                    <textarea class="form-control" id="tool-args">{{}}</textarea>
                </div>
                <button class="btn btn-primary" onclick="executarToolRpc()" id="btn-run">Executar Ferramenta (tools/call)</button>
                <div class="form-group">
                    <label>Resposta do Servidor</label>
                    <div class="console-output" id="rpc-output">// Selecione uma ferramenta e clique em Executar</div>
                </div>
            </div>
        </div>
    </main>

    <script>
    const TOOLS_LIST = {json.dumps(tools, ensure_ascii=False)};
    
    function initSelect() {{
        const sel = document.getElementById('tool-select');
        sel.innerHTML = '';
        TOOLS_LIST.forEach(t => {{
            const opt = document.createElement('option');
            opt.value = t.name;
            opt.textContent = t.name;
            sel.appendChild(opt);
        }});
        if (TOOLS_LIST.length > 0) onToolChange(TOOLS_LIST[0].name);
    }}

    function onToolChange(name) {{
        const tool = TOOLS_LIST.find(t => t.name === name);
        const sample = {{}};
        if (tool && tool.inputSchema && tool.inputSchema.properties) {{
            for (const [k, v] of Object.entries(tool.inputSchema.properties)) {{
                sample[k] = v.type === 'integer' || v.type === 'number' ? 1 : (v.type === 'boolean' ? true : "exemplo");
            }}
        }}
        document.getElementById('tool-args').value = JSON.stringify(sample, null, 2);
    }}

    function selectTool(name) {{
        const sel = document.getElementById('tool-select');
        sel.value = name;
        onToolChange(name);
        sel.scrollIntoView({{behavior: 'smooth', block: 'center'}});
    }}

    function filtrarTools(q) {{
        const query = q.toLowerCase().trim();
        document.querySelectorAll('.tool-card').forEach(c => {{
            const name = c.getAttribute('data-name');
            c.style.display = name.includes(query) ? 'flex' : 'none';
        }});
    }}

    function copiarConfig() {{
        const text = document.getElementById('claude-config-text').textContent;
        navigator.clipboard.writeText(text).then(() => alert('Configuração copiada!'));
    }}

    async function executarToolRpc() {{
        const name = document.getElementById('tool-select').value;
        const argsRaw = document.getElementById('tool-args').value;
        const outBox = document.getElementById('rpc-output');
        const status = document.getElementById('rpc-status');
        let args = {{}};
        try {{
            args = JSON.parse(argsRaw);
        }} catch(e) {{
            outBox.textContent = "Erro JSON: " + e.message;
            return;
        }}

        status.textContent = "Enviando...";
        status.className = "badge badge-blue";

        try {{
            const t0 = performance.now();
            const res = await fetch('/mcp', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{
                    jsonrpc: "2.0",
                    method: "tools/call",
                    params: {{ name: name, arguments: args }},
                    id: Date.now()
                }})
            }});
            const data = await res.json();
            const ms = (performance.now() - t0).toFixed(1);
            outBox.textContent = JSON.stringify(data, null, 2);
            status.textContent = res.ok ? `HTTP ${{res.status}} (${{ms}}ms)` : `Erro ${{res.status}}`;
            status.className = res.ok ? "badge badge-green" : "badge badge-purple";
        }} catch(err) {{
            outBox.textContent = "Erro de conexão: " + err.message;
            status.textContent = "Falha";
            status.className = "badge badge-purple";
        }}
    }}

    initSelect();
    </script>
</body>
</html>"""


# Aliases para compatibilidade reversa
EnterpriseMCPServer = MCPServer
LogisticaMCPServer = MCPServer
AIDD_EnterpriseMCPServer = MCPServer


def run_stdio_server(db_path: str):
    """Executa o servidor MCP via Standard I/O (STDIO) para Claude Desktop."""
    server = MCPServer(db_path)
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
