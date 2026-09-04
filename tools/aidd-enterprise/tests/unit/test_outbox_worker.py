# -*- coding: utf-8 -*-
"""
Testes do OutboxWorker (Onda 1 / v5.0-Alpha): valida o critério de aceite do
Transactional Outbox Pattern — "simulação de interrupção de processo com
recuperação e despacho 100% íntegro de eventos pendentes".
"""

import os
import sys

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
