import json

class RouteRegistry:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(RouteRegistry, cls).__new__(cls)
            cls._instance.routes = {"GET": {}, "POST": {}, "PUT": {}, "DELETE": {}, "PATCH": {}}
            cls._instance.endpoints = []
        return cls._instance

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

        body { background: var(--bg-body); color: var(--text-main); height: 100vh; width: 100vw; display: flex; flex-direction: column; overflow: hidden; }

        /* TOPBAR (IMPECCABLE SINGLE LINE NON-BREAKING & TRUNCATING) */
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
            width: 100%;
        }
        .brand-title {
            display: flex;
            align-items: center;
            gap: 0.6rem;
            min-width: 0;
            flex: 1;
            overflow: hidden;
        }
        .brand-title svg { flex-shrink: 0; }
        .brand-title span.title-text {
            font-weight: 800;
            font-size: 0.92rem;
            color: #fff;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .badge-ver {
            background: rgba(59, 130, 246, 0.15);
            border: 1px solid rgba(59, 130, 246, 0.3);
            color: var(--primary-light);
            font-size: 0.7rem;
            font-weight: 800;
            padding: 0.15rem 0.5rem;
            border-radius: 9999px;
            flex-shrink: 0;
            white-space: nowrap;
        }
        .header-actions {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            flex-shrink: 0;
        }

        .btn { padding: 0.4rem 0.75rem; border-radius: 8px; font-size: 0.8rem; font-weight: 600; border: 1px solid var(--border); background: rgba(255, 255, 255, 0.04); color: #fff; text-decoration: none; cursor: pointer; display: inline-flex; align-items: center; gap: 0.35rem; transition: all 0.15s; flex-shrink: 0; }
        .btn:hover { background: rgba(255, 255, 255, 0.08); border-color: var(--border-hover); }
        .btn-primary { background: var(--primary); border-color: var(--primary); }

        /* STUDIO 3-COLUMNS LAYOUT (100% VIEWPORT PROTECTED WITH MINMAX) */
        .studio-layout {
            display: grid;
            grid-template-columns: 300px minmax(0, 1fr) 460px;
            flex: 1;
            height: calc(100vh - 56px);
            width: 100%;
            overflow: hidden;
        }
        @media (max-width: 1366px) { .studio-layout { grid-template-columns: 270px minmax(0, 1fr) 410px; } }
        @media (max-width: 1100px) { .studio-layout { grid-template-columns: 240px minmax(0, 1fr) 370px; } }

        /* 1. SIDEBAR */
        aside.sidebar {
            background: var(--bg-sidebar);
            border-right: 1px solid var(--border);
            overflow-y: auto;
            overflow-x: hidden;
            padding: 1rem 0.75rem;
            display: flex;
            flex-direction: column;
            gap: 1rem;
            height: 100%;
        }
        .search-box {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--border);
            padding: 0.5rem 0.75rem;
            border-radius: 8px;
            color: var(--text-muted);
            font-size: 0.8rem;
            flex-shrink: 0;
        }
        .search-box input { background: none; border: none; outline: none; color: #fff; font-size: 0.82rem; width: 100%; }
        .nav-cat-title { font-size: 0.7rem; font-weight: 800; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.06em; padding: 0.7rem 0.5rem 0.3rem 0.5rem; }
        .endpoint-link {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 0.65rem;
            border-radius: 8px;
            color: #cbd5e1;
            font-size: 0.82rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.15s;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .endpoint-link:hover, .endpoint-link.active { background: rgba(59, 130, 246, 0.12); color: #fff; }
        
        .method-pill { font-size: 0.65rem; font-weight: 800; font-family: 'JetBrains Mono', monospace; padding: 0.15rem 0.4rem; border-radius: 4px; min-width: 48px; text-align: center; flex-shrink: 0; }
        .pill-get { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
        .pill-post { background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }
        .pill-put { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
        .pill-delete { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
        .pill-patch { background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); }

        /* 2. DOCUMENTAÇÃO TÉCNICA */
        main.doc-column {
            background: var(--bg-middle);
            overflow-y: auto;
            overflow-x: hidden;
            padding: 2rem 2.5rem;
            border-right: 1px solid var(--border);
            height: 100%;
            display: flex;
            flex-direction: column;
        }
        .doc-tag-badge { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; color: var(--primary-light); letter-spacing: 0.05em; margin-bottom: 0.4rem; }
        .doc-endpoint-title { font-size: 1.65rem; font-weight: 800; letter-spacing: -0.02em; margin-bottom: 0.85rem; color: #fff; line-height: 1.25; word-break: break-word; }
        .path-badge-box {
            display: inline-flex;
            align-items: center;
            gap: 0.75rem;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--border);
            padding: 0.5rem 0.85rem;
            border-radius: 8px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.88rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
            max-width: 100%;
            overflow-x: auto;
            word-break: break-all;
        }
        .doc-desc { font-size: 0.92rem; line-height: 1.65; color: #cbd5e1; margin-bottom: 1.5rem; }

        h3.section-header { font-size: 0.98rem; font-weight: 800; color: #fff; margin: 1.5rem 0 0.85rem 0; padding-bottom: 0.4rem; border-bottom: 1px solid var(--border); text-transform: uppercase; letter-spacing: 0.04em; }

        .params-table { width: 100%; border-collapse: collapse; margin-bottom: 1.5rem; table-layout: fixed; }
        .params-table th, .params-table td { padding: 0.75rem 0.85rem; text-align: left; border-bottom: 1px solid var(--border); font-size: 0.82rem; word-break: break-word; }
        .params-table th:nth-child(1) { width: 30%; }
        .params-table th:nth-child(2) { width: 25%; }
        .params-table th:nth-child(3) { width: 45%; }
        .params-table th { font-size: 0.7rem; font-weight: 800; color: var(--text-muted); text-transform: uppercase; }
        .param-name { font-family: 'JetBrains Mono', monospace; font-weight: 700; color: #fff; }
        .param-type { font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #94a3b8; }
        .badge-req { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); font-size: 0.65rem; font-weight: 800; padding: 0.1rem 0.3rem; border-radius: 4px; margin-left: 0.3rem; }

        .response-tabs { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 0.85rem; }
        .resp-status-btn { padding: 0.3rem 0.65rem; border-radius: 6px; font-size: 0.72rem; font-weight: 800; font-family: 'JetBrains Mono', monospace; border: 1px solid var(--border); background: rgba(255,255,255,0.02); color: var(--text-muted); cursor: pointer; }
        .resp-status-btn.active-200 { background: rgba(16, 185, 129, 0.15); color: #34d399; border-color: rgba(16, 185, 129, 0.3); }
        .resp-status-btn.active-400 { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border-color: rgba(245, 158, 11, 0.3); }
        .resp-status-btn.active-500 { background: rgba(239, 68, 68, 0.15); color: #f87171; border-color: rgba(239, 68, 68, 0.3); }

        /* 3. PLAYGROUND STUDIO */
        aside.studio-column {
            background: var(--bg-studio);
            overflow-y: auto;
            overflow-x: hidden;
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 1.2rem;
            height: 100%;
        }
        .studio-header { display: flex; justify-content: space-between; align-items: center; }
        .studio-title { font-size: 0.82rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); }

        .lang-tabs { display: flex; background: rgba(255, 255, 255, 0.03); border: 1px solid var(--border); border-radius: 8px; padding: 0.2rem; gap: 0.2rem; }
        .lang-tab { padding: 0.3rem 0.65rem; border-radius: 6px; font-size: 0.72rem; font-weight: 700; color: var(--text-muted); cursor: pointer; border: none; background: none; transition: all 0.15s; }
        .lang-tab.active { background: rgba(59, 130, 246, 0.2); color: var(--primary-light); }

        .code-box { background: var(--code-bg); border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }
        .code-header { background: rgba(255, 255, 255, 0.02); border-bottom: 1px solid var(--border); padding: 0.5rem 0.85rem; display: flex; justify-content: space-between; align-items: center; font-size: 0.72rem; font-family: 'JetBrains Mono', monospace; color: var(--text-muted); }
        pre.code-content { padding: 1rem; font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; line-height: 1.55; color: #e2e8f0; overflow-x: auto; white-space: pre-wrap; word-break: break-all; }

        textarea.body-editor {
            width: 100%;
            height: 150px;
            background: var(--code-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 0.85rem;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.78rem;
            color: #60a5fa;
            outline: none;
            resize: vertical;
            line-height: 1.45;
        }
        textarea.body-editor:focus { border-color: var(--primary); }

        .btn-run {
            background: var(--primary);
            border: 1px solid var(--primary);
            color: #fff;
            font-weight: 800;
            font-size: 0.85rem;
            padding: 0.7rem;
            border-radius: 8px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            transition: all 0.2s;
            flex-shrink: 0;
        }
        .btn-run:hover { background: #2563eb; transform: translateY(-1px); }

        .response-box {
            background: var(--code-bg);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 0.85rem;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.76rem;
            min-height: 120px;
            max-height: 200px;
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
            min-width: 260px;
            max-width: 400px;
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 10px;
            padding: 0.75rem 1rem;
            color: #f8fafc;
            font-size: 0.82rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.65rem;
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
            <span class="title-text">__TITLE__</span>
            <span class="badge-ver">OpenAPI 3.1.0</span>
        </div>
        <div class="header-actions">
            <a href="/" class="btn">Aplicação Web</a>
            <a href="/webhooks" class="btn" style="border-color: rgba(139, 92, 246, 0.4); color: #c4b5fd;">Webhook Studio</a>
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
                <input type="text" id="filter-input" placeholder="Filtrar endpoints (Ctrl + K)..." oninput="filtrarSidebar(this.value)">
                <kbd style="font-size: 0.65rem; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15); border-radius: 4px; padding: 0.15rem 0.35rem; color: var(--text-muted); font-family: monospace; flex-shrink: 0;">Ctrl K</kbd>
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

        // SPOTLIGHT COMMAND PALETTE PARA SWAGGER STUDIO (ZERO EMOJIS)
        let spotlightSelectedIndex = 0;
        let spotlightFilteredCommands = [];

        function getOpenApiIconSvg(type, method) {
            if (method) {
                const color = method === 'GET' ? '#22c55e' : method === 'POST' ? '#38bdf8' : method === 'PUT' ? '#f59e0b' : '#ef4444';
                return `<span style="font-size:0.65rem;font-weight:800;color:${color};background:${color}15;border:1px solid ${color}40;padding:0.15rem 0.4rem;border-radius:4px;font-family:monospace;">${method}</span>`;
            }
            const icons = {
                app: '<svg width="16" height="16" fill="none" stroke="#38bdf8" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>',
                docs: '<svg width="16" height="16" fill="none" stroke="#38bdf8" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"/></svg>',
                webhooks: '<svg width="16" height="16" fill="none" stroke="#f59e0b" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>',
                mcp: '<svg width="16" height="16" fill="none" stroke="#a855f7" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"/></svg>',
                guia: '<svg width="16" height="16" fill="none" stroke="#10b981" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>',
                json: '<svg width="16" height="16" fill="none" stroke="#94a3b8" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>'
            };
            return icons[type] || '<svg width="16" height="16" fill="none" stroke="#94a3b8" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>';
        }

        function getSpotlightCommands() {
            const baseCommands = [
                { id: 'nav-app', cat: 'Navegação', title: 'Super-App Clínico (Home)', desc: 'Dashboard e painéis do Super-App', iconType: 'app', action: () => { window.location.href = '/'; } },
                { id: 'nav-docs', cat: 'Navegação', title: 'Swagger Studio (OpenAPI)', desc: 'Documentação interativa REST e live playground', iconType: 'docs', action: () => { window.location.href = '/docs'; } },
                { id: 'nav-wh', cat: 'Navegação', title: 'Webhook Studio', desc: 'Simulador de eventos e logs de webhook', iconType: 'webhooks', action: () => { window.location.href = '/webhooks'; } },
                { id: 'nav-mcp', cat: 'Navegação', title: 'MCP Native Server Portal', desc: '16 Ferramentas JSON-RPC para Claude Desktop e LLMs', iconType: 'mcp', action: () => { window.location.href = '/mcp'; } },
                { id: 'nav-guia', cat: 'Navegação', title: 'Manual Enciclopédico & Design System', desc: '11 Capítulos de arquitetura, segurança e UI', iconType: 'guia', action: () => { window.location.href = '/docs/guia'; } },
                { id: 'nav-json', cat: 'Navegação', title: 'Exportar OpenAPI JSON', desc: 'Download do manifesto bruto openapi.json', iconType: 'json', action: () => { window.open('/openapi.json', '_blank'); } }
            ];

            const endpointCommands = endpointsData.map(ep => ({
                id: 'ep-' + ep.id,
                cat: 'Endpoints REST',
                title: `${ep.method} ${ep.path}`,
                desc: ep.summary || ep.description || '',
                method: ep.method,
                action: () => { selecionarEndpoint(ep.id); }
            }));

            return [...baseCommands, ...endpointCommands];
        }

        function abrirSpotlight() {
            let modal = document.getElementById('spotlight-modal');
            if (!modal) {
                criarSpotlightDOM();
                modal = document.getElementById('spotlight-modal');
            }
            modal.style.display = 'flex';
            const inp = document.getElementById('spotlight-input');
            inp.value = '';
            filtrarSpotlight('');
            setTimeout(() => inp.focus(), 50);
        }

        function fecharSpotlight() {
            const modal = document.getElementById('spotlight-modal');
            if (modal) modal.style.display = 'none';
        }

        function criarSpotlightDOM() {
            const div = document.createElement('div');
            div.id = 'spotlight-modal';
            div.style.cssText = 'position:fixed;inset:0;background:rgba(2,6,23,0.85);backdrop-filter:blur(8px);z-index:9999;display:none;align-items:flex-start;justify-content:center;padding-top:5rem;';
            div.onclick = (e) => { if (e.target === div) fecharSpotlight(); };
            div.innerHTML = `
                <div style="background:#0f172a;border:1px solid rgba(255,255,255,0.15);border-radius:16px;width:100%;max-width:640px;box-shadow:0 25px 50px -12px rgba(0,0,0,0.7);overflow:hidden;display:flex;flex-direction:column;max-height:80vh;" onclick="event.stopPropagation()">
                    <div style="padding:1rem;border-bottom:1px solid rgba(255,255,255,0.1);display:flex;align-items:center;gap:0.75rem;background:rgba(255,255,255,0.02);">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                        <input type="text" id="spotlight-input" placeholder="Buscar endpoints REST, ações ou navegação (Ctrl + K)..." 
                               oninput="filtrarSpotlight(this.value)" onkeydown="navegarSpotlightTeclado(event)"
                               style="width:100%;background:transparent;border:none;color:#fff;font-size:0.9rem;font-weight:600;outline:none;">
                        <kbd style="font-size:0.7rem;background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.2);padding:0.2rem 0.5rem;border-radius:4px;color:#94a3b8;cursor:pointer;" onclick="fecharSpotlight()">ESC</kbd>
                    </div>
                    <div id="spotlight-results" style="overflow-y:auto;padding:0.5rem;max-height:55vh;display:flex;flex-direction:column;gap:0.25rem;"></div>
                    <div style="padding:0.6rem 1rem;background:#020617;border-top:1px solid rgba(255,255,255,0.1);display:flex;justify-content:space-between;align-items:center;font-size:0.72rem;color:#94a3b8;">
                        <div><kbd style="background:rgba(255,255,255,0.1);padding:0.1rem 0.3rem;border-radius:3px;">↑</kbd> <kbd style="background:rgba(255,255,255,0.1);padding:0.1rem 0.3rem;border-radius:3px;">↓</kbd> Navegar • <kbd style="background:rgba(255,255,255,0.1);padding:0.1rem 0.3rem;border-radius:3px;">↵</kbd> Executar • <kbd style="background:rgba(255,255,255,0.1);padding:0.1rem 0.3rem;border-radius:3px;">ESC</kbd> Fechar</div>
                        <span style="color:#38bdf8;font-weight:bold;font-family:monospace;">Spotlight Command Palette</span>
                    </div>
                </div>`;
            document.body.appendChild(div);
        }

        function filtrarSpotlight(q) {
            const query = (q || '').toLowerCase().trim();
            const allCommands = getSpotlightCommands();
            spotlightFilteredCommands = allCommands.filter(cmd => 
                !query || 
                cmd.title.toLowerCase().includes(query) || 
                cmd.desc.toLowerCase().includes(query) || 
                cmd.cat.toLowerCase().includes(query)
            );
            spotlightSelectedIndex = 0;
            renderizarSpotlightResultados();
        }

        function renderizarSpotlightResultados() {
            const container = document.getElementById('spotlight-results');
            if (!container) return;
            if (spotlightFilteredCommands.length === 0) {
                container.innerHTML = `<div style="padding:2rem;text-align:center;color:#64748b;font-size:0.85rem;">Nenhum comando ou endpoint encontrado</div>`;
                return;
            }
            let html = '';
            let currentCat = '';
            spotlightFilteredCommands.forEach((cmd, idx) => {
                if (cmd.cat !== currentCat) {
                    currentCat = cmd.cat;
                    html += `<div style="font-size:0.68rem;font-weight:800;text-transform:uppercase;color:#64748b;padding:0.5rem 0.75rem 0.2rem 0.75rem;letter-spacing:0.05em;">${currentCat}</div>`;
                }
                const isSelected = idx === spotlightSelectedIndex;
                const iconHtml = getOpenApiIconSvg(cmd.iconType, cmd.method);
                html += `
                <div onclick="executarSpotlightComando(${idx})" 
                     style="display:flex;align-items:center;justify-content:space-between;padding:0.6rem 0.8rem;border-radius:8px;cursor:pointer;background:${isSelected ? 'rgba(56,189,248,0.15)' : 'transparent'};border:1px solid ${isSelected ? 'rgba(56,189,248,0.3)' : 'transparent'};transition:all 0.15s;">
                    <div style="display:flex;align-items:center;gap:0.6rem;min-width:0;">
                        <div style="width:24px;display:flex;align-items:center;justify-content:center;flex-shrink:0;">${iconHtml}</div>
                        <div style="min-width:0;">
                            <div style="font-weight:700;font-size:0.82rem;color:#fff;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-family:${cmd.method ? 'monospace' : 'inherit'};">${cmd.title}</div>
                            <div style="font-size:0.72rem;color:#94a3b8;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${cmd.desc}</div>
                        </div>
                    </div>
                    <span style="font-size:0.68rem;color:#94a3b8;background:rgba(255,255,255,0.05);padding:0.15rem 0.4rem;border-radius:4px;flex-shrink:0;">${cmd.cat}</span>
                </div>`;
            });
            container.innerHTML = html;
        }

        function executarSpotlightComando(idx) {
            const cmd = spotlightFilteredCommands[idx];
            if (cmd && cmd.action) {
                fecharSpotlight();
                cmd.action();
            }
        }

        function navegarSpotlightTeclado(e) {
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                if (spotlightSelectedIndex < spotlightFilteredCommands.length - 1) {
                    spotlightSelectedIndex++;
                    renderizarSpotlightResultados();
                }
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                if (spotlightSelectedIndex > 0) {
                    spotlightSelectedIndex--;
                    renderizarSpotlightResultados();
                }
            } else if (e.key === 'Enter') {
                e.preventDefault();
                executarSpotlightComando(spotlightSelectedIndex);
            } else if (e.key === 'Escape') {
                e.preventDefault();
                fecharSpotlight();
            }
        }

        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
                e.preventDefault();
                abrirSpotlight();
            } else if (e.key === 'Escape') {
                fecharSpotlight();
            }
        });

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
