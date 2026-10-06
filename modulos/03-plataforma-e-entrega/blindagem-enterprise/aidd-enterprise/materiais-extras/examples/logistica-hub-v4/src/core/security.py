import hmac, hashlib, base64, json, time, os

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "aidd_enterprise_master_jwt_secret_key_v4_scale_production_2026")

class JWTService:
    @staticmethod
    def _base64url_encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

    @staticmethod
    def _base64url_decode(s: str) -> bytes:
        rem = len(s) % 4
        if rem > 0:
            s += "=" * (4 - rem)
        return base64.urlsafe_b64decode(s.encode("utf-8"))

    @classmethod
    def encode(cls, payload: dict, secret: str = JWT_SECRET_KEY, exp_seconds: int = 86400) -> str:
        header = {"alg": "HS256", "typ": "JWT"}
        p = payload.copy()
        p["exp"] = int(time.time()) + exp_seconds
        p["iat"] = int(time.time())

        h_b64 = cls._base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
        p_b64 = cls._base64url_encode(json.dumps(p, separators=(",", ":")).encode("utf-8"))

        sig_input = f"{h_b64}.{p_b64}".encode("utf-8")
        sig = hmac.new(secret.encode("utf-8"), sig_input, hashlib.sha256).digest()
        sig_b64 = cls._base64url_encode(sig)

        return f"{h_b64}.{p_b64}.{sig_b64}"

    @classmethod
    def decode(cls, token: str, secret: str = JWT_SECRET_KEY) -> tuple:
        if not token:
            return False, None, "Token ausente"
        
        token = token.strip()
        if token.lower().startswith("bearer "):
            token = token[7:].strip()

        parts = token.split(".")
        if len(parts) != 3:
            return False, None, "Formato de token JWT inválido"

        h_b64, p_b64, sig_b64 = parts
        sig_input = f"{h_b64}.{p_b64}".encode("utf-8")
        expected_sig = hmac.new(secret.encode("utf-8"), sig_input, hashlib.sha256).digest()
        expected_sig_b64 = cls._base64url_encode(expected_sig)

        if not hmac.compare_digest(sig_b64, expected_sig_b64):
            return False, None, "Assinatura criptográfica inválida"

        try:
            payload = json.loads(cls._base64url_decode(p_b64).decode("utf-8"))
        except Exception as e:
            return False, None, f"Payload corrompido: {e}"

        if "exp" in payload and payload["exp"] < int(time.time()):
            return False, None, "Token expirado"

        return True, payload, "OK"


class SecurityService:
    # Placeholder injetado nos <script> inline dos HTML para receber um nonce
    # por requisição (ver new_nonce/inject_nonce). O servidor o substitui pelo
    # nonce real compartilhado com o header Content-Security-Policy.
    CSP_NONCE_PLACEHOLDER = "__CSP_NONCE__"

    _CSP_SCRIPT_SRC = ["'self'", "https://cdn.jsdelivr.net"]
    # Handlers inline (onclick/oninput/...) seguem via script-src-attr; o
    # elementos <script> ficam protegidos só por nonce por requisição.
    _CSP_SCRIPT_SRC_ATTR = ["'unsafe-inline'"]
    _CSP_STYLE_SRC = ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com", "https://cdn.jsdelivr.net"]
    _CSP_FONT_SRC = ["'self'", "https://fonts.gstatic.com"]
    _CSP_IMG_SRC = ["'self'", "data:"]
    _CSP_CONNECT_SRC = ["'self'", "https://cdn.jsdelivr.net"]

    @staticmethod
    def new_nonce() -> str:
        """Gera um nonce CSP por requisição (base64url, padding removido)."""
        return base64.urlsafe_b64encode(os.urandom(16)).decode("ascii").rstrip("=")

    @staticmethod
    def inject_nonce(content: str, nonce: str = None) -> str:
        """Substitui o placeholder de nonce nos scripts inline pelo nonce real."""
        if not nonce:
            return content
        return content.replace(SecurityService.CSP_NONCE_PLACEHOLDER, nonce)

    @classmethod
    def get_security_headers(cls, nonce: str = None) -> dict:
        script_src = list(cls._CSP_SCRIPT_SRC)
        if nonce:
            script_src.append(f"'nonce-{nonce}'")
        csp_value = (
            "default-src 'self'; "
            f"script-src {' '.join(script_src)}; "
            f"script-src-attr {' '.join(cls._CSP_SCRIPT_SRC_ATTR)}; "
            f"style-src {' '.join(cls._CSP_STYLE_SRC)}; "
            f"font-src {' '.join(cls._CSP_FONT_SRC)}; "
            f"img-src {' '.join(cls._CSP_IMG_SRC)}; "
            f"connect-src {' '.join(cls._CSP_CONNECT_SRC)}"
        )
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": csp_value,
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload"
        }

    @staticmethod
    def hash_password(password: str, salt: str = None) -> str:
        if not salt:
            salt = base64.b64encode(os.urandom(16)).decode("utf-8")
        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
        return f"{salt}:{base64.b64encode(key).decode('utf-8')}"

    @staticmethod
    def verify_password(password: str, hashed_str: str) -> bool:
        try:
            salt, key_b64 = hashed_str.split(":")
            new_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
            return hmac.compare_digest(key_b64, base64.b64encode(new_key).decode("utf-8"))
        except Exception:
            return False

    @staticmethod
    def validate_request_auth(auth_header: str, required_role: str = None) -> tuple:
        # Se nenhuma autenticação for configurada via env (ALLOW_ANONYMOUS=1), permite bypass para desenvolvimento
        if os.environ.get("ALLOW_ANONYMOUS", "0") == "1" and not auth_header:
            return True, {"sub": "dev_guest", "role": "admin"}
        
        ok, payload, msg = JWTService.decode(auth_header)
        if not ok:
            return False, msg
        
        if required_role and payload.get("role") != required_role and payload.get("role") != "admin":
            return False, f"Acesso negado. Requer nível '{required_role}'"
            
        return True, payload
