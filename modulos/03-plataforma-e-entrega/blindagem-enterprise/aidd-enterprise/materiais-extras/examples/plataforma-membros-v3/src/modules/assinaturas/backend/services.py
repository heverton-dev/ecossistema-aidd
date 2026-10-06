import json

class AssinaturasService:
    def __init__(self, db, events=None):
        self.db = db
        self.events = events

    def listar_planos(self):
        with self.db.get_connection() as conn:
            rows = conn.execute("SELECT * FROM planos ORDER BY preco_mensal ASC").fetchall()
            resultado = []
            for r in rows:
                p = dict(r)
                p["beneficios"] = json.loads(p["beneficios_json"])
                resultado.append(p)
            return resultado

    def assinar_plano(self, usuario_id: int, plano_slug: str):
        with self.db.get_connection() as conn:
            plano = conn.execute("SELECT * FROM planos WHERE slug = ?", (plano_slug,)).fetchone()
            if not plano:
                return {"sucesso": False, "erro": "Plano nao encontrado."}
            
            conn.execute("UPDATE usuarios SET plano_ativo = ? WHERE id = ?", (plano["nome"], usuario_id))
            conn.execute("INSERT INTO assinaturas_ativas (usuario_id, plano_id) VALUES (?, ?)", (usuario_id, plano["id"]))
            conn.commit()

            if self.events:
                self.events.emit("assinatura_ativada", {
                    "usuario_id": usuario_id,
                    "plano": plano["nome"],
                    "valor": plano["preco_mensal"]
                })
            return {"sucesso": True, "plano": plano["nome"], "mensagem": f"Plano {plano['nome']} ativado com sucesso!"}

    def seed_planos(self):
        with self.db.get_connection() as conn:
            count = conn.execute("SELECT COUNT(*) FROM planos").fetchone()[0]
            if count == 0:
                conn.executescript("""
                    INSERT INTO planos (slug, nome, preco_mensal, beneficios_json, destaque) VALUES
                    ('pro', 'Plano PRO', 49.90, '["Acesso a todos os cursos", "Certificados de conclusão", "Comunidade VIP", "Suporte prioritário"]', 1),
                    ('enterprise', 'Plano Enterprise', 149.90, '["Tudo do PRO", "Consultoria 1-on-1 quinzenal", "Código-fonte de todos os projetos", "Acesso antecipado a novas skills"]', 0);
                """)
                conn.commit()
