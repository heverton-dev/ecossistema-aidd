import hashlib, hmac

SALT = b"aidd_salt_super_seguro_2026"

class AuthService:
    def __init__(self, db):
        self.db = db

    def _hash(self, s: str) -> str:
        return hashlib.pbkdf2_hmac("sha256", s.encode("utf-8"), SALT, 100000).hex()

    def cadastrar(self, nome: str, email: str, senha: str):
        email_limpo = email.strip().lower()
        with self.db.get_connection() as conn:
            try:
                cur = conn.execute("INSERT INTO usuarios (nome, email, senha_hash) VALUES (?, ?, ?)",
                                   (nome.strip(), email_limpo, self._hash(senha)))
                conn.commit()
                return {"sucesso": True, "usuario_id": cur.lastrowid, "nome": nome, "email": email_limpo}
            except Exception as e:
                return {"sucesso": False, "erro": "Email ja cadastrado."}

    def autenticar(self, email: str, senha: str):
        email_limpo = email.strip().lower()
        with self.db.get_connection() as conn:
            user = conn.execute("SELECT * FROM usuarios WHERE email = ?", (email_limpo,)).fetchone()
            if user and hmac.compare_digest(self._hash(senha), user["senha_hash"]):
                return {"sucesso": True, "usuario": {"id": user["id"], "nome": user["nome"], "email": user["email"], "role": user["role"]}}
            return {"sucesso": False, "erro": "Credenciais invalidas."}
