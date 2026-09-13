# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — COGNITIVE SESSION LEDGER (SQLite-WAL)
=============================================================================
Fornece persistencia estruturada imutavel para sessoes de agentes de IA,
registrando intencoes, decisoes arquiteturais, hashes de arquivos alterados
e vereditos de quality gates. Permite recuperacao instantanea em <5ms sem
depender de historico volatil de chat.
"""

import json
import os
import sqlite3
import time
from typing import Any, Dict, List, Optional


class CognitiveSessionLedger:
    """Gerenciador imutavel de estado cognitivo e telemetria de sessoes."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_dir = os.path.join(root_dir, ".aidd")
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, "cognitive_ledger.db")

        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cognitive_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_events 
                ON cognitive_events(session_id, timestamp);
            """)
            conn.commit()

    def record_event(self, session_id: str, event_type: str, payload: Dict[str, Any]) -> int:
        """Registra um evento atomico de sessao."""
        payload_str = json.dumps(payload, ensure_ascii=False)
        ts = time.time()
        with self._get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO cognitive_events (session_id, timestamp, event_type, payload_json) VALUES (?, ?, ?, ?)",
                (session_id, ts, event_type, payload_str),
            )
            conn.commit()
            return cur.lastrowid

    def get_latest_session_state(self, session_id: str) -> Dict[str, Any]:
        """Recupera o snapshot mais recente da sessao."""
        with self._get_connection() as conn:
            cur = conn.execute(
                "SELECT event_type, payload_json, timestamp FROM cognitive_events WHERE session_id = ? ORDER BY id DESC LIMIT 10",
                (session_id,),
            )
            rows = cur.fetchall()

        events = []
        for r in rows:
            events.append({
                "event_type": r[0],
                "payload": json.loads(r[1]),
                "timestamp": r[2]
            })
        return {"session_id": session_id, "recent_events": events}


_default_ledger: Optional[CognitiveSessionLedger] = None


def get_ledger() -> CognitiveSessionLedger:
    global _default_ledger
    if _default_ledger is None:
        _default_ledger = CognitiveSessionLedger()
    return _default_ledger
