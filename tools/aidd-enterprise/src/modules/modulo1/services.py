# -*- coding: utf-8 -*-
"""
Serviço de regras de negócio Full CRUD, paginação, métricas e eventos para o módulo 'modulo1'.
"""

import json
from typing import Optional, List, Dict, Any
from core.database import append_audit_log


class Modulo1Service:
    def __init__(self, db, events=None):
        self.db = db
        self.events = events

    def listar(self, apenas_ativos: bool = True, status: Optional[str] = None, busca: Optional[str] = None, pagina: int = 1, limite: int = 50) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            query = "SELECT * FROM mod_modulo1 WHERE deletado_em IS NULL"
            params = []
            if apenas_ativos:
                query += " AND ativo = 1"
            if status:
                query += " AND status = ?"
                params.append(status)
            if busca:
                query += " AND (titulo LIKE ? OR descricao LIKE ?)"
                params.extend([f"%{busca}%", f"%{busca}%"])
            query += " ORDER BY id DESC"
            offset = max(0, (pagina - 1) * limite)
            query += " LIMIT ? OFFSET ?"
            params.extend([limite, offset])
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def obter_metricas(self) -> Dict[str, Any]:
        with self.db.get_connection() as conn:
            total = conn.execute("SELECT count(*) FROM mod_modulo1 WHERE deletado_em IS NULL").fetchone()[0]
            ativos = conn.execute("SELECT count(*) FROM mod_modulo1 WHERE deletado_em IS NULL AND ativo = 1").fetchone()[0]
            concluidos = conn.execute("SELECT count(*) FROM mod_modulo1 WHERE deletado_em IS NULL AND status = 'concluido'").fetchone()[0]
            return {
                "total": total,
                "ativos": ativos,
                "concluidos": concluidos,
                "taxa_conclusao": round((concluidos / total * 100) if total > 0 else 0.0, 1)
            }

    def obter_por_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM mod_modulo1 WHERE id = ? AND deletado_em IS NULL", (item_id,)).fetchone()
            return dict(row) if row else None

    def criar(self, titulo: str, dados: Optional[Dict[str, Any]] = None, descricao: str = "", status: str = "ativo") -> Dict[str, Any]:
        titulo_limpo = (titulo or "").strip()
        if not titulo_limpo:
            raise ValueError("O título do item é obrigatório")

        dados_dict = dados if dados is not None else {}
        with self.db.get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO mod_modulo1 (titulo, descricao, dados_json, status, ativo)
                VALUES (?, ?, ?, ?, 1)
                """,
                (titulo_limpo, descricao.strip(), json.dumps(dados_dict, ensure_ascii=False), status)
            )
            novo_id = cur.lastrowid

            payload = {
                "id": novo_id,
                "titulo": titulo_limpo,
                "descricao": descricao,
                "status": status,
                "dados": dados_dict
            }

            # WORM Audit Hash Chain: registro imutável encadeado com SHA-256
            append_audit_log(conn.cursor(), "modulo1_criado", payload)

            # Transactional Outbox Pattern: grava o evento na MESMA transação da
            # mutação, garantindo entrega at-least-once mesmo se o processo cair
            # antes do EventBus.emit() abaixo ser disparado.
            self.db.enqueue_outbox_event(conn, "modulo1_criado", payload)
            conn.commit()

        if self.events:
            self.events.emit("modulo1_criado", payload)

        return {"sucesso": True, "id": novo_id, "item": payload}

    def atualizar(self, item_id: int, titulo: Optional[str] = None, dados: Optional[Dict[str, Any]] = None, descricao: Optional[str] = None, status: Optional[str] = None) -> Dict[str, Any]:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM mod_modulo1 WHERE id = ? AND deletado_em IS NULL", (item_id,)).fetchone()
            if not row:
                return {"sucesso": False, "erro": "Item não encontrado"}

            novo_titulo = titulo.strip() if titulo is not None else row["titulo"]
            nova_desc = descricao.strip() if descricao is not None else row["descricao"]
            novo_status = status if status is not None else row["status"]
            novos_dados = json.dumps(dados, ensure_ascii=False) if dados is not None else row["dados_json"]

            conn.execute(
                """
                UPDATE mod_modulo1
                SET titulo = ?, descricao = ?, dados_json = ?, status = ?, atualizado_em = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (novo_titulo, nova_desc, novos_dados, novo_status, item_id)
            )

            payload = {
                "id": item_id,
                "titulo": novo_titulo,
                "descricao": nova_desc,
                "status": novo_status
            }

            append_audit_log(conn.cursor(), "modulo1_atualizado", payload)
            self.db.enqueue_outbox_event(conn, "modulo1_atualizado", payload)
            conn.commit()

        if self.events:
            self.events.emit("modulo1_atualizado", payload)

        return {"sucesso": True, "id": item_id, "item": payload}

    def deletar(self, item_id: int) -> Dict[str, Any]:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM mod_modulo1 WHERE id = ? AND deletado_em IS NULL", (item_id,)).fetchone()
            if not row:
                return {"sucesso": False, "erro": "Item não encontrado"}
            conn.execute("UPDATE mod_modulo1 SET deletado_em = CURRENT_TIMESTAMP, ativo = 0 WHERE id = ?", (item_id,))
            append_audit_log(conn.cursor(), "modulo1_deletado", {"id": item_id})
            self.db.enqueue_outbox_event(conn, "modulo1_deletado", {"id": item_id})
            conn.commit()

        if self.events:
            self.events.emit("modulo1_deletado", {"id": item_id})

        return {"sucesso": True, "id": item_id}
