# -*- coding: utf-8 -*-
"""
Testes de hardening do JWTService (PLAN-0018 item 6 -
jwt-hardening-segredo-prod-exp-obrigatorio):

1) Segredo padrao/vazio em ambiente de producao deve abortar o boot (erro fatal).
2) Tokens sem claim `exp` explicito devem ser rejeitados no decode.
3) Revogacao de token (TRL) deve ser respeitada na verificacao padrao (decode).
"""

import os
import sys
import json
import hmac
import hashlib
import base64
import subprocess

from src.core.security import JWTService, JWT_SECRET_KEY

_RAIZ_PROJETO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SRC_DIR = os.path.join(_RAIZ_PROJETO, "src")


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _token_sem_exp(secret: str = JWT_SECRET_KEY) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": "usuario-teste"}
    h_b64 = _b64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    p_b64 = _b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    sig = hmac.new(secret.encode("utf-8"), f"{h_b64}.{p_b64}".encode("utf-8"), hashlib.sha256).digest()
    return f"{h_b64}.{p_b64}.{_b64url(sig)}"


def test_decode_rejeita_token_sem_claim_exp_obrigatoria():
    token = _token_sem_exp()
    ok, payload, msg = JWTService.decode(token)
    assert ok is False
    assert payload is None
    assert "exp" in msg.lower()


def test_encode_gera_jti_e_decode_aceita_token_valido():
    token = JWTService.encode({"sub": "usuario-teste"})
    ok, payload, msg = JWTService.decode(token)
    assert ok is True
    assert payload.get("jti")
    assert msg == "OK"


def test_revoke_invalida_token_na_verificacao_padrao():
    token = JWTService.encode({"sub": "usuario-revogado"})
    ok, _, _ = JWTService.decode(token)
    assert ok is True

    assert JWTService.revoke(token) is True

    ok2, payload2, msg2 = JWTService.decode(token)
    assert ok2 is False
    assert payload2 is None
    assert "revogado" in msg2.lower()


def test_revoke_de_token_invalido_retorna_false():
    assert JWTService.revoke("token-invalido") is False


def test_boot_falha_com_segredo_default_em_producao():
    """Reproducao real: processo Python novo, sem JWT_SECRET_KEY definido,
    com ENVIRONMENT=production, deve abortar a importacao do modulo (mesmo
    caminho de import usado pelo server.py real: cwd=src, 'core.security')."""
    env = os.environ.copy()
    env.pop("JWT_SECRET_KEY", None)
    env["ENVIRONMENT"] = "production"
    resultado = subprocess.run(
        [sys.executable, "-c", "import core.security"],
        cwd=_SRC_DIR, env=env, capture_output=True, text=True,
    )
    assert resultado.returncode != 0
    assert "producao" in resultado.stderr.lower()


def test_boot_falha_com_segredo_default_explicito_em_producao():
    env = os.environ.copy()
    env["ENVIRONMENT"] = "production"
    env["JWT_SECRET_KEY"] = "DEV_ONLY_INSECURE_SECRET_CHANGE_BEFORE_DEPLOY"
    resultado = subprocess.run(
        [sys.executable, "-c", "import core.security"],
        cwd=_SRC_DIR, env=env, capture_output=True, text=True,
    )
    assert resultado.returncode != 0
    assert "producao" in resultado.stderr.lower()


def test_boot_ok_com_segredo_forte_em_producao():
    env = os.environ.copy()
    env["ENVIRONMENT"] = "production"
    env["JWT_SECRET_KEY"] = "uma-chave-secreta-forte-e-unica-para-producao-2026"
    resultado = subprocess.run(
        [sys.executable, "-c", "import core.security; print('OK')"],
        cwd=_SRC_DIR, env=env, capture_output=True, text=True,
    )
    assert resultado.returncode == 0
    assert "OK" in resultado.stdout


def test_boot_ok_sem_segredo_fora_de_producao():
    """Fora de producao, ausencia de JWT_SECRET_KEY continua caindo no
    default de desenvolvimento (nao regride o fluxo local/testes)."""
    env = os.environ.copy()
    env.pop("JWT_SECRET_KEY", None)
    env.pop("ENVIRONMENT", None)
    env.pop("APP_ENV", None)
    env.pop("ENV", None)
    resultado = subprocess.run(
        [sys.executable, "-c", "import core.security; print('OK')"],
        cwd=_SRC_DIR, env=env, capture_output=True, text=True,
    )
    assert resultado.returncode == 0
    assert "OK" in resultado.stdout
