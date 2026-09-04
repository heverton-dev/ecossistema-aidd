import json

class RouteRegistry:
    def __init__(self):
        self.routes = {"GET": {}, "POST": {}, "PUT": {}, "DELETE": {}, "PATCH": {}}
        self.endpoints = []

    def _normalize_responses(self, responses, sample_response):
        if responses and isinstance(responses, dict):
            norm = {}
            for code, r in responses.items():
                code_str = str(code)
                if isinstance(r, dict):
                    if "content" in r or "description" in r:
                        norm[code_str] = {
                            "description": r.get("description", "Resposta do servidor"),
                            "content": r.get("content", {"application/json": {"example": r}})
                        }
                    else:
                        norm[code_str] = {
                            "description": "Sucesso" if code_str == "200" else f"Código {code_str}",
                            "content": {"application/json": {"example": r}}
                        }
                else:
                    norm[code_str] = {
                        "description": "Sucesso" if code_str == "200" else f"Código {code_str}",
                        "content": {"application/json": {"example": r}}
                    }
            return norm

        if sample_response is not None:
            return {
                "200": {
                    "description": "Operação realizada com sucesso",
                    "content": {"application/json": {"example": sample_response}}
                },
                "400": {
                    "description": "Requisição inválida ou parâmetros ausentes",
                    "content": {"application/json": {"example": {"error": "Bad Request", "message": "Parâmetros inválidos"}}}
                },
                "401": {
                    "description": "Não autorizado ou token expirado",
                    "content": {"application/json": {"example": {"error": "Unauthorized", "message": "Autenticação requerida"}}}
                },
                "500": {
                    "description": "Erro interno no servidor",
                    "content": {"application/json": {"example": {"error": "Internal Server Error"}}}
                }
            }

        return {
            "200": {
                "description": "Operação realizada com sucesso",
                "content": {"application/json": {"example": {"status": "success", "data": []}}}
            },
            "400": {
                "description": "Requisição inválida ou parâmetros ausentes",
                "content": {"application/json": {"example": {"error": "Bad Request"}}}
            },
            "500": {
                "description": "Erro interno no servidor",
                "content": {"application/json": {"example": {"error": "Internal Server Error"}}}
            }
        }

    def _infer_body_schema(self, body_example):
        if not isinstance(body_example, dict):
            return []
        schema = []
        for k, v in body_example.items():
            t = "string"
            if isinstance(v, bool):
                t = "boolean"
            elif isinstance(v, int):
                t = "integer"
            elif isinstance(v, float):
                t = "number"
            elif isinstance(v, list):
                t = "array"
            elif isinstance(v, dict):
                t = "object"
            schema.append({"name": k, "type": t, "req": True, "desc": f"Campo {k}"})
        return schema

    def _add_endpoint(self, method: str, path: str, summary: str = "", tags: list = None, tag: str = None,
                      description: str = "", query_params: list = None, params: list = None,
                      body_schema: list = None, body_example: dict = None, body: dict = None,
                      responses: dict = None, sample_response=None, auth: str = None, **kwargs):
        method_upper = method.upper()
        tag_name = tag or (tags[0] if tags and len(tags) > 0 else "Geral")
        desc = description or summary or f"Endpoint {method_upper} {path}"
        auth_info = auth or ("Bearer Token / Sessão Ativa" if method_upper == "GET" else "Bearer Token / API Key")

        all_params = query_params or (params if method_upper in ["GET", "DELETE"] else []) or []
        b_example = body_example or body or (params if isinstance(params, dict) else None)
        b_schema = body_schema or (params if isinstance(params, list) and method_upper in ["POST", "PUT", "PATCH"] else None) or []

        if not b_schema and b_example and isinstance(b_example, dict):
            b_schema = self._infer_body_schema(b_example)

        norm_responses = self._normalize_responses(responses, sample_response)

        ep_id = f"{method_upper.lower()}_{path.replace('/', '_').strip('_')}"
        existing_ids = [e["id"] for e in self.endpoints]
        if ep_id in existing_ids:
            ep_id = f"{ep_id}_{len(existing_ids)}"

        endpoint_def = {
            "id": ep_id,
            "method": method_upper,
            "path": path,
            "summary": summary or path,
            "tag": tag_name,
            "description": desc,
            "auth": auth_info,
            "query_params": all_params,
            "body_schema": b_schema,
            "body_example": b_example,
            "responses": norm_responses
        }
        self.endpoints.append(endpoint_def)

    def route(self, method: str, path: str, **kwargs):
        def decorator(fn):
            m = method.upper()
            if m not in self.routes:
                self.routes[m] = {}
            self.routes[m][path] = fn
            self._add_endpoint(m, path, **kwargs)
            return fn
        return decorator

    def get(self, path: str, summary: str = "", tags: list = None, tag: str = None,
            description: str = "", query_params: list = None, params: list = None,
            responses: dict = None, sample_response=None, auth: str = None, **kwargs):
        def decorator(fn):
            self.routes["GET"][path] = fn
            self._add_endpoint("GET", path, summary=summary, tags=tags, tag=tag,
                               description=description, query_params=query_params, params=params,
                               responses=responses, sample_response=sample_response, auth=auth, **kwargs)
            return fn
        return decorator

    def post(self, path: str, summary: str = "", tags: list = None, tag: str = None,
             description: str = "", body_schema: list = None, params: list = None,
             body_example: dict = None, body: dict = None,
             responses: dict = None, sample_response=None, auth: str = None, **kwargs):
        def decorator(fn):
            self.routes["POST"][path] = fn
            self._add_endpoint("POST", path, summary=summary, tags=tags, tag=tag,
                               description=description, body_schema=body_schema, params=params,
                               body_example=body_example, body=body,
                               responses=responses, sample_response=sample_response, auth=auth, **kwargs)
            return fn
        return decorator

    def put(self, path: str, summary: str = "", tags: list = None, tag: str = None,
            description: str = "", body_schema: list = None, params: list = None,
            body_example: dict = None, body: dict = None,
            responses: dict = None, sample_response=None, auth: str = None, **kwargs):
        def decorator(fn):
            self.routes["PUT"][path] = fn
            self._add_endpoint("PUT", path, summary=summary, tags=tags, tag=tag,
                               description=description, body_schema=body_schema, params=params,
                               body_example=body_example, body=body,
                               responses=responses, sample_response=sample_response, auth=auth, **kwargs)
            return fn
        return decorator

    def delete(self, path: str, summary: str = "", tags: list = None, tag: str = None,
               description: str = "", query_params: list = None, params: list = None,
               responses: dict = None, sample_response=None, auth: str = None, **kwargs):
        def decorator(fn):
            self.routes["DELETE"][path] = fn
            self._add_endpoint("DELETE", path, summary=summary, tags=tags, tag=tag,
                               description=description, query_params=query_params, params=params,
                               responses=responses, sample_response=sample_response, auth=auth, **kwargs)
            return fn
        return decorator

    def patch(self, path: str, summary: str = "", tags: list = None, tag: str = None,
              description: str = "", body_schema: list = None, params: list = None,
              body_example: dict = None, body: dict = None,
              responses: dict = None, sample_response=None, auth: str = None, **kwargs):
        def decorator(fn):
            self.routes["PATCH"][path] = fn
            self._add_endpoint("PATCH", path, summary=summary, tags=tags, tag=tag,
                               description=description, body_schema=body_schema, params=params,
                               body_example=body_example, body=body,
                               responses=responses, sample_response=sample_response, auth=auth, **kwargs)
            return fn
        return decorator

    def mount(self, prefix: str, registry: 'RouteRegistry'):
        prefix = prefix.rstrip('/')
        for m, route_dict in registry.routes.items():
            if m not in self.routes:
                self.routes[m] = {}
            for path, handler in route_dict.items():
                full_path = f"{prefix}{path}"
                self.routes[m][full_path] = handler
        for ep in registry.endpoints:
            new_ep = dict(ep)
            new_ep["path"] = f"{prefix}{ep['path']}"
            new_ep["id"] = f"{new_ep['method'].lower()}_{new_ep['path'].replace('/', '_').strip('_')}"
            self.endpoints.append(new_ep)

    def include_registry(self, registry: 'RouteRegistry', prefix: str = ""):
        self.mount(prefix, registry)

    def generate_openapi_json(self, title: str, version: str):
        paths_obj = {}
        tags_set = set()

        for ep in self.endpoints:
            p = ep["path"]
            m = ep["method"].lower()
            tag = ep["tag"]
            tags_set.add(tag)

            if p not in paths_obj:
                paths_obj[p] = {}

            op = {
                "summary": ep["summary"],
                "description": ep["description"],
                "tags": [tag],
                "responses": {
                    code: {
                        "description": r.get("description", "Resposta"),
                        "content": r.get("content", {})
                    }
                    for code, r in ep["responses"].items()
                }
            }

            if ep.get("query_params"):
                op["parameters"] = [
                    {
                        "name": q.get("name", "param"),
                        "in": "query",
                        "required": q.get("req", False),
                        "description": q.get("desc", ""),
                        "schema": {"type": q.get("type", "string")}
                    }
                    for q in ep["query_params"]
                ]

            if ep.get("body_example") or ep.get("body_schema"):
                content_schema = {"type": "object"}
                if ep.get("body_example"):
                    content_schema["example"] = ep["body_example"]
                op["requestBody"] = {
                    "required": True,
                    "content": {"application/json": {"schema": content_schema}}
                }

            paths_obj[p][m] = op

        return {
            "openapi": "3.1.0",
            "info": {
                "title": title,
                "version": version,
                "description": "API Reference Dinâmica de Alta Fidelidade com Interactive Live Playground e Autenticação JWT"
            },
            "components": {
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT",
                        "description": "Insira o token JWT gerado em /api/auth/login"
                    }
                }
            },
            "security": [
                {"bearerAuth": []}
            ],
            "tags": [{"name": t} for t in sorted(tags_set)],
            "paths": paths_obj
        }

    def get_swagger_html(self, title: str):
        endpoints_json = json.dumps(self.endpoints, ensure_ascii=False)

        html_template = """<!DOCTYPE html>
<html lang="pt-BR" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>__TITLE__</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-body: #030712;
            --bg-sidebar: #050b18;
            --bg-middle: #040814;
            --bg-studio: #020617;
            --border: rgba(255, 255, 255, 0.08);
            --border-hover: rgba(255, 255, 255, 0.16);
            --primary: #3b82f6;
            --primary-light: #60a5fa;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --code-bg: #010409;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }

        /* =========================================================================
           DESIGN SYSTEM UNIVERSAL (SCROLLBAR 4PX & BUTTON WRAP PROTECTION)
           ========================================================================= */
        * {
            scrollbar-width: thin;
            scrollbar-color: rgba(59, 130, 246, 0.4) transparent;
        }
        ::-webkit-scrollbar {
            width: 4px !important;
            height: 4px !important;
        }
        ::-webkit-scrollbar-track {
            background: transparent !important;
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(59, 130, 246, 0.35) !important;
            border-radius: 9999px !important;
            transition: background 0.2s ease !important;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(59, 130, 246, 0.75) !important;
        }

        /* Proteção Universal: Botões em Linha Única */
        button, .btn, .btn-primary, .btn-secondary, .btn-run, .resp-status-btn, .lang-tab, .endpoint-link {
            white-space: nowrap !important;
            text-overflow: ellipsis;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            flex-shrink: 0 !important;
            line-height: 1.2 !important;
        }

        body { background: var(--bg-body); color: var(--text-main); height: 100vh; display: flex; flex-direction: column; overflow: hidden; }

        /* TOPBAR (IMPECCABLE SINGLE LINE NON-BREAKING) */
        header {
            min-height: 56px;
            height: 56px;
            background: rgba(3, 7, 18, 0.95);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 1.5rem;
            flex-shrink: 0;
            z-index: 50;
            gap: 1rem;
            white-space: nowrap;
            overflow-x: auto;
            overflow-y: hidden;
            scrollbar-width: none;
        }
        header::-webkit-scrollbar { display: none; }
        .brand-title { flex-shrink: 0; white-space: nowrap; }
        .brand-title { font-weight: 800; font-size: 0.95rem; color: #fff; display: flex; align-items: center; gap: 0.6rem; }
        .badge-ver { background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.3); color: var(--primary-light); font-size: 0.72rem; font-weight: 800; padding: 0.2rem 0.5rem; border-radius: 9999px; }

        .btn { padding: 0.45rem 0.85rem; border-radius: 8px; font-size: 0.82rem; font-weight: 600; border: 1px solid var(--border); background: rgba(255, 255, 255, 0.04); color: #fff; text-decoration: none; cursor: pointer; display: inline-flex; align-items: center; gap: 0.4rem; transition: all 0.15s; }
        .btn:hover { background: rgba(255, 255, 255, 0.08); border-color: var(--border-hover); }
        .btn-primary { background: var(--primary); border-color: var(--primary); }

        /* STUDIO 3-COLUMNS LAYOUT */
        .studio-layout {
            display: grid;
            grid-template-columns: 310px 1fr 500px;
            flex: 1;
            height: calc(100vh - 56px);
            overflow: hidden;
        }
        @media (max-width: 1300px) { .studio-layout { grid-template-columns: 280px 1fr 440px; } }

        /* 1. SIDEBAR */
        aside.sidebar {
            background: var(--bg-sidebar);
            border-right: 1px solid var(--border);
            overflow-y: auto;
            padding: 1.2rem 0.8rem;
            display: flex;
            flex-direction: column;
            gap: 1.2rem;
        }
        .search-box {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--border);
            padding: 0.55rem 0.8rem;
            border-radius: 8px;
            color: var(--text-muted);
            font-size: 0.82rem;
        }
        .search-box input { background: none; border: none; outline: none; color: #fff; font-size: 0.84rem; width: 100%; }
        .nav-cat-title { font-size: 0.72rem; font-weight: 800; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.06em; padding: 0.8rem 0.6rem 0.3rem 0.6rem; }
        .endpoint-link {
            display: flex;
            align-items: center;
            gap: 0.6rem;
            padding: 0.55rem 0.7rem;
            border-radius: 8px;
            color: #cbd5e1;
            font-size: 0.84rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.15s;
        }
        .endpoint-link:hover, .endpoint-link.active { background: rgba(59, 130, 246, 0.12); color: #fff; }
        
        .method-pill { font-size: 0.65rem; font-weight: 800; font-family: 'JetBrains Mono', monospace; padding: 0.15rem 0.4rem; border-radius: 4px; min-width: 52px; text-align: center; }
        .pill-get { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
        .pill-post { background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }
        .pill-put { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
        .pill-delete { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
        .pill-patch { background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); }

        /* 2. DOCUMENTAÇÃO TÉCNICA */
        main.doc-column {
            background: var(--bg-middle);
            overflow-y: auto;
            padding: 3rem 3.5rem;
            border-right: 1px solid var(--border);
        }
        .doc-tag-badge { font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: var(--primary-light); letter-spacing: 0.05em; margin-bottom: 0.6rem; }
        .doc-endpoint-title { font-size: 2.2rem; font-weight: 800; letter-spacing: -0.03em; margin-bottom: 1rem; color: #fff; }
        .path-badge-box {
            display: inline-flex;
            align-items: center;
            gap: 0.8rem;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--border);
            padding: 0.6rem 1rem;
            border-radius: 10px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.95rem;
            font-weight: 600;
            margin-bottom: 1.8rem;
        }
        .doc-desc { font-size: 0.98rem; line-height: 1.7; color: #cbd5e1; margin-bottom: 2rem; }

        h3.section-header { font-size: 1.1rem; font-weight: 800; color: #fff; margin: 2rem 0 1rem 0; padding-bottom: 0.5rem; border-bottom: 1px solid var(--border); }

        .params-table { width: 100%; border-collapse: collapse; margin-bottom: 2rem; }
        .params-table th, .params-table td { padding: 0.85rem 1rem; text-align: left; border-bottom: 1px solid var(--border); font-size: 0.86rem; }
        .params-table th { font-size: 0.72rem; font-weight: 800; color: var(--text-muted); text-transform: uppercase; }
        .param-name { font-family: 'JetBrains Mono', monospace; font-weight: 700; color: #fff; }
        .param-type { font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #94a3b8; }
        .badge-req { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); font-size: 0.68rem; font-weight: 800; padding: 0.1rem 0.35rem; border-radius: 4px; margin-left: 0.4rem; }

        .response-tabs { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1rem; }
        .resp-status-btn { padding: 0.3rem 0.7rem; border-radius: 6px; font-size: 0.75rem; font-weight: 800; font-family: 'JetBrains Mono', monospace; border: 1px solid var(--border); background: rgba(255,255,255,0.02); color: var(--text-muted); cursor: pointer; }
        .resp-status-btn.active-200 { background: rgba(16, 185, 129, 0.15); color: #34d399; border-color: rgba(16, 185, 129, 0.3); }
        .resp-status-btn.active-400 { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border-color: rgba(245, 158, 11, 0.3); }
        .resp-status-btn.active-500 { background: rgba(239, 68, 68, 0.15); color: #f87171; border-color: rgba(239, 68, 68, 0.3); }

        /* 3. PLAYGROUND STUDIO */
        aside.studio-column {
            background: var(--bg-studio);
            overflow-y: auto;
            padding: 2rem;
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }
        .studio-header { display: flex; justify-content: space-between; align-items: center; }
        .studio-title { font-size: 0.88rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); }

        .lang-tabs { display: flex; background: rgba(255, 255, 255, 0.03); border: 1px solid var(--border); border-radius: 8px; padding: 0.2rem; gap: 0.2rem; }
        .lang-tab { padding: 0.35rem 0.75rem; border-radius: 6px; font-size: 0.75rem; font-weight: 700; color: var(--text-muted); cursor: pointer; border: none; background: none; transition: all 0.15s; }
        .lang-tab.active { background: rgba(59, 130, 246, 0.2); color: var(--primary-light); }

        .code-box { background: var(--code-bg); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }
        .code-header { background: rgba(255, 255, 255, 0.02); border-bottom: 1px solid var(--border); padding: 0.6rem 1rem; display: flex; justify-content: space-between; align-items: center; font-size: 0.75rem; font-family: 'JetBrains Mono', monospace; color: var(--text-muted); }
        pre.code-content { padding: 1.2rem; font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; line-height: 1.6; color: #e2e8f0; overflow-x: auto; white-space: pre-wrap; word-break: break-all; }

        textarea.body-editor {
            width: 100%;
            height: 180px;
            background: var(--code-bg);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 1rem;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.82rem;
            color: #60a5fa;
            outline: none;
            resize: vertical;
            line-height: 1.5;
        }
        textarea.body-editor:focus { border-color: var(--primary); }

        .btn-run {
            background: var(--primary);
            border: 1px solid var(--primary);
            color: #fff;
            font-weight: 800;
            font-size: 0.9rem;
            padding: 0.8rem;
            border-radius: 10px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            transition: all 0.2s;
        }
        .btn-run:hover { background: #2563eb; transform: translateY(-1px); }

        .response-box {
            background: var(--code-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1rem;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            min-height: 140px;
            max-height: 240px;
            overflow-y: auto;
            color: #34d399;
            white-space: pre-wrap;
            word-break: break-all;
        }

        /* TOAST NOTIFICATION */
        #aidd-toast-container {
            position: fixed;
            bottom: 1.5rem;
            right: 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
            z-index: 99999;
            pointer-events: none;
        }
        .aidd-toast {
            pointer-events: auto;
            min-width: 280px;
            max-width: 420px;
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 12px;
            padding: 0.85rem 1.1rem;
            color: #f8fafc;
            font-size: 0.86rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.6);
            transform: translateY(20px) scale(0.95);
            opacity: 0;
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .aidd-toast.show { transform: translateY(0) scale(1); opacity: 1; }
        .aidd-toast.toast-success { border-color: rgba(16, 185, 129, 0.4); }
        .aidd-toast.toast-error { border-color: rgba(239, 68, 68, 0.4); }
    </style>
</head>
<body>
    <header>
        <div class="brand-title">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2.5"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
            <span>__TITLE__</span>
            <span class="badge-ver">OpenAPI 3.1.0</span>
        </div>
        <div style="display: flex; gap: 0.8rem;">
            <a href="/" class="btn">Aplicação Web</a>
            <a href="/mcp" class="btn" style="border-color: rgba(16,185,129,0.4); color: #34d399;">Portal MCP</a>
            <a href="/docs/guia" class="btn" style="border-color: rgba(59,130,246,0.5); color: #93c5fd;">Guia Oficial</a>
            <a href="/openapi.json" target="_blank" class="btn">Exportar JSON</a>
        </div>
    </header>

    <div class="studio-layout">
        <!-- 1. SIDEBAR -->
        <aside class="sidebar">
            <div class="search-box">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                <input type="text" id="filter-input" placeholder="Filtrar endpoints..." oninput="filtrarSidebar(this.value)">
            </div>
            <div id="sidebar-endpoints-tree"></div>
        </aside>

        <!-- 2. DOCUMENTAÇÃO DO ENDPOINT -->
        <main class="doc-column" id="doc-main-area">
            <div class="doc-tag-badge" id="doc-tag">Tag</div>
            <h1 class="doc-endpoint-title" id="doc-title">Carregando...</h1>
            
            <div class="path-badge-box">
                <span class="method-pill pill-get" id="doc-method-pill">GET</span>
                <span id="doc-path">/api/...</span>
            </div>

            <p class="doc-desc" id="doc-desc">Descrição do endpoint.</p>

            <h3 class="section-header">Autenticação</h3>
            <p style="font-size: 0.86rem; color: var(--text-muted);" id="doc-auth">Bearer token ou Sessão</p>

            <h3 class="section-header" id="params-header-title">Parâmetros de Requisição</h3>
            <table class="params-table">
                <thead>
                    <tr><th>CAMPO</th><th>TIPO</th><th>DESCRIÇÃO</th></tr>
                </thead>
                <tbody id="params-table-body"></tbody>
            </table>

            <h3 class="section-header">Respostas da API</h3>
            <div class="response-tabs" id="response-code-tabs"></div>
            <pre class="code-box" style="padding: 1rem; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: #34d399;" id="response-schema-viewer"></pre>
        </main>

        <!-- 3. PLAYGROUND STUDIO -->
        <aside class="studio-column">
            <div class="studio-header">
                <div class="studio-title">Interactive Playground</div>
                <div class="lang-tabs">
                    <button class="lang-tab active" id="tab-curl" onclick="trocarLinguagem('curl')">cURL</button>
                    <button class="lang-tab" id="tab-js" onclick="trocarLinguagem('js')">JavaScript</button>
                    <button class="lang-tab" id="tab-python" onclick="trocarLinguagem('python')">Python</button>
                </div>
            </div>

            <!-- CODE SNIPPET -->
            <div class="code-box">
                <div class="code-header">
                    <span id="snippet-lang-title">cURL Request</span>
                    <button class="btn" style="padding: 0.2rem 0.5rem; font-size: 0.7rem;" onclick="copiarSnippet()">Copiar</button>
                </div>
                <pre class="code-content" id="snippet-code-box">curl ...</pre>
            </div>

            <!-- REQUEST BODY EDITOR -->
            <div id="body-editor-container" style="display: none;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem;">
                    <span style="font-size: 0.78rem; font-weight: 800; color: var(--text-muted); text-transform: uppercase;">Body Payload (JSON)</span>
                    <button class="btn" style="padding: 0.15rem 0.4rem; font-size: 0.7rem;" onclick="resetBodyDefault()">Restaurar Padrão</button>
                </div>
                <textarea class="body-editor" id="live-body-editor"></textarea>
            </div>

            <button class="btn-run" onclick="executarChamadaAoVivo()">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                Executar Chamada (Send Request)
            </button>

            <!-- RESPOSTA EM TEMPO REAL -->
            <div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                    <div style="font-size: 0.78rem; font-weight: 800; color: var(--text-muted); text-transform: uppercase;">Resposta do Servidor</div>
                    <span id="response-status-badge" style="font-size: 0.72rem; font-weight: 800; font-family: 'JetBrains Mono', monospace;"></span>
                </div>
                <div class="response-box" id="live-response-box">// Clique em "Executar Chamada" para disparar a requisição</div>
            </div>
        </aside>
    </div>

    <!-- TOAST CONTAINER -->
    <div id="aidd-toast-container"></div>

    <script id="endpoints-data" type="application/json">
        __ENDPOINTS_JSON__
    </script>

    <script>
        let endpointsData = [];
        try {
            const dataElem = document.getElementById('endpoints-data');
            endpointsData = JSON.parse(dataElem.textContent);
        } catch (e) {
            console.error('Falha ao parsear endpoints JSON:', e);
        }

        let currentEndpoint = endpointsData.length > 0 ? endpointsData[0] : null;
        let currentLang = 'curl';
        let currentRespCode = '200';

        function showToast(message, type = 'info') {
            const container = document.getElementById('aidd-toast-container');
            const toast = document.createElement('div');
            toast.className = 'aidd-toast toast-' + type;
            toast.textContent = message;
            container.appendChild(toast);
            requestAnimationFrame(() => toast.classList.add('show'));
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => { if (toast.parentNode) toast.parentNode.removeChild(toast); }, 300);
            }, 3000);
        }

        function getMethodPillClass(method) {
            const m = (method || '').toUpperCase();
            if (m === 'GET') return 'pill-get';
            if (m === 'POST') return 'pill-post';
            if (m === 'PUT') return 'pill-put';
            if (m === 'DELETE') return 'pill-delete';
            if (m === 'PATCH') return 'pill-patch';
            return 'pill-post';
        }

        function montarSidebar(lista) {
            const tree = document.getElementById('sidebar-endpoints-tree');
            if (!tree) return;
            tree.innerHTML = '';
            let currentTag = '';

            lista.forEach((ep) => {
                if (ep.tag !== currentTag) {
                    currentTag = ep.tag || 'Geral';
                    const catHeader = document.createElement('div');
                    catHeader.className = 'nav-cat-title';
                    catHeader.textContent = currentTag;
                    tree.appendChild(catHeader);
                }

                const link = document.createElement('div');
                const isSelected = currentEndpoint && ep.id === currentEndpoint.id;
                link.className = 'endpoint-link' + (isSelected ? ' active' : '');
                link.dataset.endpointId = ep.id;
                link.onclick = function() { selecionarEndpoint(ep.id); };

                const pill = document.createElement('span');
                pill.className = 'method-pill ' + getMethodPillClass(ep.method);
                pill.textContent = ep.method;

                const label = document.createElement('span');
                label.style.overflow = 'hidden';
                label.style.textOverflow = 'ellipsis';
                label.style.whiteSpace = 'nowrap';
                label.textContent = ep.summary || ep.path;

                link.appendChild(pill);
                link.appendChild(label);
                tree.appendChild(link);
            });
        }

        function selecionarEndpoint(id) {
            currentEndpoint = endpointsData.find(e => e.id === id) || (endpointsData.length > 0 ? endpointsData[0] : null);
            if (!currentEndpoint) return;

            document.querySelectorAll('.endpoint-link').forEach(el => {
                el.classList.toggle('active', el.dataset.endpointId === currentEndpoint.id);
            });

            document.getElementById('doc-tag').textContent = currentEndpoint.tag || 'Geral';
            document.getElementById('doc-title').textContent = currentEndpoint.summary || currentEndpoint.path;
            document.getElementById('doc-path').textContent = currentEndpoint.path;
            document.getElementById('doc-desc').textContent = currentEndpoint.description || currentEndpoint.summary || '';
            document.getElementById('doc-auth').textContent = currentEndpoint.auth || 'Bearer Token ou Sessão';

            const pill = document.getElementById('doc-method-pill');
            pill.textContent = currentEndpoint.method;
            pill.className = 'method-pill ' + getMethodPillClass(currentEndpoint.method);

            // Tabela de Parâmetros
            const tbody = document.getElementById('params-table-body');
            tbody.innerHTML = '';
            const hasBody = ['POST', 'PUT', 'PATCH'].includes(currentEndpoint.method);
            const params = (hasBody ? currentEndpoint.body_schema : currentEndpoint.query_params) || [];

            if (params.length > 0) {
                params.forEach(p => {
                    const tr = document.createElement('tr');
                    
                    const tdName = document.createElement('td');
                    const nameSpan = document.createElement('span');
                    nameSpan.className = 'param-name';
                    nameSpan.textContent = p.name || '';
                    tdName.appendChild(nameSpan);
                    if (p.req) {
                        const reqBadge = document.createElement('span');
                        reqBadge.className = 'badge-req';
                        reqBadge.textContent = 'OBRIGATÓRIO';
                        tdName.appendChild(reqBadge);
                    }
                    
                    const tdType = document.createElement('td');
                    const typeSpan = document.createElement('span');
                    typeSpan.className = 'param-type';
                    typeSpan.textContent = p.type || 'string';
                    tdType.appendChild(typeSpan);
                    
                    const tdDesc = document.createElement('td');
                    tdDesc.textContent = p.desc || '-';
                    
                    tr.appendChild(tdName);
                    tr.appendChild(tdType);
                    tr.appendChild(tdDesc);
                    tbody.appendChild(tr);
                });
            } else {
                const tr = document.createElement('tr');
                const td = document.createElement('td');
                td.colSpan = 3;
                td.style.color = 'var(--text-muted)';
                td.textContent = 'Nenhum parâmetro obrigatório.';
                tr.appendChild(td);
                tbody.appendChild(tr);
            }

            // Tabs de Respostas
            const respTabs = document.getElementById('response-code-tabs');
            respTabs.innerHTML = '';
            const respCodes = Object.keys(currentEndpoint.responses || {});
            respCodes.forEach((code, idx) => {
                const activeCls = code === '200' ? 'active-200' : (code.startsWith('4') ? 'active-400' : 'active-500');
                const desc = (currentEndpoint.responses[code] && currentEndpoint.responses[code].description) ? currentEndpoint.responses[code].description : '';
                const btn = document.createElement('button');
                btn.className = 'resp-status-btn' + (idx === 0 ? ' ' + activeCls : '');
                btn.dataset.code = code;
                btn.textContent = code + ' ' + desc;
                btn.onclick = function() { selecionarResposta(code); };
                respTabs.appendChild(btn);
            });

            selecionarResposta(respCodes[0] || '200');

            // Body Editor
            const bodyEditorContainer = document.getElementById('body-editor-container');
            const bodyEditor = document.getElementById('live-body-editor');
            if (hasBody) {
                bodyEditorContainer.style.display = 'block';
                const ex = currentEndpoint.body_example || {};
                bodyEditor.value = JSON.stringify(ex, null, 2);
            } else {
                bodyEditorContainer.style.display = 'none';
            }

            atualizarSnippetCodigo();
            document.getElementById('live-response-box').textContent = '// Clique em "Executar Chamada" para disparar a requisição ao vivo';
            document.getElementById('response-status-badge').textContent = '';
        }

        function selecionarResposta(code) {
            currentRespCode = code;
            document.querySelectorAll('.resp-status-btn').forEach(btn => {
                const isThis = btn.dataset.code === code;
                const activeCls = code === '200' ? 'active-200' : (code.startsWith('4') ? 'active-400' : 'active-500');
                btn.className = 'resp-status-btn' + (isThis ? ' ' + activeCls : '');
            });

            const respObj = currentEndpoint && currentEndpoint.responses ? currentEndpoint.responses[code] : null;
            const viewer = document.getElementById('response-schema-viewer');
            if (respObj && respObj.content && respObj.content['application/json']) {
                viewer.textContent = JSON.stringify(respObj.content['application/json'].example || respObj, null, 2);
            } else {
                viewer.textContent = JSON.stringify(respObj || {"status": "ok"}, null, 2);
            }
        }

        function trocarLinguagem(lang) {
            currentLang = lang;
            document.querySelectorAll('.lang-tab').forEach(b => {
                b.classList.remove('active');
            });
            const activeTab = document.getElementById('tab-' + lang);
            if (activeTab) activeTab.classList.add('active');
            
            const titleSpan = document.getElementById('snippet-lang-title');
            if (titleSpan) {
                titleSpan.textContent = lang === 'curl' ? 'cURL Request' : (lang === 'js' ? 'JavaScript (Fetch)' : 'Python (Requests)');
            }
            atualizarSnippetCodigo();
        }

        function resetBodyDefault() {
            if (currentEndpoint) {
                document.getElementById('live-body-editor').value = JSON.stringify(currentEndpoint.body_example || {}, null, 2);
            }
        }

        function getSnippetCurl(ep, origin, hasBody, bodyStr) {
            if (!hasBody) {
                return 'curl -X ' + ep.method + ' "' + origin + ep.path + '" \\\\\\n  -H "Authorization: Bearer seu_token_aqui"';
            }
            return 'curl -X ' + ep.method + ' "' + origin + ep.path + '" \\\\\\n  -H "Content-Type: application/json" \\\\\\n  -H "Authorization: Bearer seu_token_aqui" \\\\\\n  -d ' + JSON.stringify(bodyStr);
        }

        function getSnippetJs(ep, origin, hasBody, bodyStr) {
            var lines = [];
            if (!hasBody) {
                lines.push('const response = await fetch("' + origin + ep.path + '", {');
                lines.push('  method: "' + ep.method + '",');
                lines.push('  headers: { "Authorization": "Bearer seu_token_aqui" }');
                lines.push('});');
            } else {
                lines.push('const response = await fetch("' + origin + ep.path + '", {');
                lines.push('  method: "' + ep.method + '",');
                lines.push('  headers: {');
                lines.push('    "Content-Type": "application/json",');
                lines.push('    "Authorization": "Bearer seu_token_aqui"');
                lines.push('  },');
                lines.push('  body: JSON.stringify(' + bodyStr + ')');
                lines.push('});');
            }
            lines.push('const data = await response.json();');
            lines.push('console.log(data);');
            return lines.join('\\n');
        }

        function getSnippetPython(ep, origin, hasBody, bodyStr) {
            var lines = [];
            lines.push('import requests');
            lines.push('');
            if (!hasBody) {
                lines.push('headers = {"Authorization": "Bearer seu_token_aqui"}');
                lines.push('response = requests.' + ep.method.toLowerCase() + '("' + origin + ep.path + '", headers=headers)');
            } else {
                lines.push('payload = ' + bodyStr);
                lines.push('headers = {"Authorization": "Bearer seu_token_aqui"}');
                lines.push('response = requests.' + ep.method.toLowerCase() + '("' + origin + ep.path + '", json=payload, headers=headers)');
            }
            lines.push('print(response.json())');
            return lines.join('\\n');
        }

        function atualizarSnippetCodigo() {
            if (!currentEndpoint) return;
            const box = document.getElementById('snippet-code-box');
            const ep = currentEndpoint;
            const origin = window.location.origin || 'http://localhost:3000';
            const hasBody = ['POST', 'PUT', 'PATCH'].includes(ep.method);
            const bodyStr = ep.body_example ? JSON.stringify(ep.body_example, null, 2) : '{}';

            if (currentLang === 'curl') {
                box.textContent = getSnippetCurl(ep, origin, hasBody, bodyStr);
            } else if (currentLang === 'js') {
                box.textContent = getSnippetJs(ep, origin, hasBody, bodyStr);
            } else if (currentLang === 'python') {
                box.textContent = getSnippetPython(ep, origin, hasBody, bodyStr);
            }
        }

        async function executarChamadaAoVivo() {
            if (!currentEndpoint) return;
            const box = document.getElementById('live-response-box');
            const badge = document.getElementById('response-status-badge');
            const origin = window.location.origin || 'http://localhost:3000';
            const ep = currentEndpoint;
            const hasBody = ['POST', 'PUT', 'PATCH'].includes(ep.method);

            box.textContent = 'Enviando requisição para ' + origin + ep.path + '...';

            try {
                const t0 = performance.now();
                let res;
                if (!hasBody) {
                    res = await fetch(ep.path, { method: ep.method });
                } else {
                    const bodyText = document.getElementById('live-body-editor').value;
                    res = await fetch(ep.path, {
                        method: ep.method,
                        headers: { 'Content-Type': 'application/json' },
                        body: bodyText || '{}'
                    });
                }
                const elapsed = Math.round(performance.now() - t0);
                badge.textContent = 'HTTP ' + res.status + ' (' + elapsed + 'ms)';
                badge.style.color = res.ok ? '#34d399' : '#f87171';

                const text = await res.text();
                try {
                    const data = JSON.parse(text);
                    box.textContent = JSON.stringify(data, null, 2);
                } catch (parseErr) {
                    box.textContent = text;
                }
            } catch (err) {
                badge.textContent = 'ERRO DE CONEXÃO';
                badge.style.color = '#f87171';
                box.textContent = err.message;
            }
        }

        function filtrarSidebar(query) {
            const q = (query || '').toLowerCase();
            const filtrados = endpointsData.filter(e => 
                (e.summary && e.summary.toLowerCase().includes(q)) || 
                (e.path && e.path.toLowerCase().includes(q)) || 
                (e.tag && e.tag.toLowerCase().includes(q)) ||
                (e.method && e.method.toLowerCase().includes(q))
            );
            montarSidebar(filtrados);
        }

        function copiarSnippet() {
            const code = document.getElementById('snippet-code-box').textContent;
            navigator.clipboard.writeText(code).then(() => {
                showToast('Snippet copiado com sucesso!', 'success');
            }).catch(() => {
                showToast('Falha ao copiar snippet.', 'error');
            });
        }

        window.onload = function() {
            montarSidebar(endpointsData);
            if (endpointsData.length > 0) {
                selecionarEndpoint(endpointsData[0].id);
            }
        };
    </script>
</body>
</html>"""
        return html_template.replace("__TITLE__", title).replace("__ENDPOINTS_JSON__", endpoints_json)
