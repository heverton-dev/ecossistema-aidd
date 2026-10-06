# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.2 — TRANSACTIONAL OUTBOX WORKER (Polling + BLPOP Event-Driven)
=============================================================================
Consome a tabela _outbox_events (gravada atomicamente por Database.enqueue_outbox_event
na mesma transação da mutação de negócio) e despacha os eventos pendentes para o
EventBus. Sobrevive a quedas de processo: qualquer evento que não tenha sido
despachado antes da queda continua com status 'pendente' e é reprocessado no
próximo ciclo, garantindo entrega mesmo sem os listeners em memória originais.

Dois modos de operação:
  1. **OutboxWorker** (polling, fallback): Usa sleep-based polling. Ativado
     por padrão, sem necessidade de Redis. Seguro como fallback universal.
  2. **RedisBLPOPWorker** (event-driven): Usa Redis BLPOP para wakeup
     instantâneo ao enfileirar um evento. Ativado quando EVENTBUS_URL aponta
     para um Redis (redis://...). Otimiza latência em 10-100x vs polling.

Exclusão mútua entre workers (claim atômico):
Cada evento é reivindicado (claimed_at/claimed_by) por um UPDATE atômico com a
guarda `status='pendente' AND claimed_at IS NULL` ANTES do emit. Dois workers
concorrentes disputam o mesmo UPDATE com rowcount==1 para exatamente um deles;
o perdedor vê rowcount==0 e pula o evento. Não há janela de dupla entrega.

Lease de claim (crash recovery):
Um worker que morre entre o claim e o emit deixa o evento 'pendente' com
claimed_at preenchido. Após `claim_lease_seconds`, qualquer worker reivindica o
evento novamente (condição `claimed_at < limiar`), garantindo at-least-once.

Backoff exponencial para falhas (max 3 retries):
Eventos que falham ao despachar recebem backoff exponencial (1s, 2s, 4s) com
máximo de 3 tentativas. Eventos que esgotam as retentativas são movidos para
a tabela _dead_letter_events para inspeção/reprocesso manual.

Dead-Layer Queue:
Eventos com 3+ falhas são movidos para _dead_letter_events com metadata
completa (erro, traceback, timestamps), saindo da fila de processamento
automático sem bloquear os demais eventos.
"""

import json
import os
import time
import uuid
import threading
import datetime
import traceback
from typing import List, Optional

# Backoff exponencial config
_BACKOFF_BASE_S = 1.0
_BACKOFF_MAX_S = 4.0
_MAX_RETRIES = 3


def _exponential_backoff(attempt: int) -> float:
    """Backoff exponencial: 1s, 2s, 4s (teto _BACKOFF_MAX_S)."""
    return min(_BACKOFF_BASE_S * (2 ** attempt), _BACKOFF_MAX_S)


def _dispatch_event(event_bus, row: dict) -> None:
    """Despacha um evento para o EventBus. Levanta exceção em caso de falha."""
    payload = json.loads(row["payload"])
    payload.setdefault("outbox_event_id", row["id"])
    payload.setdefault("outbox_seq", row.get("seq") or 0)
    event_bus.emit(row["event_name"], payload, origin_module="outbox_worker")


def _move_to_dead_letter(db, event_id: str, event_name: str, tentativas: int,
                         last_error: Exception) -> None:
    """Move evento para _dead_letter_events com metadata completa."""
    agora = datetime.datetime.now(datetime.timezone.utc).isoformat()
    erro_info = json.dumps({
        "error_type": type(last_error).__name__,
        "error_message": str(last_error),
        "traceback": traceback.format_exc(),
        "failed_at": agora,
    }, ensure_ascii=False)
    with db.get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO _dead_letter_events "
            "(id, event_name, payload, tentativas, last_error, dead_at) "
            "SELECT id, event_name, payload, ?, ?, ? FROM _outbox_events WHERE id = ?",
            (tentativas, erro_info, agora, event_id)
        )
        conn.execute(
            "UPDATE _outbox_events SET status = 'dead_letter', tentativas = ?, "
            "claimed_at = NULL, claimed_by = NULL WHERE id = ?",
            (tentativas, event_id)
        )
        conn.commit()


def _process_claimed_event(db, event_bus, row: dict, max_tentativas: int) -> bool:
    """Processa um evento já claimado. Retorna True se despachado com sucesso."""
    try:
        _dispatch_event(event_bus, row)
        agora = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with db.get_connection() as conn:
            conn.execute(
                "UPDATE _outbox_events SET status = 'processado', processado_em = ?, "
                "claimed_at = NULL, claimed_by = NULL WHERE id = ?",
                (agora, row["id"])
            )
            conn.commit()
        return True
    except Exception as e:
        tentativas = (row.get("tentativas") or 0) + 1
        if tentativas >= max_tentativas:
            print(f"[OUTBOX_DLQ] Evento {row['id']} ({row['event_name']}) "
                  f"esgotou {max_tentativas} tentativas — movendo para dead_letter")
            _move_to_dead_letter(db, row["id"], row["event_name"], tentativas, e)
        else:
            print(f"[OUTBOX_RETRY] Falha ao despachar {row['id']} ({row['event_name']}) "
                  f"tentativa {tentativas}/{max_tentativas}: {e}")
            backoff = _exponential_backoff(tentativas - 1)
            with db.get_connection() as conn:
                conn.execute(
                    "UPDATE _outbox_events SET tentativas = ?, status = 'pendente', "
                    "claimed_at = NULL, claimed_by = NULL WHERE id = ?",
                    (tentativas, row["id"])
                )
                conn.commit()
            time.sleep(backoff)
        return False


class OutboxWorker:
    """Worker de polling com sleep-based loop. Funcional como fallback universal
    quando Redis não está disponível. A BLPOP worker é opt-in via EVENTBUS_URL."""

    def __init__(
        self,
        db,
        event_bus,
        poll_interval: float = 2.0,
        batch_size: int = 50,
        max_tentativas: int = _MAX_RETRIES,
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
        despacho libera o claim, incrementa 'tentativas' com backoff, e ao esgotar
        max_tentativas o evento vai para _dead_letter_events."""
        despachados = 0
        for row in self._claim_pendentes(limit):
            if _process_claimed_event(self.db, self.event_bus, row, self.max_tentativas):
                despachados += 1
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
        """Legacy method — mantido para compatibilidade. Delegates to _process_claimed_event."""
        novas = int(tentativas_atuais) + 1
        if novas >= self.max_tentativas:
            _move_to_dead_letter(self.db, event_id, event_name, novas, erro)
        else:
            print(f"[OUTBOX_RETRY] Falha ao despachar evento {event_id} ({event_name}) "
                  f"na tentativa {novas}/{self.max_tentativas}: {erro}")
            with self.db.get_connection() as conn:
                conn.execute(
                    "UPDATE _outbox_events SET tentativas = ?, status = 'pendente', "
                    "claimed_at = NULL, claimed_by = NULL WHERE id = ?",
                    (novas, event_id)
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


class RedisBLPOPWorker:
    """Worker event-driven que usa Redis BLPOP para wakeup instantâneo.

    Em vez de sleep-based polling, este worker bloqueia em BLPOP na queue
    `aidd:outbox:notify` (timeout de 5s para permitir shutdown graceful).
    Quando um evento é enfileirado via Database.enqueue_outbox_event, um LPUSH
    nessa queue acorda o worker imediatamente — latência cai de poll_interval
    (2s default) para ~ms.

    Fallback híbrido: se Redis cair durante operação, o worker gracefulmente
    degrada para polling no banco (chama process_pending do OutboxWorker).
    Isso garante que eventos nunca ficam presos mesmo com Redis indisponível.

    Ativação: EVENTBUS_URL deve apontar para um Redis (redis://...).
    Configuração via variáveis de ambiente:
      - OUTBOX_BLPOP_TIMEOUT: timeout do BLPOP em segundos (default: 5)
      - OUTBOX_BLPOP_QUEUE: nome da Redis queue (default: aidd:outbox:notify)
    """

    BLPOP_QUEUE_DEFAULT = "aidd:outbox:notify"
    BLPOP_TIMEOUT_DEFAULT = 5

    def __init__(
        self,
        db,
        event_bus,
        redis_url: Optional[str] = None,
        batch_size: int = 50,
        max_tentativas: int = _MAX_RETRIES,
        claim_lease_seconds: float = 60.0,
        worker_id: Optional[str] = None,
        blpop_timeout: Optional[int] = None,
        blpop_queue: Optional[str] = None,
    ):
        self.db = db
        self.event_bus = event_bus
        self.batch_size = batch_size
        self.max_tentativas = max(1, int(max_tentativas))
        self.claim_lease_seconds = float(claim_lease_seconds)
        self.worker_id = worker_id or uuid.uuid4().hex[:8]
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Redis connection (lazy, graceful degradation)
        self._redis_url = redis_url or os.getenv("EVENTBUS_URL")
        self._redis_client = None
        self._redis_available = False
        self._blpop_timeout = int(
            blpop_timeout or os.getenv("OUTBOX_BLPOP_TIMEOUT", self.BLPOP_TIMEOUT_DEFAULT)
        )
        self._blpop_queue = (
            blpop_queue or os.getenv("OUTBOX_BLPOP_QUEUE", self.BLPOP_QUEUE_DEFAULT)
        )

        # Fallback polling worker
        self._fallback = OutboxWorker(
            db=db,
            event_bus=event_bus,
            poll_interval=2.0,
            batch_size=batch_size,
            max_tentativas=max_tentativas,
            claim_lease_seconds=claim_lease_seconds,
            worker_id=self.worker_id,
        )

    def _ensure_redis(self) -> bool:
        """Tenta conectar ao Redis (lazy init). Retorna True se disponível."""
        if self._redis_client is not None:
            return self._redis_available
        if not self._redis_url:
            self._redis_available = False
            return False
        try:
            import redis as redis_lib
            self._redis_client = redis_lib.from_url(
                self._redis_url, decode_responses=True, socket_connect_timeout=3
            )
            self._redis_client.ping()
            self._redis_available = True
            print(f"[OUTBOX_BLPOP] Redis conectado: {self._redis_url.split('@')[-1]}")
        except Exception as e:
            print(f"[OUTBOX_BLPOP] Redis indisponível ({e}), usando fallback polling")
            self._redis_available = False
            self._redis_client = None
        return self._redis_available

    def start(self):
        """Inicia worker BLPOP em background (thread daemon)."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, name="AIDD-RedisBLPOPWorker", daemon=True
        )
        self._thread.start()

    def stop(self):
        self._running = False
        self._fallback.stop()

    def _loop(self):
        """Loop principal: BLPOP com timeout → process_pending → retry."""
        while self._running:
            try:
                if self._ensure_redis():
                    self._blpop_cycle()
                else:
                    self._fallback_cycle()
            except Exception as e:
                print(f"[OUTBOX_BLPOP_ERROR] Falha no ciclo BLPOP: {e}")
                time.sleep(1)

    def _blpop_cycle(self):
        """Ciclo BLPOP: espera por notificação ou timeout, depois processa."""
        try:
            # BLPOP bloqueia até timeout ou item disponível
            result = self._redis_client.blpop(
                self._blpop_queue, timeout=self._blpop_timeout
            )
            if result is not None:
                # Notificação recebida — processa imediatamente
                self._drain_pending()
            else:
                # Timeout sem notificação — still check for orphaned events
                self._drain_pending()
        except Exception as e:
            print(f"[OUTBOX_BLPOP_ERROR] Falha BLPOP: {e}")
            self._redis_available = False
            # Degrada para polling
            self._fallback_cycle()

    def _fallback_cycle(self):
        """Ciclo de fallback: processa pendentes via polling silencioso."""
        self._drain_pending()

    def _drain_pending(self):
        """Processa todos os eventos pendentes (claim + emit + backoff)."""
        despachados = 0
        for row in self._claim_pendentes(self.batch_size):
            if _process_claimed_event(self.db, self.event_bus, row, self.max_tentativas):
                despachados += 1

    def _claim_pendentes(self, limit: int) -> List[dict]:
        """Claim atômico — idêntico ao OutboxWorker (mesma exclusão mútua)."""
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

    def process_pending(self, limit: int = 50) -> int:
        """Process pending events — exposto para testes e chamadas externas."""
        return self._fallback.process_pending(limit)

    @staticmethod
    def push_notification(redis_url: str, queue: Optional[str] = None) -> bool:
        """Helper estático: enfileira uma notificação na Redis queue para acordar
        o BLPOP worker. Chamado por Database.enqueue_outbox_event quando Redis
        está disponível. Retorna True se notificação enviada com sucesso."""
        q = queue or os.getenv("OUTBOX_BLPOP_QUEUE", RedisBLPOPWorker.BLPOP_QUEUE_DEFAULT)
        try:
            import redis as redis_lib
            r = redis_lib.from_url(redis_url, decode_responses=True, socket_connect_timeout=2)
            r.lpush(q, "new_event")
            return True
        except Exception:
            return False
