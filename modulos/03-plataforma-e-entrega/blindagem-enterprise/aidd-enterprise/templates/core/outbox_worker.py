# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.0-Alpha — TRANSACTIONAL OUTBOX WORKER (Entrega Garantida At-Least-Once)
=============================================================================
Consome a tabela _outbox_events (gravada atomicamente por Database.enqueue_outbox_event
na mesma transação da mutação de negócio) e despacha os eventos pendentes para o
EventBus. Sobrevive a quedas de processo: qualquer evento que não tenha sido
despachado antes da queda continua com status 'pendente' e é reprocessado no
próximo ciclo, garantindo entrega mesmo sem os listeners em memória originais.
"""

import json
import time
import threading
import datetime
from typing import Optional


class OutboxWorker:
    def __init__(self, db, event_bus, poll_interval: float = 2.0, batch_size: int = 50):
        self.db = db
        self.event_bus = event_bus
        self.poll_interval = poll_interval
        self.batch_size = batch_size
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """Inicia o polling em background (thread daemon, não bloqueia o servidor)."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, name="AIDD-OutboxWorker", daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            try:
                self.process_pending(self.batch_size)
            except Exception as e:
                print(f"[OUTBOX_ERROR] Falha no ciclo de polling: {e}")
            time.sleep(self.poll_interval)

    def process_pending(self, limit: int = 50) -> int:
        """Processa até `limit` eventos pendentes de forma síncrona. Retorna quantos
        eventos foram despachados com sucesso. Método público e testável isoladamente,
        sem depender da thread de polling."""
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT id, event_name, payload FROM _outbox_events "
                "WHERE status = 'pendente' ORDER BY criado_em ASC LIMIT ?",
                (limit,)
            ).fetchall()
            pendentes = [dict(r) for r in rows]

        despachados = 0
        for row in pendentes:
            try:
                payload = json.loads(row["payload"])
                self.event_bus.emit(row["event_name"], payload, origin_module="outbox_worker")
                self._marcar_processado(row["id"])
                despachados += 1
            except Exception as e:
                print(f"[OUTBOX_ERROR] Falha ao despachar evento {row['id']} ({row['event_name']}): {e}")

        return despachados

    def _marcar_processado(self, event_id: str):
        with self.db.get_connection() as conn:
            conn.execute(
                "UPDATE _outbox_events SET status = 'processado', processado_em = ? WHERE id = ?",
                (datetime.datetime.now(datetime.timezone.utc).isoformat(), event_id)
            )
            conn.commit()
