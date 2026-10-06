import time

from core.security import JWTService, SecurityService


def test_jwt_encode_decode_roundtrip():
    token = JWTService.encode({"sub": "admin@empresa.com", "role": "admin"})
    ok, payload, msg = JWTService.decode(token)
    assert ok is True
    assert msg == "OK"
    assert payload["sub"] == "admin@empresa.com"
    assert payload["role"] == "admin"
    assert "exp" in payload and "iat" in payload


def test_jwt_decode_accepts_bearer_prefix():
    token = JWTService.encode({"sub": "x@y.com"})
    ok, payload, _ = JWTService.decode(f"Bearer {token}")
    assert ok is True
    assert payload["sub"] == "x@y.com"


def test_jwt_decode_rejects_tampered_signature():
    token = JWTService.encode({"sub": "admin@empresa.com"})
    header_b64, payload_b64, sig_b64 = token.split(".")
    tampered = f"{header_b64}.{payload_b64}.{sig_b64[:-2]}xx"
    ok, payload, msg = JWTService.decode(tampered)
    assert ok is False
    assert payload is None
    assert "inválida" in msg or "invalid" in msg.lower()


def test_jwt_decode_rejects_wrong_secret():
    token = JWTService.encode({"sub": "admin@empresa.com"}, secret="segredo-correto")
    ok, payload, msg = JWTService.decode(token, secret="segredo-errado")
    assert ok is False
    assert payload is None


def test_jwt_decode_rejects_expired_token():
    token = JWTService.encode({"sub": "admin@empresa.com"}, exp_seconds=-10)
    ok, payload, msg = JWTService.decode(token)
    assert ok is False
    assert "expirado" in msg.lower()


def test_jwt_decode_rejects_malformed_token():
    ok, payload, msg = JWTService.decode("token-invalido-sem-pontos")
    assert ok is False
    assert payload is None

    ok2, _, _ = JWTService.decode("")
    assert ok2 is False


def test_security_headers_present():
    headers = SecurityService.get_security_headers()
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert "Strict-Transport-Security" in headers


def test_password_hash_and_verify_roundtrip():
    hashed = SecurityService.hash_password("minhaSenh@123")
    assert SecurityService.verify_password("minhaSenh@123", hashed) is True
    assert SecurityService.verify_password("senha-errada", hashed) is False


def test_validate_request_auth_with_valid_token():
    token = JWTService.encode({"sub": "admin@empresa.com", "role": "admin"})
    ok, payload = SecurityService.validate_request_auth(f"Bearer {token}")
    assert ok is True
    assert payload["role"] == "admin"


def test_validate_request_auth_rejects_role_below_required():
    token = JWTService.encode({"sub": "operador@empresa.com", "role": "operador"})
    ok, msg = SecurityService.validate_request_auth(f"Bearer {token}", required_role="admin")
    assert ok is False
    assert "Acesso negado" in msg
