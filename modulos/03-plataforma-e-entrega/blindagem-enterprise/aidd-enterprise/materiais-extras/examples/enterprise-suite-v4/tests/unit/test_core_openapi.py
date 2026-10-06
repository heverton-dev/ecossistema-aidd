from core.openapi import RouteRegistry


def test_get_decorator_registra_rota_e_endpoint():
    registry = RouteRegistry()

    @registry.get("/api/teste", summary="Endpoint de teste", tags=["Teste"])
    def handler(params):
        return {"ok": True}

    assert registry.routes["GET"]["/api/teste"] is handler
    assert len(registry.endpoints) == 1
    assert registry.endpoints[0]["method"] == "GET"
    assert registry.endpoints[0]["tag"] == "Teste"


def test_post_decorator_infere_schema_do_body_example():
    registry = RouteRegistry()

    @registry.post("/api/itens", body_example={"nome": "x", "quantidade": 3, "ativo": True})
    def handler(data):
        return data

    schema = registry.endpoints[0]["body_schema"]
    tipos = {campo["name"]: campo["type"] for campo in schema}
    assert tipos == {"nome": "string", "quantidade": "integer", "ativo": "boolean"}


def test_generate_openapi_json_estrutura_basica():
    registry = RouteRegistry()

    @registry.get("/api/a", summary="A", tags=["Grupo A"])
    def handler_a(params):
        return []

    @registry.post("/api/b", summary="B", tags=["Grupo B"], body_example={"x": 1})
    def handler_b(data):
        return {}

    doc = registry.generate_openapi_json("Minha API", "1.0.0")

    assert doc["info"]["title"] == "Minha API"
    assert doc["info"]["version"] == "1.0.0"
    assert set(doc["paths"].keys()) == {"/api/a", "/api/b"}
    assert "get" in doc["paths"]["/api/a"]
    assert "post" in doc["paths"]["/api/b"]
    assert doc["paths"]["/api/b"]["post"]["requestBody"]["required"] is True
    assert {"Grupo A", "Grupo B"}.issubset({t["name"] for t in doc["tags"]})


def test_ids_de_endpoint_duplicados_recebem_sufixo():
    registry = RouteRegistry()

    @registry.get("/api/repetido", summary="1")
    def h1(params):
        return {}

    @registry.get("/api/repetido", summary="2")
    def h2(params):
        return {}

    ids = [e["id"] for e in registry.endpoints]
    assert len(ids) == len(set(ids))


def test_get_swagger_html_renderiza_titulo_e_endpoints(app):
    html = app.registry.get_swagger_html("Minha Documentação")
    assert "Minha Documentação" in html
    assert "/api/frotas/veiculos" in html
