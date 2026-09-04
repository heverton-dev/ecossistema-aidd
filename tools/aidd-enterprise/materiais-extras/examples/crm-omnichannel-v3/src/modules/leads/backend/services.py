from shared.utils.formatters import sanitizar_whatsapp, formatar_moeda

class LeadsService:
    def __init__(self, db, events=None):
        self.db = db
        self.events = events

    def listar(self, status=None, busca=None):
        with self.db.get_connection() as conn:
            query = "SELECT * FROM leads WHERE 1=1"
            params = []
            if status and status != 'todos':
                query += " AND status = ?"
                params.append(status)
            if busca:
                query += " AND (LOWER(nome) LIKE LOWER(?) OR LOWER(empresa) LIKE LOWER(?) OR LOWER(email) LIKE LOWER(?))"
                params.extend([f"%{busca}%", f"%{busca}%", f"%{busca}%"])
            query += " ORDER BY score DESC, id DESC"
            return [dict(r) for r in conn.execute(query, params).fetchall()]

    def obter_por_id(self, lead_id: int):
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
            return dict(row) if row else None

    def salvar(self, dados: dict):
        lid = dados.get("id")
        nome = dados.get("nome", "").strip()
        email = dados.get("email", "").strip()
        telefone = sanitizar_whatsapp(dados.get("telefone", ""))
        empresa = dados.get("empresa", "").strip()
        score = int(dados.get("score", 50))
        status = dados.get("status", "novo")
        origem = dados.get("origem", "Website")
        valor = float(dados.get("valor_estimado", 0))

        with self.db.get_connection() as conn:
            if lid:
                conn.execute("""
                    UPDATE leads SET nome=?, email=?, telefone=?, empresa=?, score=?, status=?, origem=?, valor_estimado=?
                    WHERE id=?
                """, (nome, email, telefone, empresa, score, status, origem, valor, int(lid)))
                novo_id = int(lid)
                evento = "lead_atualizado"
            else:
                cur = conn.execute("""
                    INSERT INTO leads (nome, email, telefone, empresa, score, status, origem, valor_estimado)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (nome, email, telefone, empresa, score, status, origem, valor))
                novo_id = cur.lastrowid
                evento = "lead_criado"
            conn.commit()

            if self.events:
                self.events.emit(evento, {"id": novo_id, "nome": nome, "status": status, "valor": valor})
            return {"sucesso": True, "id": novo_id, "mensagem": "Lead salvo com sucesso!"}

    def deletar(self, lead_id: int):
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
            conn.commit()
            if self.events:
                self.events.emit("lead_excluido", {"id": lead_id})
            return {"sucesso": True, "mensagem": "Lead removido com sucesso!"}

    def seed_iniciais(self):
        with self.db.get_connection() as conn:
            if conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0] == 0:
                conn.executescript("""
                    INSERT INTO leads (nome, email, telefone, empresa, score, status, origem, valor_estimado) VALUES
                    ('Carlos Eduardo Mendes', 'carlos@techcorp.com.br', '5511988887777', 'TechCorp Brasil', 95, 'qualificado', 'WhatsApp', 18500.0),
                    ('Juliana Siqueira', 'juliana@inovare.com', '5521977776666', 'Inovare Soluções', 80, 'proposta', 'Google Ads', 32000.0),
                    ('Marcos Vinicius', 'marcos@vendaspro.com', '5531966665555', 'Vendas Pro', 65, 'novo', 'LinkedIn', 9500.0),
                    ('Dra. Helena Castro', 'helena@biomed.med.br', '5541999991111', 'BioMed Lab', 98, 'negociacao', 'Indicação VIP', 75000.0),
                    ('Fernando Guimarães', 'fernando@logistica.com', '5511955554444', 'Log Express', 88, 'ganho', 'Website', 42000.0);
                """)
                conn.commit()
