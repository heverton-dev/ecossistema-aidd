class ContasService:
    def __init__(self, db, events=None):
        self.db = db
        self.events = events

    def listar(self, tipo=None, status=None, busca=None):
        with self.db.get_connection() as conn:
            q = "SELECT * FROM lancamentos WHERE 1=1"
            p = []
            if tipo and tipo != 'todos':
                q += " AND tipo = ?"
                p.append(tipo)
            if status and status != 'todos':
                q += " AND status = ?"
                p.append(status)
            if busca:
                q += " AND (LOWER(descricao) LIKE LOWER(?) OR LOWER(categoria) LIKE LOWER(?) OR LOWER(entidade_nome) LIKE LOWER(?))"
                p.extend([f"%{busca}%", f"%{busca}%", f"%{busca}%"])
            q += " ORDER BY data_vencimento ASC, id DESC"
            return [dict(r) for r in conn.execute(q, p).fetchall()]

    def obter_por_id(self, lanc_id: int):
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM lancamentos WHERE id = ?", (lanc_id,)).fetchone()
            return dict(row) if row else None

    def salvar(self, dados: dict):
        lid = dados.get("id")
        desc = dados.get("descricao", "").strip()
        tipo = dados.get("tipo", "receita").lower()
        cat = dados.get("categoria", "Geral").strip()
        valor = float(dados.get("valor", 0))
        venc = dados.get("data_vencimento", "2026-09-15")
        st = dados.get("status", "pendente")
        ent = dados.get("entidade_nome", "Cliente Direto").strip()

        with self.db.get_connection() as conn:
            if lid:
                conn.execute("""
                    UPDATE lancamentos SET descricao=?, tipo=?, categoria=?, valor=?, data_vencimento=?, status=?, entidade_nome=?
                    WHERE id=?
                """, (desc, tipo, cat, valor, venc, st, ent, int(lid)))
                novo_id = int(lid)
                evt = "conta_atualizada"
            else:
                cur = conn.execute("""
                    INSERT INTO lancamentos (descricao, tipo, categoria, valor, data_vencimento, status, entidade_nome)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (desc, tipo, cat, valor, venc, st, ent))
                novo_id = cur.lastrowid
                evt = "conta_criada"
            conn.commit()

            if self.events:
                self.events.emit(evt, {"id": novo_id, "descricao": desc, "tipo": tipo, "valor": valor, "status": st})
            return {"sucesso": True, "id": novo_id, "mensagem": "Lançamento financeiro salvo com sucesso!"}

    def alternar_status(self, lanc_id: int):
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT status FROM lancamentos WHERE id = ?", (lanc_id,)).fetchone()
            if not row:
                return {"sucesso": False, "mensagem": "Lançamento não encontrado"}
            novo_st = "pago" if row[0] == "pendente" else "pendente"
            conn.execute("UPDATE lancamentos SET status = ? WHERE id = ?", (novo_st, lanc_id))
            conn.commit()
            if self.events:
                self.events.emit("conta_status_alterado", {"id": lanc_id, "novo_status": novo_st})
            return {"sucesso": True, "id": lanc_id, "status": novo_st}

    def deletar(self, lanc_id: int):
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM lancamentos WHERE id = ?", (lanc_id,))
            conn.commit()
            if self.events:
                self.events.emit("conta_excluida", {"id": lanc_id})
            return {"sucesso": True, "mensagem": "Lançamento excluído com sucesso!"}

    def fluxo_caixa_resumo(self):
        with self.db.get_connection() as conn:
            rec_total = conn.execute("SELECT COALESCE(SUM(valor), 0) FROM lancamentos WHERE tipo = 'receita'").fetchone()[0]
            rec_paga = conn.execute("SELECT COALESCE(SUM(valor), 0) FROM lancamentos WHERE tipo = 'receita' AND status = 'pago'").fetchone()[0]
            desp_total = conn.execute("SELECT COALESCE(SUM(valor), 0) FROM lancamentos WHERE tipo = 'despesa'").fetchone()[0]
            desp_paga = conn.execute("SELECT COALESCE(SUM(valor), 0) FROM lancamentos WHERE tipo = 'despesa' AND status = 'pago'").fetchone()[0]
            return {
                "receitas_total": rec_total,
                "receitas_recebidas": rec_paga,
                "despesas_total": desp_total,
                "despesas_pagas": desp_paga,
                "saldo_realizado": rec_paga - desp_paga,
                "saldo_projetado": rec_total - desp_total
            }

    def seed_iniciais(self):
        with self.db.get_connection() as conn:
            if conn.execute("SELECT COUNT(*) FROM lancamentos").fetchone()[0] == 0:
                conn.executescript("""
                    INSERT INTO lancamentos (descricao, tipo, categoria, valor, data_vencimento, status, entidade_nome) VALUES
                    ('Licença Enterprise AIDD Anual', 'receita', 'Serviços de Software', 45000.0, '2026-09-10', 'pago', 'TechCorp'),
                    ('Servidor Cloud Hetzner Bare Metal', 'despesa', 'Infraestrutura', 1250.0, '2026-09-05', 'pago', 'Hetzner Online'),
                    ('Consultoria de Arquitetura de Software', 'receita', 'Consultoria', 18000.0, '2026-09-15', 'pendente', 'Inovare Soluções'),
                    ('Folha de Pagamento Especialistas IA', 'despesa', 'Pessoal', 22500.0, '2026-09-05', 'pago', 'Equipe Core'),
                    ('Gateway de Pagamento & Antifraude', 'despesa', 'Taxas Bancárias', 840.0, '2026-09-20', 'pendente', 'Asaas / Stripe');
                """)
                conn.commit()
