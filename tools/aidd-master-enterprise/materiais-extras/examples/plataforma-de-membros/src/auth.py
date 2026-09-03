import hashlib, hmac, secrets

SECRET_SALT = b"aidd_salt_super_seguro_2026"

def hash_senha(senha: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), SECRET_SALT, 100000).hex()

def verificar_senha(senha: str, hash_salvo: str) -> bool:
    return hmac.compare_digest(hash_senha(senha), hash_salvo)

def gerar_token_sessao() -> str:
    return secrets.token_hex(24)
