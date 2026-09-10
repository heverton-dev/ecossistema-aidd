# -*- coding: utf-8 -*-
"""
JWTGenerator — Geração determinística de tokens JWT compatíveis com GoTrue/PostgREST.

Gera os dois tokens necessários para a stack auto-hospedada:
  - anon:         acesso anônimo (leitura pública — role 'anon' no PostgreSQL)
  - service_role: acesso administrativo total (role 'service_role' — sem RLS)

Uso:
    gen = JWTGenerator(jwt_secret="meu-segredo-com-32-chars-minimo")
    anon_key      = gen.anon_key()
    service_key   = gen.service_role_key()
    print(gen.env_block())  # bloco pronto para .env.production
"""

import time
import secrets
import string
from typing import Dict

try:
    import jwt as pyjwt
    HAS_JWT = True
except ImportError:
    HAS_JWT = False


def _gerar_secret(length: int = 40) -> str:
    """Gera um JWT secret aleatório seguro com comprimento mínimo de 32 chars."""
    alphabet = string.ascii_letters + string.digits + "-_"
    return "".join(secrets.choice(alphabet) for _ in range(length))


class JWTGenerator:
    """
    Gera e valida tokens JWT assinados com HS256 para uso com GoTrue e PostgREST.
    """

    def __init__(self, jwt_secret: str = ""):
        if not jwt_secret:
            jwt_secret = _gerar_secret()
        if len(jwt_secret) < 32:
            raise ValueError("JWT secret precisa ter pelo menos 32 caracteres.")
        self.jwt_secret = jwt_secret

    def _gerar_token(self, role: str, exp_years: int = 10) -> str:
        """Gera um token JWT assinado com HS256 para um role específico."""
        if not HAS_JWT:
            raise ImportError(
                "PyJWT não instalado. Execute: pip install PyJWT>=2.8.0"
            )
        iat = int(time.time())
        exp = iat + (exp_years * 365 * 24 * 3600)
        payload = {
            "role": role,
            "iss": "supabase",
            "iat": iat,
            "exp": exp,
        }
        return pyjwt.encode(payload, self.jwt_secret, algorithm="HS256")

    def anon_key(self) -> str:
        """Token JWT para acesso anônimo (role 'anon')."""
        return self._gerar_token("anon")

    def service_role_key(self) -> str:
        """Token JWT para acesso administrativo total (role 'service_role', bypass RLS)."""
        return self._gerar_token("service_role")

    def env_block(self, domain: str = "localhost") -> str:
        """
        Retorna bloco completo de variáveis de ambiente pronto para .env.production.
        Inclui JWT_SECRET, ANON_KEY e SERVICE_ROLE_KEY.
        """
        protocol = "http" if domain == "localhost" else "https"
        anon = self.anon_key()
        service = self.service_role_key()
        return (
            f"# Gerado por aidd-bridge — jwt_generator.py\n"
            f"# Tokens JWT assinados com HS256 e o mesmo secret do GoTrue/PostgREST\n"
            f"VITE_SUPABASE_URL={protocol}://{domain}\n"
            f"VITE_SUPABASE_PUBLISHABLE_KEY={anon}\n"
            f"SUPABASE_JWT_SECRET={self.jwt_secret}\n"
            f"SUPABASE_ANON_KEY={anon}\n"
            f"SUPABASE_SERVICE_ROLE_KEY={service}\n"
        )

    @classmethod
    def novo(cls) -> "JWTGenerator":
        """Cria uma instância com um JWT secret aleatório seguro gerado automaticamente."""
        return cls(jwt_secret=_gerar_secret(40))
