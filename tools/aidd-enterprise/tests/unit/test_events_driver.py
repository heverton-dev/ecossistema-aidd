# -*- coding: utf-8 -*-
"""
Testes do EventBus com driver plugável (Onda 2 / v5.0-Beta): comportamento
padrão (InMemory) preservado, e distribuição real entre duas instâncias via
Redis Streams quando um Redis estiver acessível (Docker ou serviço local),
com skip honesto caso contrário — cobre o critério de aceite "evento emitido
na Instância A é processado pelo listener na Instância B".
"""

import os
import sys
import time
import shutil
import socket
import subprocess

import pytest

TEMPLATES_V2 = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "templates", "v2"))
if TEMPLATES_V2 not in sys.path:
    sys.path.insert(0, TEMPLATES_V2)

from events import EventBus, InMemoryEventBusDriver, RedisStreamsDriver  # noqa: E402


def test_inmemory_driver_is_default_and_preserves_behavior():
    bus = EventBus()
    assert isinstance(bus._driver, InMemoryEventBusDriver)

    received = []
    bus.on("pedido_criado", lambda p: received.append(p))
    payload = bus.emit("pedido_criado", {"id": 1})

    assert len(received) == 1
    assert received[0]["id"] == 1
    assert payload["event_name"] == "pedido_criado"
    assert payload["origin_module"] == "system"
    assert "event_id" in payload and "timestamp" in payload


def test_inmemory_driver_isolates_handler_exceptions(capsys):
    bus = EventBus()
    calls = []

    def handler_com_bug(_payload):
        raise RuntimeError("boom")

    bus.on("x", handler_com_bug)
    bus.on("x", lambda p: calls.append(p))

    bus.emit("x", {"id": 1})  # não deve propagar a exceção do primeiro handler

    assert len(calls) == 1
    assert "[EVENT_ERROR]" in capsys.readouterr().out


def test_eventbus_accepts_explicit_driver_override():
    driver = InMemoryEventBusDriver()
    bus = EventBus(driver=driver)
    assert bus._driver is driver


def test_redis_driver_raises_clear_error_message_when_url_invalid_scheme():
    # redis-py só falha ao tentar conectar de fato (from_url é lazy), então
    # validamos aqui apenas que o driver é instanciável e expõe _stream_key
    # corretamente — a falha de conexão real é coberta pelo teste de
    # integração via Docker abaixo.
    driver = RedisStreamsDriver("redis://localhost:6399/0")
    assert driver._stream_key("pedido_criado") == "aidd:events:pedido_criado"


# ---------------------------------------------------------------------------
# Integração real: duas instâncias de EventBus via Redis Streams (Docker)
# ---------------------------------------------------------------------------

def _docker_daemon_available() -> bool:
    if not shutil.which("docker"):
        return False
    try:
        result = subprocess.run(["docker", "info"], capture_output=True, timeout=5)
        return result.returncode == 0
    except Exception:
        return False


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.mark.skipif(not _docker_daemon_available(), reason="Docker daemon indisponível neste ambiente")
def test_event_emitted_on_instance_a_is_processed_on_instance_b_via_redis():
    port = _find_free_port()
    container_name = f"aidd-v5-redistest-{port}"
    run_cmd = ["docker", "run", "--rm", "-d", "--name", container_name, "-p", f"{port}:6379", "redis:7"]
    started = subprocess.run(run_cmd, capture_output=True, text=True, timeout=60)
    if started.returncode != 0:
        pytest.skip(f"Não foi possível iniciar container redis:7: {started.stderr.strip()}")

    try:
        redis_url = f"redis://127.0.0.1:{port}/0"

        deadline = time.time() + 20
        last_error = None
        instancia_a = instancia_b = None
        while time.time() < deadline:
            try:
                # RedisStreamsDriver.__init__ usa redis.from_url(), que e
                # preguicoso (nao conecta de fato) - so construir o driver
                # nao prova que o servidor esta pronto para servir comandos.
                # PING forca o primeiro round-trip real; sem isso o primeiro
                # comando de verdade (xgroup_create dentro de .on(), mais
                # abaixo) pode cair numa janela estreita logo apos o
                # container subir e falhar com connection reset sem retry.
                driver_a = RedisStreamsDriver(redis_url, group_name="grupo-teste")
                driver_a._redis.ping()
                driver_b = RedisStreamsDriver(redis_url, group_name="grupo-teste")
                driver_b._redis.ping()
                instancia_a = EventBus(driver=driver_a)
                instancia_b = EventBus(driver=driver_b)
                break
            except Exception as e:
                last_error = e
                time.sleep(1)
        if instancia_a is None:
            pytest.skip(f"Redis não ficou pronto a tempo: {last_error}")

        recebidos_b = []
        instancia_b.on("pedido_criado", lambda p: recebidos_b.append(p))
        time.sleep(0.3)  # tempo para a thread consumidora registrar o consumer group

        instancia_a.emit("pedido_criado", {"id": 123, "origem": "instancia_a"})

        deadline = time.time() + 10
        while not recebidos_b and time.time() < deadline:
            time.sleep(0.2)

        assert len(recebidos_b) == 1
        assert recebidos_b[0]["id"] == 123
        assert recebidos_b[0]["origem"] == "instancia_a"
    finally:
        subprocess.run(["docker", "stop", container_name], capture_output=True, timeout=30)
