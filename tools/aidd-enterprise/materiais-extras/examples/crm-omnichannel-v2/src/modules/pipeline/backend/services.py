class PipelineService:
    def __init__(self, db, events=None):
        self.db = db
        self.events = events

    def obter_kanban(self):
        with self.db.get_connection() as conn:
            leads = [dict(r) for r in conn.execute("SELECT * FROM leads ORDER BY score DESC").fetchall()]
            estagios = {
                "novo": {"nome": "Novos Leads", "itens": [], "total_valor": 0},
                "qualificado": {"nome": "Qualificados", "itens": [], "total_valor": 0},
                "proposta": {"nome": "Proposta Enviada", "itens": [], "total_valor": 0},
                "negociacao": {"nome": "Em Negociação", "itens": [], "total_valor": 0},
                "ganho": {"nome": "Fechado / Ganho", "itens": [], "total_valor": 0}
            }
            for l in leads:
                st = l.get("status", "novo")
                if st in estagios:
                    estagios[st]["itens"].append(l)
                    estagios[st]["total_valor"] += l.get("valor_estimado", 0)
            return estagios

    def mover_lead(self, lead_id: int, novo_status: str):
        with self.db.get_connection() as conn:
            conn.execute("UPDATE leads SET status = ? WHERE id = ?", (novo_status, lead_id))
            conn.commit()
            if self.events:
                self.events.emit("lead_movido_pipeline", {"lead_id": lead_id, "novo_status": novo_status})
            return {"sucesso": True, "lead_id": lead_id, "status": novo_status}
