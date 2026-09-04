import hmac, hashlib, base64, json, time, os, urllib.parse, urllib.request

_JWT_SECRET_RAW = os.environ.get("JWT_SECRET_KEY")
if not _JWT_SECRET_RAW:
    _JWT_SECRET_RAW = "DEV_ONLY_INSECURE_SECRET_CHANGE_BEFORE_DEPLOY"
JWT_SECRET_KEY = _JWT_SECRET_RAW

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
    @staticmethod
    def get_security_headers() -> dict:
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self';",
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
        if not auth_header:
            return False, "Token de autenticação ausente"
        
        ok, payload, msg = JWTService.decode(auth_header)
        if not ok:
            return False, msg
        
        if required_role and payload.get("role") != required_role and payload.get("role") != "admin":
            return False, f"Acesso negado. Requer nível '{required_role}'"

        return True, payload


class OIDCService:
    """Fluxo OAuth2 Authorization Code + PKCE para SSO corporativo (Google
    Workspace, Microsoft Entra ID, GitHub, Okta). Ativado apenas quando as
    variáveis de ambiente OIDC_* estão configuradas — o modo padrão (JWT local
    via JWTService) continua funcionando sem nenhuma dependência extra."""

    @staticmethod
    def generate_pkce_pair() -> tuple:
        """Gera o par (code_verifier, code_challenge) do PKCE (RFC 7636, método S256)."""
        verifier = base64.urlsafe_b64encode(os.urandom(40)).decode("utf-8").rstrip("=")
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode("utf-8")).digest()
        ).decode("utf-8").rstrip("=")
        return verifier, challenge

    @staticmethod
    def build_authorization_url(authorization_endpoint: str, client_id: str, redirect_uri: str,
                                 state: str, code_challenge: str, scope: str = "openid email profile") -> str:
        params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        return f"{authorization_endpoint}?{urllib.parse.urlencode(params)}"

    @staticmethod
    def exchange_code_for_tokens(token_endpoint: str, client_id: str, client_secret: str,
                                  code: str, code_verifier: str, redirect_uri: str) -> dict:
        """Troca o authorization code por tokens (id_token, access_token) via
        Authorization Code + PKCE, sem depender de bibliotecas HTTP externas."""
        data = urllib.parse.urlencode({
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
            "code_verifier": code_verifier,
        }).encode("utf-8")
        req = urllib.request.Request(
            token_endpoint, data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))

    @staticmethod
    def fetch_jwks(jwks_uri: str) -> dict:
        with urllib.request.urlopen(jwks_uri, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))

    @staticmethod
    def validate_id_token(id_token: str, jwks: dict, audience: str, issuer: str) -> dict:
        """Valida a assinatura criptográfica RS256 do id_token contra a chave
        pública correspondente no JWKS, e as claims padrão (iss, aud, exp)."""
        try:
            import jwt
        except ImportError:
            raise RuntimeError("PyJWT não instalado. Para SSO OIDC, instale: pip install pyjwt cryptography")

        header = jwt.get_unverified_header(id_token)
        kid = header.get("kid")
        keys = jwks.get("keys", [])
        jwk = next((k for k in keys if k.get("kid") == kid), None)
        if jwk is None and keys:
            jwk = keys[0]
        if jwk is None:
            raise ValueError("JWKS não contém nenhuma chave pública utilizável")

        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
        return jwt.decode(id_token, key=public_key, algorithms=["RS256"], audience=audience, issuer=issuer)

    @staticmethod
    def map_claims_to_role(claims: dict, group_role_map: dict = None) -> str:
        """Mapeia grupos/claims corporativos para os papéis internos do sistema
        (admin/operador/leitor). Sem correspondência no mapa, o papel padrão
        de menor privilégio ('leitor') é atribuído."""
        group_role_map = group_role_map or {}
        groups = claims.get("groups") or claims.get("roles") or []
        if isinstance(groups, str):
            groups = [groups]
        for g in groups:
            if g in group_role_map:
                return group_role_map[g]
        return "leitor"
