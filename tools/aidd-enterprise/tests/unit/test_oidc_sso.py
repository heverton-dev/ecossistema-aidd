# -*- coding: utf-8 -*-
"""
Testes do OIDCService (Onda 3 / v5.0-Release): PKCE, montagem da URL de
autorização, mapeamento de papéis, e o fluxo completo de troca de código +
validação de id_token contra um MOCK OIDC PROVIDER LOCAL (http.server puro,
sem Docker e sem rede externa) — cobre o critério de aceite "login simulado
via mock OIDC gera token JWT assinado com claims de usuário corporativo".
"""

import os
import sys
import json
import time
import base64
import hashlib
import threading
import http.server
import urllib.parse

import pytest

TEMPLATES_V2 = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "templates", "v2"))
if TEMPLATES_V2 not in sys.path:
    sys.path.insert(0, TEMPLATES_V2)

from security import OIDCService, JWTService  # noqa: E402

jwt = pytest.importorskip("jwt", reason="PyJWT necessário para os testes de OIDC")
from cryptography.hazmat.primitives.asymmetric import rsa  # noqa: E402
from cryptography.hazmat.primitives import serialization  # noqa: E402


def test_generate_pkce_pair_challenge_matches_s256_of_verifier():
    verifier, challenge = OIDCService.generate_pkce_pair()
    expected = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("utf-8")).digest()).decode("utf-8").rstrip("=")
    assert challenge == expected
    assert len(verifier) >= 43  # RFC 7636: mínimo 43 caracteres


def test_build_authorization_url_includes_pkce_and_state():
    url = OIDCService.build_authorization_url(
        "https://idp.exemplo.com/authorize", "client-123", "http://localhost:3000/callback",
        "state-abc", "challenge-xyz"
    )
    parsed = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(parsed.query)
    assert parsed.scheme == "https"
    assert parsed.netloc == "idp.exemplo.com"
    assert qs["response_type"] == ["code"]
    assert qs["client_id"] == ["client-123"]
    assert qs["state"] == ["state-abc"]
    assert qs["code_challenge"] == ["challenge-xyz"]
    assert qs["code_challenge_method"] == ["S256"]


def test_map_claims_to_role_uses_group_mapping():
    claims = {"groups": ["eng-leads", "finance"]}
    role = OIDCService.map_claims_to_role(claims, {"eng-leads": "admin", "finance": "operador"})
    assert role == "admin"  # primeiro grupo do mapa que casar


def test_map_claims_to_role_defaults_to_leitor_without_match():
    assert OIDCService.map_claims_to_role({"groups": ["desconhecido"]}, {"eng-leads": "admin"}) == "leitor"
    assert OIDCService.map_claims_to_role({}, {}) == "leitor"


# ---------------------------------------------------------------------------
# Mock OIDC Provider local (sem Docker, sem rede externa) — RFC 7517 JWKS
# ---------------------------------------------------------------------------

class _MockOIDCHandler(http.server.BaseHTTPRequestHandler):
    private_key = None
    jwks = None
    issued_id_token = None

    def log_message(self, *args):
        pass  # silencia logs do http.server durante os testes

    def do_GET(self):
        if self.path == "/jwks":
            body = json.dumps(self.jwks).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/token":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            parsed = urllib.parse.parse_qs(body)
            assert parsed.get("grant_type") == ["authorization_code"]
            assert parsed.get("code") == ["auth-code-teste"]

            resp = {
                "access_token": "access-token-fake",
                "id_token": self.issued_id_token,
                "token_type": "Bearer",
                "expires_in": 3600,
            }
            body_bytes = json.dumps(resp).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body_bytes)
        else:
            self.send_response(404)
            self.end_headers()


def _int_to_base64url(n: int) -> str:
    byte_length = (n.bit_length() + 7) // 8
    return base64.urlsafe_b64encode(n.to_bytes(byte_length, "big")).decode("utf-8").rstrip("=")


@pytest.fixture
def mock_oidc_provider():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_numbers = private_key.public_key().public_numbers()

    jwks = {
        "keys": [{
            "kty": "RSA",
            "kid": "test-key-1",
            "use": "sig",
            "alg": "RS256",
            "n": _int_to_base64url(public_numbers.n),
            "e": _int_to_base64url(public_numbers.e),
        }]
    }

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    server = http.server.HTTPServer(("127.0.0.1", 0), _MockOIDCHandler)
    port = server.server_address[1]

    issuer = f"http://127.0.0.1:{port}/"
    audience = "client-teste-123"
    claims = {
        "iss": issuer,
        "aud": audience,
        "sub": "user-42",
        "email": "colaborador@empresa.com",
        "name": "Colaborador Teste",
        "groups": ["eng-leads"],
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    id_token = jwt.encode(claims, private_pem, algorithm="RS256", headers={"kid": "test-key-1"})

    _MockOIDCHandler.private_key = private_key
    _MockOIDCHandler.jwks = jwks
    _MockOIDCHandler.issued_id_token = id_token

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    yield {
        "base_url": f"http://127.0.0.1:{port}",
        "issuer": issuer,
        "audience": audience,
        "expected_claims": claims,
    }

    server.shutdown()
    server.server_close()


def test_fetch_jwks_from_mock_provider(mock_oidc_provider):
    jwks = OIDCService.fetch_jwks(f"{mock_oidc_provider['base_url']}/jwks")
    assert jwks["keys"][0]["kid"] == "test-key-1"


def test_exchange_code_and_validate_id_token_end_to_end(mock_oidc_provider):
    """Fluxo completo: troca do authorization code por tokens no mock provider,
    busca do JWKS, validação criptográfica RS256 do id_token e emissão de um
    JWT interno da aplicação com claims corporativos — sem nenhuma chamada de
    rede externa (tudo local, http.server + PyJWT + cryptography)."""
    tokens = OIDCService.exchange_code_for_tokens(
        token_endpoint=f"{mock_oidc_provider['base_url']}/token",
        client_id=mock_oidc_provider["audience"],
        client_secret="segredo-teste",
        code="auth-code-teste",
        code_verifier="verifier-fake",
        redirect_uri="http://localhost:3000/api/auth/oauth/callback",
    )
    assert "id_token" in tokens

    jwks = OIDCService.fetch_jwks(f"{mock_oidc_provider['base_url']}/jwks")
    claims = OIDCService.validate_id_token(
        tokens["id_token"], jwks,
        audience=mock_oidc_provider["audience"], issuer=mock_oidc_provider["issuer"]
    )

    assert claims["email"] == "colaborador@empresa.com"
    assert claims["groups"] == ["eng-leads"]

    role = OIDCService.map_claims_to_role(claims, {"eng-leads": "admin"})
    assert role == "admin"

    app_token = JWTService.encode({"sub": claims["email"], "role": role, "name": claims["name"]})
    ok, decoded, msg = JWTService.decode(app_token)
    assert ok is True
    assert decoded["sub"] == "colaborador@empresa.com"
    assert decoded["role"] == "admin"


def test_validate_id_token_rejects_wrong_audience(mock_oidc_provider):
    jwks = OIDCService.fetch_jwks(f"{mock_oidc_provider['base_url']}/jwks")
    with pytest.raises(Exception):
        OIDCService.validate_id_token(
            _MockOIDCHandler.issued_id_token, jwks,
            audience="audiencia-errada", issuer=mock_oidc_provider["issuer"]
        )


def test_validate_id_token_rejects_tampered_signature(mock_oidc_provider):
    jwks = OIDCService.fetch_jwks(f"{mock_oidc_provider['base_url']}/jwks")
    token = _MockOIDCHandler.issued_id_token
    header, payload, sig = token.split(".")
    tampered = f"{header}.{payload}.{sig[:-4]}AAAA"
    with pytest.raises(Exception):
        OIDCService.validate_id_token(
            tampered, jwks,
            audience=mock_oidc_provider["audience"], issuer=mock_oidc_provider["issuer"]
        )
