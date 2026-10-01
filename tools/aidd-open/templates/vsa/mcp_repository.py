# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.1 Enterprise — Shared Kernel MCP Repository (mcp_repository.py)
=============================================================================
Camada de infraestrutura (persistencia) usada por MCPServer (core/mcp_server.py):
concentra os acessos sqlite3 brutos das ferramentas MCP genericas de
introspeccao de schema e CRUD por modulo, mantendo mcp_server.py livre de
SQL/import sqlite3 direto (Regra 1 do G_ARQUITETURA_DELIVERABLE).
"""

import sqlite3
from typing import Any, List, Optional


class MCPRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def listar_tabelas(self) -> List[str]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            return [r[0] for r in cur.fetchall()]

    def contar_registros(self, tabela_sanitizada: str) -> int:
        count_sql = "SELECT COUNT(*) FROM " + tabela_sanitizada
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(count_sql)
            res = cur.fetchone()
            return res[0] if res else 0

    def consultar(self, tabela_sanitizada: str, limite: int) -> List[sqlite3.Row]:
        query_sql = "SELECT * FROM " + tabela_sanitizada + " LIMIT ?"
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(query_sql, (limite,))
            return cur.fetchall()

    def listar_modulo(self, tabela: str, apenas_ativos: bool, status: Optional[str]) -> List[sqlite3.Row]:
        conditions = ["1=1"]
        params: List[Any] = []
        if apenas_ativos:
            conditions.append("ativo = 1")
        if status:
            conditions.append("status = ?")
            params.append(status)
        where_clause = " AND ".join(conditions)
        sql = "SELECT * FROM " + tabela + " WHERE " + where_clause + " ORDER BY id DESC"
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            return cur.fetchall()

    def obter_modulo(self, tabela: str, item_id: int) -> Optional[sqlite3.Row]:
        sql = "SELECT * FROM " + tabela + " WHERE id = ?"
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(sql, (item_id,))
            return cur.fetchone()

    def criar_modulo(self, tabela: str, titulo: str, descricao: str, dados_json: str, status: str) -> int:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO " + tabela + " (titulo, descricao, dados_json, status, ativo) VALUES (?, ?, ?, ?, 1)",
                (titulo, descricao, dados_json, status),
            )
            conn.commit()
            return cur.lastrowid

    def atualizar_modulo(self, tabela: str, item_id: int, titulo: str, descricao: str, status: str) -> None:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE " + tabela + " SET titulo = ?, descricao = ?, status = ?, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?",
                (titulo, descricao, status, item_id),
            )
            conn.commit()

    def deletar_modulo(self, tabela: str, item_id: int) -> None:
        sql = "DELETE FROM " + tabela + " WHERE id = ?"
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(sql, (item_id,))
            conn.commit()
