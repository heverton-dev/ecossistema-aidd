class ProgressoService:
    def __init__(self, db, events=None):
        self.db = db
        self.events = events

    def alternar_progresso(self, usuario_id: int, aula_id: int):
        with self.db.get_connection() as conn:
            p = conn.execute("SELECT 1 FROM progresso WHERE usuario_id = ? AND aula_id = ?", (usuario_id, aula_id)).fetchone()
            if p:
                conn.execute("DELETE FROM progresso WHERE usuario_id = ? AND aula_id = ?", (usuario_id, aula_id))
                status = False
            else:
                conn.execute("INSERT INTO progresso (usuario_id, aula_id) VALUES (?, ?)", (usuario_id, aula_id))
                status = True
            conn.commit()
            if self.events:
                self.events.emit("progresso_atualizado", {"usuario_id": usuario_id, "aula_id": aula_id, "concluida": status})
            return {"sucesso": True, "concluida": status}
