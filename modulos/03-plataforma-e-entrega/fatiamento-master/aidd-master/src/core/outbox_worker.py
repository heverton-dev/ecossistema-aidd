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

Exclusão mútua entre workers (claim atômico):
Cada evento é reivindicado (claimed_at/claimed_by) por um UPDATE atômico com a
guarda `status='pendente' AND claimed_at IS NULL` ANTES do emit. Dois workers
concorrentes disputam o mesmo UPDATE com rowcount==1 para exatamente um deles;
o perdedor vê rowcount==0 e pula o evento. Não há janela de dupla entrega.

Lease de claim (crash recovery):
Um worker que morre entre o claim e o emit deixa o evento 'pendente' com
claimed_at preenchido. Após `claim_lease_seconds`, qualquer worker reivindica o
evento novamente (condição `claimed_at < limiar`), garantindo at-least-once.

Semântica de entrega: at-least-once. Um crash entre emit() e a marcação de
'processado' causa o redespacho do mesmo evento no ciclo seguinte — listeners
devem usar idempotência (_eventos_processados, seq monotônico). Um evento que
falha sistematicamente é retentado até max_tentativas vezes (coluna 'tentativas')
e então movido para status 'dead_letter': sai da fila de processamento automático
sem bloquear os demais eventos; inspeção/reprocesso manual é decisão explícita
via SQL.
"""

import json
import time
import uuid
import threading
import datetime
from typing import List, Optional


class OutboxWorker:
    def __init__(
        self,
        db,
        event_bus,
        poll_interval: float = 2.0,
        batch_size: int = 50,
        max_tentativas: int = 5,
        claim_lease_seconds: float = 60.0,
        worker_id: Optional[str] = None,
    ):
        self.db = db
        self.event_bus = event_bus
        self.poll_interval = poll_interval
        self.batch_size = batch_size
        self.max_tentativas = max(1, int(max_tentativas))
        self.claim_lease_seconds = float(claim_lease_seconds)
        self.worker_id = worker_id or uuid.uuid4().hex[:8]
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
        """Claim atômico de até `limit` eventos pendentes e despacho síncrono.
        Retorna quantos eventos foram despachados com sucesso. Método público e
        testável isoladamente, sem depender da thread de polling. Falha de
        despacho libera o claim e incrementa 'tentativas'; ao esgotar
        max_tentativas o evento vai para 'dead_letter'."""
        despachados = 0
        for row in self._claim_pendentes(limit):
            try:
                payload = json.loads(row["payload"])
                payload.setdefault("outbox_event_id", row["id"])
                payload.setdefault("outbox_seq", row.get("seq") or 0)
                self.event_bus.emit(row["event_name"], payload, origin_module="outbox_worker")
                self._marcar_processado(row["id"])
                despachados += 1
            except Exception as e:
                self._registrar_falha(row["id"], row["event_name"], row.get("tentativas") or 0, e)

        return despachados

    def _claim_pendentes(self, limit: int) -> List[dict]:
        """Reivindica até `limit` eventos pendentes com exclusão mútua.

        A guarda `status='pendente' AND claimed_at IS NULL` faz de cada UPDATE um
        teste-e-defina atômico: entre N workers concorrentes, exatamente um obtém
        rowcount==1 para cada evento. O lease (`claimed_at < limiar`) recupera
        eventos órfãos de workers que morreram no meio do despacho.
        """
        agora = datetime.datetime.now(datetime.timezone.utc)
        limiar = (agora - datetime.timedelta(seconds=self.claim_lease_seconds)).isoformat()
        agora_str = agora.isoformat()

        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT id, event_name, payload, tentativas, seq FROM _outbox_events "
                "WHERE status = 'pendente' AND (claimed_at IS NULL OR claimed_at < ?) "
                "ORDER BY criado_em ASC, seq ASC LIMIT ?",
                (limiar, limit)
            ).fetchall()
            candidatos = [dict(r) for r in rows]

        claimados: List[dict] = []
        for cand in candidatos:
            with self.db.get_connection() as conn:
                cur = conn.execute(
                    "UPDATE _outbox_events SET claimed_at = ?, claimed_by = ? "
                    "WHERE id = ? AND status = 'pendente' AND (claimed_at IS NULL OR claimed_at < ?)",
                    (agora_str, self.worker_id, cand["id"], limiar)
                )
                conn.commit()
                if cur.rowcount == 1:
                    claimados.append(cand)

        return claimados

    def _registrar_falha(self, event_id: str, event_name: str, tentativas_atuais: int, erro: Exception):
        """Incrementa o contador de tentativas do evento; ao atingir max_tentativas
        move para status 'dead_letter' (sai da fila). Libera o claim em ambos os
        casos, permitindo que outro worker retente em vez de travar a fila."""
        novas = int(tentativas_atuais) + 1
        status = "dead_letter" if novas >= self.max_tentativas else "pendente"
        print(f"[OUTBOX_ERROR] Falha ao despachar evento {event_id} ({event_name}) "
              f"na tentativa {novas}/{self.max_tentativas}: {erro}")
        with self.db.get_connection() as conn:
            conn.execute(
                "UPDATE _outbox_events SET tentativas = ?, status = ?, "
                "claimed_at = NULL, claimed_by = NULL WHERE id = ?",
                (novas, status, event_id)
            )
            conn.commit()

    def _marcar_processado(self, event_id: str):
        with self.db.get_connection() as conn:
            conn.execute(
                "UPDATE _outbox_events SET status = 'processado', processado_em = ?, "
                "claimed_at = NULL, claimed_by = NULL WHERE id = ?",
                (datetime.datetime.now(datetime.timezone.utc).isoformat(), event_id)
            )
            conn.commit()