from shared.utils.crypto import hash_senha, verificar_senha
from shared.utils.validators import validar_email

class AuthService:
    def __init__(self, db, events=None):
        self.db = db
        self.events = events

    def cadastrar(self, nome: str, email: str, senha: str):
        email_limpo = email.strip().lower()
        if not validar_email(email_limpo):
            return {"sucesso": False, "erro": "Formato de email invalido."}
            
        with self.db.get_connection() as conn:
            try:
                cur = conn.execute(
                    "INSERT INTO usuarios (nome, email, senha_hash) VALUES (?, ?, ?)",
                    (nome.strip(), email_limpo, hash_senha(senha))
                )
                conn.commit()
                uid = cur.lastrowid
                if self.events:
                    self.events.emit("usuario_cadastrado", {"id": uid, "nome": nome, "email": email_limpo})
                return {"sucesso": True, "usuario_id": uid, "nome": nome, "email": email_limpo}
            except Exception as e:
                return {"sucesso": False, "erro": "Email ja cadastrado."}

    def autenticar(self, email: str, senha: str):
        email_limpo = email.strip().lower()
        with self.db.get_connection() as conn:
            user = conn.execute("SELECT * FROM usuarios WHERE email = ?", (email_limpo,)).fetchone()
            if user and verificar_senha(senha, user["senha_hash"]):
                return {
                    "sucesso": True,
                    "usuario": {
                        "id": user["id"],
                        "nome": user["nome"],
                        "email": user["email"],
                        "role": user["role"],
                        "plano_ativo": user["plano_ativo"]
                    }
                }
            return {"sucesso": False, "erro": "Credenciais invalidas."}
