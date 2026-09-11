import json
import urllib.error
import urllib.request


def _get(url):
    with urllib.request.urlopen(url, timeout=5) as res:
        return res.status, dict(res.headers), res.read()


def _post(url, payload):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=5) as res:
        return res.status, json.loads(res.read().decode("utf-8"))


def test_api_frotas_veiculos_via_http_real(live_server):
    status, headers, body = _get(f"{live_server}/api/frotas/veiculos")
    assert status == 200
    veiculos = json.loads(body.decode("utf-8"))
    assert len(veiculos) == 3
    assert headers["X-Frame-Options"] == "DENY"


def test_post_auth_login_via_http_real(live_server):
    status, resposta = _post(f"{live_server}/api/auth/login", {"email": "teste@empresa.com", "password": "x"})
    assert status == 200
    assert resposta["sucesso"] is True
    assert resposta["token"].count(".") == 2


def test_openapi_json_lista_endpoints_reais(live_server):
    status, _, body = _get(f"{live_server}/openapi.json")
    assert status == 200
    doc = json.loads(body.decode("utf-8"))
    assert doc["openapi"] == "3.1.0"
    assert "/api/frotas/veiculos" in doc["paths"]
    assert "post" in doc["paths"]["/api/entregas/salvar"]


def test_docs_swagger_studio_renderiza(live_server):
    status, headers, body = _get(f"{live_server}/docs")
    assert status == 200
    assert headers["Content-Type"].startswith("text/html")
    assert b"Swagger" in body or b"Studio" in body


def test_webhooks_studio_page_renderiza_apos_correcao(live_server):
    status, headers, body = _get(f"{live_server}/webhooks")
    assert status == 200
    assert headers["Content-Type"].startswith("text/html")


def test_mcp_portal_renderiza(live_server):
    status, headers, body = _get(f"{live_server}/mcp")
    assert status == 200
    assert b"MCP" in body


def test_api_mcp_rpc_via_http_real(live_server):
    status, resposta = _post(f"{live_server}/api/mcp/rpc", {
        "jsonrpc": "2.0", "id": "e2e-1", "method": "tools/list"
    })
    assert status == 200
    assert any(t["name"] == "frotas_listar_veiculos" for t in resposta["result"]["tools"])


def test_rota_get_inexistente_cai_no_static_handler_404(live_server):
    try:
        _get(f"{live_server}/api/rota/que/nao/existe")
        assert False, "esperava HTTPError 404"
    except urllib.error.HTTPError as e:
        assert e.code == 404


def test_post_em_rota_inexistente_retorna_404(live_server):
    req = urllib.request.Request(
        f"{live_server}/api/rota/inexistente",
        data=b"{}",
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=5)
        assert False, "esperava HTTPError 404"
    except urllib.error.HTTPError as e:
        assert e.code == 404
