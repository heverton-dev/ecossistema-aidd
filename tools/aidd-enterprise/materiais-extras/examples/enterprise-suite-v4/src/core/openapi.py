import json, os

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

    def get_swagger_html(self, title: str) -> str:
        """Carrega e renderiza a interface do Swagger Studio."""
        endpoints_json = json.dumps(self.endpoints, ensure_ascii=False)
        tpl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "swagger_studio.html")
        if os.path.exists(tpl_path):
            with open(tpl_path, "r", encoding="utf-8") as f:
                template = f.read()
            return template.replace("__TITLE__", title).replace("__ENDPOINTS_JSON__", endpoints_json)
        return f"{title}"
