import json

class RouteRegistry:
    def __init__(self):
        self.routes = {"GET": {}, "POST": {}}
        self.doc_specs = []

    def get(self, path: str, summary: str = "", tags: list = None):
        def decorator(func):
            self.routes["GET"][path] = func
            self.doc_specs.append({"method": "get", "path": path, "summary": summary, "tags": tags or ["Geral"]})
            return func
        return decorator

    def post(self, path: str, summary: str = "", tags: list = None):
        def decorator(func):
            self.routes["POST"][path] = func
            self.doc_specs.append({"method": "post", "path": path, "summary": summary, "tags": tags or ["Geral"]})
            return func
        return decorator

    def generate_openapi_json(self, title="AIDD Modular API", version="2.0.0"):
        paths = {}
        for spec in self.doc_specs:
            p = spec["path"]
            m = spec["method"]
            if p not in paths:
                paths[p] = {}
            paths[p][m] = {
                "summary": spec["summary"],
                "tags": spec["tags"],
                "responses": {"200": {"description": "Sucesso", "content": {"application/json": {}}}}
            }
        return {
            "openapi": "3.0.0",
            "info": {"title": title, "version": version, "description": "API REST Modular auto-gerada pelo AIDD Master Pack v2.0"},
            "paths": paths
        }

    def get_swagger_html(self, title="Documentação da API"):
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
    <style>body {{ margin: 0; background: #0b0f19; }} .swagger-ui {{ filter: invert(88%) hue-rotate(180deg); }}</style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
        SwaggerUIBundle({{
            url: '/openapi.json',
            dom_id: '#swagger-ui',
            deepLinking: true,
            presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset]
        }});
    </script>
</body>
</html>"""
