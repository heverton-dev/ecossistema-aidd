# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.1 — TRANSACTIONAL OUTBOX WORKER (Entrega Garantida At-Least-Once)
=============================================================================
Consome a tabela _outbox_events (gravada atomicamente por Database.enqueue_outbox_event
na mesma transação da mutação de negócio) e despacha os eventos pendentes para o
EventBus. Sobrevive a quedas de processo: qualquer evento que não tenha sido
despachado antes da queda continua com status 'pendente' e é reprocessado no
próximo ciclo, garantindo entrega mesmo sem os listeners em memória originais.

Semântica de entrega: at-least-once. Um crash entre emit() e a marcação de
'processado' causa o redespacho do mesmo evento no ciclo seguinte — listeners
devem ser idempotentes. Um evento que falha sistematicamente é retentado até
max_tentativas vezes (coluna 'tentativas') e então movido para status
'dead_letter': sai da fila de processamento automático sem bloquear os demais
eventos; inspeção/reprocesso manual é decisão explícita via SQL.
"""

import json
import time
import threading
import datetime
from typing import Optional


class OutboxWorker:
    def __init__(self, db, event_bus, poll_interval: float = 2.0, batch_size: int = 50, max_tentativas: int = 5):
        self.db = db
        self.event_bus = event_bus
        self.poll_interval = poll_interval
        self.batch_size = batch_size
        self.max_tentativas = max(1, int(max_tentativas))
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
        sem depender da thread de polling. Falha de despacho incrementa 'tentativas';
        ao esgotar max_tentativas o evento vai para 'dead_letter'."""
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT id, event_name, payload, tentativas FROM _outbox_events "
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
                self._registrar_falha(row["id"], row["event_name"], row.get("tentativas") or 0, e)

        return despachados

    def _registrar_falha(self, event_id: str, event_name: str, tentativas_atuais: int, erro: Exception):
        """Incrementa o contador de tentativas do evento; ao atingir max_tentativas
        move para status 'dead_letter' (sai da fila de processamento automático)."""
        novas = int(tentativas_atuais) + 1
        status = "dead_letter" if novas >= self.max_tentativas else "pendente"
        print(f"[OUTBOX_ERROR] Falha ao despachar evento {event_id} ({event_name}) "
              f"na tentativa {novas}/{self.max_tentativas}: {erro}")
        with self.db.get_connection() as conn:
            conn.execute(
                "UPDATE _outbox_events SET tentativas = ?, status = ? WHERE id = ?",
                (novas, status, event_id)
            )
            conn.commit()

    def _marcar_processado(self, event_id: str):
        with self.db.get_connection() as conn:
            conn.execute(
                "UPDATE _outbox_events SET status = 'processado', processado_em = ? WHERE id = ?",
                (datetime.datetime.now(datetime.timezone.utc).isoformat(), event_id)
            )
            conn.commit()
