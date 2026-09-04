from db import Database
from auth import hash_senha, verificar_senha

class PlataformaService:
    def __init__(self, db_path="banco_membros.db"):
        self.db = Database(db_path)

    def cadastrar_usuario(self, nome: str, email: str, senha: str):
        email_limpo = email.strip().lower()
        senha_h = hash_senha(senha)
        with self.db.get_connection() as conn:
            try:
                cur = conn.execute(
                    "INSERT INTO usuarios (nome, email, senha_hash) VALUES (?, ?, ?)",
                    (nome.strip(), email_limpo, senha_h)
                )
                conn.commit()
                return {"sucesso": True, "usuario_id": cur.lastrowid, "nome": nome, "email": email_limpo}
            except Exception as e:
                return {"sucesso": False, "erro": "Email ja cadastrado."}

    def autenticar(self, email: str, senha: str):
        email_limpo = email.strip().lower()
        with self.db.get_connection() as conn:
            user = conn.execute("SELECT * FROM usuarios WHERE email = ?", (email_limpo,)).fetchone()
            if user and verificar_senha(senha, user["senha_hash"]):
                return {"sucesso": True, "usuario": {"id": user["id"], "nome": user["nome"], "email": user["email"], "role": user["role"]}}
            return {"sucesso": False, "erro": "Credenciais invalidas."}

    def listar_cursos(self, usuario_id: int = None):
        with self.db.get_connection() as conn:
            cursos = conn.execute("SELECT * FROM cursos ORDER BY id ASC").fetchall()
            resultado = []
            for c in cursos:
                c_dict = dict(c)
                matriculado = False
                if usuario_id:
                    m = conn.execute("SELECT 1 FROM matriculas WHERE usuario_id = ? AND curso_id = ?", (usuario_id, c["id"])).fetchone()
                    matriculado = bool(m)
                c_dict["matriculado"] = matriculado
                resultado.append(c_dict)
            return resultado

    def matricular(self, usuario_id: int, curso_id: int):
        with self.db.get_connection() as conn:
            conn.execute("INSERT OR IGNORE INTO matriculas (usuario_id, curso_id) VALUES (?, ?)", (usuario_id, curso_id))
            conn.commit()
            return {"sucesso": True, "mensagem": "Matricula confirmada!"}

    def obter_aulas(self, curso_id: int, usuario_id: int = None):
        with self.db.get_connection() as conn:
            aulas = conn.execute("SELECT * FROM aulas WHERE curso_id = ? ORDER BY ordem ASC", (curso_id,)).fetchall()
            resultado = []
            for a in aulas:
                a_dict = dict(a)
                concluida = False
                if usuario_id:
                    p = conn.execute("SELECT 1 FROM progresso WHERE usuario_id = ? AND aula_id = ?", (usuario_id, a["id"])).fetchone()
                    concluida = bool(p)
                a_dict["concluida"] = concluida
                resultado.append(a_dict)
            return resultado

    def alternar_progresso_aula(self, usuario_id: int, aula_id: int):
        with self.db.get_connection() as conn:
            p = conn.execute("SELECT 1 FROM progresso WHERE usuario_id = ? AND aula_id = ?", (usuario_id, aula_id)).fetchone()
            if p:
                conn.execute("DELETE FROM progresso WHERE usuario_id = ? AND aula_id = ?", (usuario_id, aula_id))
                status = False
            else:
                conn.execute("INSERT INTO progresso (usuario_id, aula_id) VALUES (?, ?)", (usuario_id, aula_id))
                status = True
            conn.commit()
            return {"sucesso": True, "concluida": status}

    def seed_dados_iniciais(self):
        with self.db.get_connection() as conn:
            count = conn.execute("SELECT COUNT(*) FROM cursos").fetchone()[0]
            if count == 0:
                conn.execute("INSERT INTO cursos (titulo, descricao, preco, thumbnail, categoria) VALUES ('Engenharia Agentica AIDD', 'Domine o desenvolvimento com multiplos agentes.', 197.0, 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400', 'IA & Arquitetura')")
                conn.execute("INSERT INTO cursos (titulo, descricao, preco, thumbnail, categoria) VALUES ('Mestre em ORCA e Worktrees', 'Como gerenciar times de IA sem contaminar contexto.', 147.0, 'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=400', 'DevOps & Git')")
                conn.execute("INSERT INTO cursos (titulo, descricao, preco, thumbnail, categoria) VALUES ('Economia Extrema de Tokens', 'Caveman Ultra, Headroom e RTK para reduzir custos.', 97.0, 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400', 'Otimizacao')")
                conn.execute("INSERT INTO aulas (curso_id, titulo, duracao, video_url, ordem) VALUES (1, 'Introducao ao Tratado das 4 Camadas', '14:20', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 1)")
                conn.execute("INSERT INTO aulas (curso_id, titulo, duracao, video_url, ordem) VALUES (1, 'Criando Circuit Breakers na Pratica', '18:45', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 2)")
                conn.execute("INSERT INTO aulas (curso_id, titulo, duracao, video_url, ordem) VALUES (2, 'O que sao Mesas de Trabalho (Worktrees)', '15:30', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 1)")
                conn.commit()
