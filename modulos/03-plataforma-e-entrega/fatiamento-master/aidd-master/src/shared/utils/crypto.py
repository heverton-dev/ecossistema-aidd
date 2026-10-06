import hashlib, hmac, secrets

DEFAULT_SALT = b"aidd_shared_master_salt_2026"

def hash_senha(senha: str, salt: bytes = DEFAULT_SALT, iteracoes: int = 100000) -> str:
    return hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt, iteracoes).hex()

def verificar_senha(senha: str, senha_hash: str, salt: bytes = DEFAULT_SALT) -> bool:
    return hmac.compare_digest(hash_senha(senha, salt), senha_hash)

def gerar_token_seguro(bytes_len: int = 32) -> str:
    return secrets.token_hex(bytes_len)
