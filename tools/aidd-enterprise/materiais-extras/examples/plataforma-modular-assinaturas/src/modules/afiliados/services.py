import json
from core.database import Database
from core.events import EventBus

class AfiliadosService:
    def __init__(self, db: Database, events: EventBus = None):
        self.db = db
        self.events = events

    def listar(self, apenas_ativos: bool = True):
        with self.db.get_connection() as conn:
            query = "SELECT * FROM mod_afiliados"
            if apenas_ativos:
                query += " WHERE ativo = 1"
            query += " ORDER BY id DESC"
            rows = conn.execute(query).fetchall()
            return [dict(r) for r in rows]

    def criar(self, titulo: str, dados: dict = None):
        dados_dict = dados if dados is not None else {}
        with self.db.get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO mod_afiliados (titulo, dados_json) VALUES (?, ?)",
                (titulo.strip(), json.dumps(dados_dict))
            )
            conn.commit()
            novo_id = cur.lastrowid
            if self.events:
                self.events.emit("afiliados_criado", {"id": novo_id, "titulo": titulo})
            return {"sucesso": True, "id": novo_id, "titulo": titulo}

    def deletar(self, item_id: int):
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM mod_afiliados WHERE id = ?", (item_id,))
            conn.commit()
            if self.events:
                self.events.emit("afiliados_deletado", {"id": item_id})
            return {"sucesso": True}
