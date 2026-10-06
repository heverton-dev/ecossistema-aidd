import hashlib, hmac

SALT = b"aidd_catalogo_salt_2026"

class ConfigService:
    def __init__(self, db):
        self.db = db

    def _hash(self, s: str) -> str:
        return hashlib.pbkdf2_hmac("sha256", s.encode("utf-8"), SALT, 100000).hex()

    def obter(self):
        with self.db.get_connection() as conn:
            rows = conn.execute("SELECT chave, valor FROM configuracoes").fetchall()
            cfg = {r["chave"]: r["valor"] for r in rows}
            if not cfg:
                cfg = {
                    "nome_loja": "Tech & Lifestyle Store",
                    "whatsapp": "5511999999999",
                    "banner_texto": "Frete Grátis acima de R$ 150 | Atendimento Direto via WhatsApp",
                    "chave_pix": "pix@techlifestyle.com.br"
                }
                for k, v in cfg.items():
                    conn.execute("INSERT OR REPLACE INTO configuracoes (chave, valor) VALUES (?, ?)", (k, v))
                conn.commit()
            return cfg

    def autenticar_admin(self, email: str, senha: str):
        email_limpo = email.strip().lower()
        with self.db.get_connection() as conn:
            user = conn.execute("SELECT * FROM usuarios WHERE email = ?", (email_limpo,)).fetchone()
            if user and hmac.compare_digest(self._hash(senha), user["senha_hash"]):
                return {"sucesso": True, "usuario": {"id": user["id"], "nome": user["nome"], "email": user["email"]}}
            return {"sucesso": False, "erro": "Credenciais invalidas."}

    def seed_admin(self):
        with self.db.get_connection() as conn:
            u = conn.execute("SELECT 1 FROM usuarios WHERE email = 'admin@loja.com'").fetchone()
            if not u:
                conn.execute("INSERT INTO usuarios (nome, email, senha_hash) VALUES (?, ?, ?)",
                             ("Gerente da Loja", "admin@loja.com", self._hash("123456")))
                conn.commit()
