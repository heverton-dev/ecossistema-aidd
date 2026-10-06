from core.events import EventBus


def test_emit_calls_all_registered_handlers():
    bus = EventBus()
    recebidos = []
    bus.on("pedido_criado", lambda d: recebidos.append(("h1", d)))
    bus.on("pedido_criado", lambda d: recebidos.append(("h2", d)))

    bus.emit("pedido_criado", {"id": 42})

    assert recebidos == [("h1", {"id": 42}), ("h2", {"id": 42})]


def test_emit_without_subscribers_does_not_raise():
    bus = EventBus()
    bus.emit("evento_sem_ouvinte", {"x": 1})


def test_handler_exception_does_not_stop_other_handlers(capsys):
    bus = EventBus()
    chamado = []

    def handler_com_erro(_dados):
        raise RuntimeError("falha proposital")

    def handler_ok(dados):
        chamado.append(dados)

    bus.on("evento_misto", handler_com_erro)
    bus.on("evento_misto", handler_ok)

    bus.emit("evento_misto", {"ok": True})

    assert chamado == [{"ok": True}]
    saida = capsys.readouterr().out
    assert "EventBus Error" in saida


def test_on_same_event_multiple_times_accumulates_handlers():
    bus = EventBus()
    contador = {"n": 0}
    bus.on("tick", lambda d: contador.__setitem__("n", contador["n"] + 1))
    bus.on("tick", lambda d: contador.__setitem__("n", contador["n"] + 1))

    bus.emit("tick", {})

    assert contador["n"] == 2
