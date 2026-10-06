class CursosService:
    def __init__(self, db, events=None):
        self.db = db
        self.events = events

    def listar(self, usuario_id: int = None):
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
            if self.events:
                self.events.emit("curso_matriculado", {"usuario_id": usuario_id, "curso_id": curso_id})
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

    def seed_iniciais(self):
        with self.db.get_connection() as conn:
            count = conn.execute("SELECT COUNT(*) FROM cursos").fetchone()[0]
            if count == 0:
                conn.executescript("""
                    INSERT INTO cursos (titulo, descricao, preco, thumbnail, categoria) VALUES 
                    ('Engenharia Agentica AIDD', 'Domine o desenvolvimento com multiplos agentes.', 197.0, 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500', 'IA & Arquitetura'),
                    ('Mestre em ORCA e Worktrees', 'Como gerenciar times de IA sem contaminar contexto.', 147.0, 'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=500', 'DevOps & Git'),
                    ('Economia Extrema de Tokens', 'Caveman Ultra, Headroom e RTK para reduzir custos.', 97.0, 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=500', 'Otimizacao');

                    INSERT INTO aulas (curso_id, titulo, duracao, video_url, ordem) VALUES 
                    (1, 'Introducao ao Tratado das 4 Camadas', '14:20', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 1),
                    (1, 'Criando Circuit Breakers na Pratica', '18:45', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 2),
                    (2, 'O que sao Mesas de Trabalho (Worktrees)', '15:30', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 1);
                """)
                conn.commit()
