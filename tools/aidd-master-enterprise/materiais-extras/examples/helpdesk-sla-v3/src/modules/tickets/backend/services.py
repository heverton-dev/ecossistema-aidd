import uuid

class TicketsService:
    def __init__(self, db, events=None):
        self.db = db
        self.events = events

    def listar(self, status=None, prioridade=None, busca=None):
        with self.db.get_connection() as conn:
            q = "SELECT * FROM tickets WHERE 1=1"
            p = []
            if status and status != 'todos':
                q += " AND status = ?"
                p.append(status)
            if prioridade and prioridade != 'todos':
                q += " AND prioridade = ?"
                p.append(prioridade)
            if busca:
                q += " AND (LOWER(assunto) LIKE LOWER(?) OR LOWER(protocolo) LIKE LOWER(?) OR LOWER(cliente_nome) LIKE LOWER(?) OR LOWER(cliente_email) LIKE LOWER(?))"
                p.extend([f"%{busca}%", f"%{busca}%", f"%{busca}%", f"%{busca}%"])
            q += " ORDER BY CASE prioridade WHEN 'P1' THEN 1 WHEN 'P2' THEN 2 WHEN 'P3' THEN 3 ELSE 4 END, id DESC"
            return [dict(r) for r in conn.execute(q, p).fetchall()]

    def obter_por_id(self, tid: int):
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM tickets WHERE id = ?", (tid,)).fetchone()
            return dict(row) if row else None

    def salvar(self, dados: dict):
        tid = dados.get("id")
        assunto = dados.get("assunto", "").strip()
        descricao = dados.get("descricao", "").strip()
        nome = dados.get("cliente_nome", "").strip()
        email = dados.get("cliente_email", "").strip()
        prio = dados.get("prioridade", "P3")
        sla = int(dados.get("sla_limite_horas", 24))
        st = dados.get("status", "aberto")

        with self.db.get_connection() as conn:
            if tid:
                conn.execute("""
                    UPDATE tickets SET assunto=?, descricao=?, cliente_nome=?, cliente_email=?, prioridade=?, sla_limite_horas=?, status=?
                    WHERE id=?
                """, (assunto, descricao, nome, email, prio, sla, st, int(tid)))
                novo_id = int(tid)
                proto = conn.execute("SELECT protocolo FROM tickets WHERE id = ?", (novo_id,)).fetchone()[0]
                evt = "ticket_atualizado"
            else:
                proto = f"TICK-{uuid.uuid4().hex[:6].upper()}"
                cur = conn.execute("""
                    INSERT INTO tickets (protocolo, assunto, descricao, cliente_nome, cliente_email, prioridade, status, sla_limite_horas)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (proto, assunto, descricao, nome, email, prio, st, sla))
                novo_id = cur.lastrowid
                evt = "ticket_aberto"
            conn.commit()

            if self.events:
                self.events.emit(evt, {"id": novo_id, "protocolo": proto, "prioridade": prio, "status": st})
            return {"sucesso": True, "id": novo_id, "protocolo": proto, "mensagem": "Ticket salvo com sucesso!"}

    def avancar_status(self, tid: int):
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT status FROM tickets WHERE id = ?", (tid,)).fetchone()
            if not row: return {"sucesso": False}
            st_atual = row[0]
            novo_st = "em_andamento" if st_atual == "aberto" else ("resolvido" if st_atual == "em_andamento" else "aberto")
            conn.execute("UPDATE tickets SET status = ? WHERE id = ?", (novo_st, tid))
            conn.commit()
            if self.events:
                self.events.emit("ticket_status_alterado", {"id": tid, "novo_status": novo_st})
            return {"sucesso": True, "id": tid, "status": novo_st}

    def deletar(self, tid: int):
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM tickets WHERE id = ?", (tid,))
            conn.commit()
            if self.events:
                self.events.emit("ticket_excluido", {"id": tid})
            return {"sucesso": True, "mensagem": "Ticket excluído com sucesso!"}

    def seed_iniciais(self):
        with self.db.get_connection() as conn:
            if conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0] == 0:
                conn.executescript("""
                    INSERT INTO tickets (protocolo, assunto, descricao, cliente_nome, cliente_email, prioridade, status, sla_limite_horas) VALUES
                    ('TICK-A92B1C', 'Instabilidade no Webhook do n8n', 'Mensagens de checkout estão sofrendo timeout.', 'Rafael Souza', 'rafael@empresa.com', 'P1', 'aberto', 2),
                    ('TICK-D44F2E', 'Dúvida sobre integração de API Swagger', 'Como autenticar com chave Bearer no /docs?', 'Beatriz Lima', 'beatriz@dev.io', 'P3', 'em_andamento', 24),
                    ('TICK-E77A10', 'Falha na emissão do Pix Copia e Cola', 'QRCode não renderizou no modal de pagamento.', 'Guilherme Dias', 'guilherme@saas.com', 'P2', 'aberto', 4),
                    ('TICK-F99C33', 'Solicitação de Aumento de Cota API', 'Precisamos de 50.000 requisições/min.', 'Marina Vilela', 'marina@fintech.io', 'P4', 'resolvido', 48);
                """)
                conn.commit()
