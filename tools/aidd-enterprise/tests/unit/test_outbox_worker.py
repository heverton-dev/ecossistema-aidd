# -*- coding: utf-8 -*-
"""
Testes do OutboxWorker (Onda 1 / v5.0-Alpha): valida o critério de aceite do
Transactional Outbox Pattern — "simulação de interrupção de processo com
recuperação e despacho 100% íntegro de eventos pendentes".
"""

import os
import sys
import time
import threading
from collections import Counter

TEMPLATES_V2 = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "templates", "v2"))
if TEMPLATES_V2 not in sys.path:
    sys.path.insert(0, TEMPLATES_V2)

from database import Database  # noqa: E402
from events import EventBus  # noqa: E402
from outbox_worker import OutboxWorker  # noqa: E402


def test_process_pending_dispatches_and_marks_processed(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'o1.db'}")
    events = EventBus()
    received = []
    events.on("pedido_criado", lambda p: received.append(p))

    with db.get_connection() as conn:
        event_id = db.enqueue_outbox_event(conn, "pedido_criado", {"id": 1, "titulo": "Pedido X"})
        conn.commit()

    worker = OutboxWorker(db, events, poll_interval=0.1)
    dispatched = worker.process_pending()

    assert dispatched == 1
    assert len(received) == 1
    assert received[0]["id"] == 1
    assert received[0]["origin_module"] == "outbox_worker"

    with db.get_connection() as conn:
        row = dict(conn.execute(
            "SELECT status, processado_em FROM _outbox_events WHERE id = ?", (event_id,)
        ).fetchone())
        assert row["status"] == "processado"
        assert row["processado_em"] is not None


def test_process_pending_recovers_event_never_emitted_in_memory(tmp_path):
    """Simula processo interrompido: o evento foi gravado na outbox (mesma
    transação da mutação de negócio) mas o processo caiu ANTES de chamar
    EventBus.emit() em memória. O worker deve recuperar e despachar mesmo assim."""
    db = Database(f"sqlite:///{tmp_path / 'o2.db'}")

    with db.get_connection() as conn:
        db.enqueue_outbox_event(conn, "pagamento_confirmado", {"id": 99, "valor": 150.0})
        conn.commit()
    # processo "morreu" aqui — nenhum events.emit() foi chamado nesta linha do tempo

    events = EventBus()
    received = []
    events.on("pagamento_confirmado", lambda p: received.append(p))

    worker = OutboxWorker(db, events)
    dispatched = worker.process_pending()

    assert dispatched == 1
    assert received[0]["id"] == 99
    assert received[0]["valor"] == 150.0


def test_process_pending_does_not_reprocess_already_dispatched(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'o3.db'}")
    events = EventBus()
    calls = []
    events.on("x_criado", lambda p: calls.append(p))
    worker = OutboxWorker(db, events)

    with db.get_connection() as conn:
        db.enqueue_outbox_event(conn, "x_criado", {"id": 1})
        conn.commit()

    assert worker.process_pending() == 1
    assert worker.process_pending() == 0  # já processado -> não reprocessa
    assert len(calls) == 1


def test_process_pending_batch_respects_limit_and_order(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'o4.db'}")
    events = EventBus()
    order = []
    events.on("y_criado", lambda p: order.append(p["id"]))
    worker = OutboxWorker(db, events)

    with db.get_connection() as conn:
        for i in range(5):
            db.enqueue_outbox_event(conn, "y_criado", {"id": i})
        conn.commit()

    dispatched = worker.process_pending(limit=3)
    assert dispatched == 3
    assert order == [0, 1, 2]

    dispatched_rest = worker.process_pending(limit=10)
    assert dispatched_rest == 2
    assert order == [0, 1, 2, 3, 4]


def test_process_pending_continues_after_one_handler_raises(tmp_path):
    """Um listener com bug em um evento não deve impedir o despacho dos demais."""
    db = Database(f"sqlite:///{tmp_path / 'o5.db'}")
    events = EventBus()
    ok_received = []

    def handler_com_bug(payload):
        raise RuntimeError("listener quebrado")

    events.on("falha_criado", handler_com_bug)
    events.on("ok_criado", lambda p: ok_received.append(p))

    worker = OutboxWorker(db, events)
    with db.get_connection() as conn:
        db.enqueue_outbox_event(conn, "falha_criado", {"id": 1})
        db.enqueue_outbox_event(conn, "ok_criado", {"id": 2})
        conn.commit()

    dispatched = worker.process_pending()

    # EventBus já isola exceções de handler internamente (ver events.py);
    # os dois eventos da outbox devem terminar marcados como processados.
    assert dispatched == 2
    assert len(ok_received) == 1
    assert ok_received[0]["id"] == 2
    assert ok_received[0]["event_name"] == "ok_criado"
    assert ok_received[0]["origin_module"] == "outbox_worker"


# ---------------------------------------------------------------------------
# Resiliência: crash pós-emit (redespacho idempotente) e dead-letter
# ---------------------------------------------------------------------------

def _status_evento(db, event_id):
    with db.get_connection() as conn:
        row = conn.execute(
            "SELECT status, tentativas, processado_em FROM _outbox_events WHERE id = ?", (event_id,)
        ).fetchone()
        return dict(row)


class EmitQueMorreDepoisDoPrimeiroEmit:
    """EventBus de mentira que simula crash do processo: o primeiro emit()
    passa (evento chegou aos listeners, como se tivesse sido publicado) e o
    processo morre ANTES de marcar como processado. Os emits seguintes falham
    até que o "processo volta" (crashado=False)."""

    def __init__(self, bus_real):
        self._bus_real = bus_real
        self.crashado = True

    def emit(self, event_name, payload, origin_module="system"):
        if self.crashado:
            self.crashado = False  # primeiro emit: pub acontece, depois "morre"
            self._bus_real.emit(event_name, payload, origin_module=origin_module)
            raise RuntimeError("CRASH_SIMULADO: processo morreu apos emit, antes de marcar processado")
        return self._bus_real.emit(event_name, payload, origin_module=origin_module)


def test_crash_pos_emit_redespacha_idempotente(tmp_path):
    """Crash imediatamente após o envio mas antes de atualizar status: o evento
    continua 'pendente' e é re-despachado no próximo ciclo. Listener idempotente
    recebe o mesmo payload duas vezes sem duplicar estado de negócio."""
    db = Database(f"sqlite:///{tmp_path / 'o6.db'}")
    events = EventBus()
    recebidos = []
    events.on("pedido_pago", lambda p: recebidos.append(p["id"]))

    with db.get_connection() as conn:
        event_id = db.enqueue_outbox_event(conn, "pedido_pago", {"id": 77})
        conn.commit()

    bus_crash = EmitQueMorreDepoisDoPrimeiroEmit(events)
    worker = OutboxWorker(db, bus_crash)

    # Ciclo 1: emit acontece, listener roda (recebidos == [77]), mas o processo
    # "morre" antes de marcar processado -> falha registrada, continua pendente
    assert worker.process_pending() == 0
    assert recebidos == [77]
    estado = _status_evento(db, event_id)
    assert estado["status"] == "pendente"
    assert estado["tentativas"] == 1

    # Estado de negócio NÃO duplicou (listener idempotente: mesmo payload 1x)

    # Ciclo 2 (processo voltou): redespacho idempotente entrega de novo e marca
    assert worker.process_pending() == 1
    assert recebidos == [77, 77]  # at-least-once: 2 entregas do mesmo evento
    estado = _status_evento(db, event_id)
    assert estado["status"] == "processado"
    assert estado["processado_em"] is not None


def test_dead_letter_apos_max_tentativas(tmp_path):
    """Listener que falha sistematicamente: após max_tentativas falhas o evento
    vai para 'dead_letter', sai da fila pendente e NÃO bloqueia eventos novos."""
    db = Database(f"sqlite:///{tmp_path / 'o7.db'}")
    events = EventBus()
    tentativas_recebidas = []

    def listener_quebrado(payload):
        raise RuntimeError("falha sistematica de integracao externa")

    events.on("webhook_quebrado", listener_quebrado)
    events.on("evento_saudavel", lambda p: tentativas_recebidas.append(p["id"]))

    worker = OutboxWorker(db, events, max_tentativas=3)

    with db.get_connection() as conn:
        id_quebrado = db.enqueue_outbox_event(conn, "webhook_quebrado", {"id": 1})
        id_saudavel = db.enqueue_outbox_event(conn, "evento_saudavel", {"id": 2})
        conn.commit()

    # Nota: o driver in-memory isola a exceção do listener, então o emit "succeeds"
    # do ponto de vista do worker (o evento é marcado como processado). Dead-letter
    # real cobre falhas que estouram ANTES/contra o barramento (emit levanta).
    # Para simular isso, fazemos o próprio emit levantar sempre:
    class EmitSempreFalha:
        def emit(self, event_name, payload, origin_module="system"):
            raise ConnectionError("barramento externo indisponivel")

    worker_falho = OutboxWorker(db, EmitSempreFalha(), max_tentativas=3)

    # Ciclo 1 e 2: falha, incrementa tentativas, continua pendente
    assert worker_falho.process_pending() == 0
    assert worker_falho.process_pending() == 0
    estado = _status_evento(db, id_quebrado)
    assert estado["status"] == "pendente"
    assert estado["tentativas"] == 2

    # Ciclo 3: atinge max_tentativas -> dead_letter
    assert worker_falho.process_pending() == 0
    estado = _status_evento(db, id_quebrado)
    assert estado["status"] == "dead_letter"
    assert estado["tentativas"] == 3

    # Dead-letter NÃO volta a ser processado (sai da fila 'pendente')
    assert worker_falho.process_pending() == 0
    estado = _status_evento(db, id_quebrado)
    assert estado["status"] == "dead_letter"
    assert estado["tentativas"] == 3

    # Evento saudável enfileirado depois NÃO é bloqueado pelo em dead-letter
    with db.get_connection() as conn:
        id_posterior = db.enqueue_outbox_event(conn, "evento_saudavel", {"id": 3})
        conn.commit()
    assert worker.process_pending() >= 1
    with db.get_connection() as conn:
        row = conn.execute("SELECT status FROM _outbox_events WHERE id = ?", (id_posterior,)).fetchone()
        assert dict(row)["status"] == "processado"


def test_listener_falho_nao_bloqueia_eventos_seguintes(tmp_path):
    """Um evento que sempre falha no emit não pode travar a fila: os seguintes
    são despachados normalmente no mesmo ciclo."""
    db = Database(f"sqlite:///{tmp_path / 'o8.db'}")
    events = EventBus()
    ok = []
    events.on("bom", lambda p: ok.append(p["id"]))

    class EmitFalhaPorNome:
        def __init__(self, bus_real, nome_quebrado):
            self._bus_real = bus_real
            self._nome_quebrado = nome_quebrado

        def emit(self, event_name, payload, origin_module="system"):
            if event_name == self._nome_quebrado:
                raise ConnectionError("destino indisponivel")
            return self._bus_real.emit(event_name, payload, origin_module=origin_module)

    worker = OutboxWorker(db, EmitFalhaPorNome(events, "ruim"), max_tentativas=2)

    with db.get_connection() as conn:
        id_ruim = db.enqueue_outbox_event(conn, "ruim", {"id": 1})
        id_bom1 = db.enqueue_outbox_event(conn, "bom", {"id": 2})
        id_bom2 = db.enqueue_outbox_event(conn, "bom", {"id": 3})
        conn.commit()

    despachados = worker.process_pending()

    assert despachados == 2  # os dois 'bom'
    assert ok == [2, 3]
    estado = _status_evento(db, id_ruim)
    assert estado["status"] == "pendente"
    assert estado["tentativas"] == 1

    # Segunda falha -> dead_letter (max_tentativas=2)
    worker.process_pending()
    estado = _status_evento(db, id_ruim)
    assert estado["status"] == "dead_letter"
    assert estado["tentativas"] == 2


# ---------------------------------------------------------------------------
# Claim atômico (exclusão mútua), lease, seq monotônico e deduplicação
# ---------------------------------------------------------------------------

def _status_claim(db, event_id):
    """Linha completa do evento, para inspecionar claim_atômico e seq."""
    with db.get_connection() as conn:
        row = conn.execute("SELECT * FROM _outbox_events WHERE id = ?", (event_id,)).fetchone()
        return dict(row)


def test_seq_monotonico_atribuido_no_enqueue(tmp_path):
    """DoD #1: `seq` monotônico (MAX+1 por transação) atribuído na gravação."""
    db = Database(f"sqlite:///{tmp_path / 'seq1.db'}")
    with db.get_connection() as conn:
        for i in range(5):
            db.enqueue_outbox_event(conn, "seq_criado", {"id": i})
        conn.commit()

    with db.get_connection() as conn:
        seqs = [dict(r)["seq"] for r in conn.execute(
            "SELECT seq FROM _outbox_events ORDER BY seq").fetchall()]
    assert seqs == [1, 2, 3, 4, 5]

    # Persistência monotônica: nova instância segue a sequência sem reiniciar
    db2 = Database(f"sqlite:///{tmp_path / 'seq1.db'}")
    with db2.get_connection() as conn:
        db2.enqueue_outbox_event(conn, "seq_criado", {"id": 99})
        conn.commit()
    with db2.get_connection() as conn:
        seqs = [dict(r)["seq"] for r in conn.execute(
            "SELECT seq FROM _outbox_events ORDER BY seq").fetchall()]
    assert seqs == [1, 2, 3, 4, 5, 6]


def test_claim_atomico_exclusao_mutua_e_lease(tmp_path):
    """DoD #2: claim via UPDATE guardado por status='pendente' AND claimed_at IS NULL.
    Enquanto o claim é válido outro worker NÃO processa; com lease expirado o
    evento órfão é recuperado e despachado exatamente uma vez."""
    db = Database(f"sqlite:///{tmp_path / 'claim.db'}")
    events = EventBus()
    recebidos = []
    events.on("cobranca_criada", lambda p: recebidos.append(p["id"]))

    with db.get_connection() as conn:
        event_id = db.enqueue_outbox_event(conn, "cobranca_criada", {"id": 7})
        conn.commit()

    worker_a = OutboxWorker(db, events, worker_id="worker-A", claim_lease_seconds=60)
    worker_b = OutboxWorker(db, events, worker_id="worker-B", claim_lease_seconds=60)

    claimados = worker_a._claim_pendentes(1)
    assert len(claimados) == 1 and claimados[0]["id"] == event_id
    estado = _status_claim(db, event_id)
    assert estado["claimed_by"] == "worker-A"
    assert estado["claimed_at"] is not None
    assert estado["status"] == "pendente"
    assert recebidos == []

    # Exclusão mútua: worker B não reprocessa enquanto o claim (lease) for válido
    assert worker_b.process_pending() == 0
    estado = _status_claim(db, event_id)
    assert estado["claimed_by"] == "worker-A"
    assert estado["status"] == "pendente"
    assert recebidos == []

    # Lease expirado: B recupera o evento órfão (crash do worker A) e despacha 1x
    time.sleep(0.05)  # garante claimed_at < limiar mesmo com relógio grosseiro
    worker_b_lease = OutboxWorker(db, events, worker_id="worker-B", claim_lease_seconds=0)
    assert worker_b_lease.process_pending() == 1
    assert recebidos == [7]
    estado = _status_claim(db, event_id)
    assert estado["status"] == "processado"
    assert estado["claimed_at"] is None and estado["claimed_by"] is None


def test_dois_workers_concorrentes_cada_evento_exatamente_uma_vez(tmp_path):
    """Critério de saída: 2 workers concorrentes processam cada evento exatamente
    1 vez (claim atômico com exclusão mútua)."""
    db = Database(f"sqlite:///{tmp_path / 'conc2.db'}")
    total = 60
    with db.get_connection() as conn:
        for i in range(total):
            db.enqueue_outbox_event(conn, "conc_criado", {"id": i})
        conn.commit()

    events = EventBus()
    lock = threading.Lock()
    emissoes = []

    def handler(payload):
        with lock:
            emissoes.append(payload["id"])

    events.on("conc_criado", handler)

    start = threading.Barrier(3)

    def roda(wid):
        worker = OutboxWorker(db, events, worker_id=wid, claim_lease_seconds=60)
        start.wait()
        while True:
            worker.process_pending(limit=1)
            with db.get_connection() as conn:
                pendentes = conn.execute(
                    "SELECT COUNT(*) FROM _outbox_events WHERE status = 'pendente'"
                ).fetchone()[0]
            if pendentes == 0:
                break

    ta = threading.Thread(target=roda, args=("worker-A",))
    tb = threading.Thread(target=roda, args=("worker-B",))
    ta.start()
    tb.start()
    start.wait()
    ta.join(timeout=60)
    tb.join(timeout=60)
    assert not ta.is_alive(), "worker-A travou no processamento"
    assert not tb.is_alive(), "worker-B travou no processamento"

    contagem = Counter(emissoes)
    assert len(contagem) == total, f"{total - len(contagem)} evento(s) não emitido(s)"
    for i in range(total):
        assert contagem[i] == 1, f"evento {i} emitido {contagem[i]}x (duplica em processamento!)"

    with db.get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) FROM _outbox_events WHERE status = 'processado'").fetchone()
        assert row[0] == total


def test_listener_falho_move_para_dead_letter_sem_loop_infinito(tmp_path):
    """Critério de saída: listener falho vai para dead-letter após N tentativas e
    NÃO entra em loop infinito — ciclos extras não re-emitam nem incrementam."""
    db = Database(f"sqlite:///{tmp_path / 'dl_loop.db'}")
    tentativas_emit = []

    class EmitSempreFalha:
        def emit(self, event_name, payload, origin_module="system"):
            tentativas_emit.append(event_name)
            raise ConnectionError("barramento externo indisponivel")

    with db.get_connection() as conn:
        event_id = db.enqueue_outbox_event(conn, "webhook_falho", {"id": 1})
        conn.commit()

    worker = OutboxWorker(db, EmitSempreFalha(), max_tentativas=3, claim_lease_seconds=60)
    for _ in range(12):  # muitos ciclos: muito além do max_tentativas
        worker.process_pending()

    estado = _status_claim(db, event_id)
    assert estado["status"] == "dead_letter"
    assert estado["tentativas"] == 3
    assert len(tentativas_emit) == 3  # exatamente N tentativas: sem loop infinito


def test_registro_idempotente_de_evento_processado(tmp_path):
    """DoD #4: _eventos_processados registra high-water mark por consumer e
    detecta entrega duplicada."""
    db = Database(f"sqlite:///{tmp_path / 'dedup0.db'}")
    with db.get_connection() as conn:
        eid = db.enqueue_outbox_event(conn, "fatura_paga", {"id": 42})
        seq = conn.execute("SELECT seq FROM _outbox_events WHERE id = ?", (eid,)).fetchone()[0]
        conn.commit()

    with db.get_connection() as conn:
        assert db.evento_ja_processado(conn, eid) is False
        assert db.ultimo_seq_processado(conn, "contabil") is None
        assert db.registrar_evento_processado(conn, eid, seq, "fatura_paga", consumer_id="contabil") is True
        assert db.registrar_evento_processado(conn, eid, seq, "fatura_paga", consumer_id="contabil") is False
        assert db.evento_ja_processado(conn, eid) is True
        assert db.ultimo_seq_processado(conn, "contabil") == seq
        conn.commit()


def test_dedup_consumidor_evita_efeito_colateral_duplicado(tmp_path):
    """Redespacho at-least-once (crash pós-emit) entrega o evento 2x; consumidor
    idempotente via outbox_event_id/outbox_seq aplica o efeito colateral 1x."""
    db = Database(f"sqlite:///{tmp_path / 'dedup1.db'}")
    events = EventBus()
    entregas = []
    efeitos = []

    def consumidor(payload):
        entregas.append(payload["id"])
        with db.get_connection() as conn:
            if db.evento_ja_processado(conn, payload["outbox_event_id"]):
                return
            db.registrar_evento_processado(
                conn,
                payload["outbox_event_id"],
                payload["outbox_seq"],
                payload["event_name"],
                consumer_id="contabil",
            )
            conn.commit()
        efeitos.append(payload["id"])

    events.on("fatura_paga", consumidor)
    with db.get_connection() as conn:
        db.enqueue_outbox_event(conn, "fatura_paga", {"id": 42})
        conn.commit()

    bus_crash = EmitQueMorreDepoisDoPrimeiroEmit(events)
    worker = OutboxWorker(db, bus_crash)

    assert worker.process_pending() == 0  # 1ª entrega; crash antes de marcar
    assert worker.process_pending() == 1  # redespacho; marca como processado
    assert entregas == [42, 42]           # at-least-once: evento chegou 2x
    assert efeitos == [42]                # idempotência: efeito colateral 1x
