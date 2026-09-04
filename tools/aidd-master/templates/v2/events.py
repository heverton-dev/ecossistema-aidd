# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.0-Beta — EventBus com Driver Distribuído Plugável (Redis Streams)
=============================================================================
EventBus é uma fachada que delega para um EventBusDriver escolhido a partir de
EVENTBUS_URL. Por padrão (Zero Fricção) usa InMemoryEventBusDriver — nenhuma
mudança de comportamento para quem já usa `EventBus()` sem argumentos. Quando
EVENTBUS_URL aponta para um Redis, o RedisStreamsDriver distribui eventos entre
múltiplas instâncias/processos via Redis Streams + Consumer Groups (at-least-once,
cada mensagem processada por exatamente um consumidor do grupo).
"""

import os
import json
import time
import uuid
import datetime
import threading
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Callable, Any, Dict, Optional
from dataclasses import dataclass, field

@dataclass
class Event:
    name: str
    payload: Dict[str, Any]
    correlation_id: str = ""


class EventBusDriver(ABC):
    """Contrato mínimo de transporte pub/sub que o EventBus delega."""

    @abstractmethod
    def subscribe(self, event_name: str, handler: Callable[[Any], None]):
        ...

    @abstractmethod
    def publish(self, event_name: str, payload: Dict[str, Any]):
        ...


class InMemoryEventBusDriver(EventBusDriver):
    """Driver padrão (Zero Setup): pub/sub em memória, escopo do processo atual."""

    def __init__(self):
        self._listeners = defaultdict(list)

    def subscribe(self, event_name: str, handler: Callable[[Any], None]):
        self._listeners[event_name].append(handler)

    def publish(self, event_name: str, payload: Dict[str, Any]):
        for handler in self._listeners.get(event_name, []):
            try:
                handler(payload)
            except Exception as e:
                print(f"[EVENT_ERROR] Falha ao processar evento '{event_name}': {e}")


class RedisStreamsDriver(EventBusDriver):
    """Driver distribuído: publica via XADD e consome via XREADGROUP com um
    Consumer Group por processo, permitindo escalar horizontalmente entre
    múltiplas instâncias sem perder sincronização de eventos."""

    def __init__(self, redis_url: str, group_name: str = "aidd-suite", consumer_name: Optional[str] = None):
        try:
            import redis
        except ImportError:
            raise RuntimeError("redis não instalado. Para EventBus distribuído, instale: pip install redis")
        self._redis = redis.from_url(redis_url, decode_responses=True)
        self._group_name = group_name
        self._consumer_name = consumer_name or uuid.uuid4().hex[:8]
        self._listeners = defaultdict(list)
        self._threads: Dict[str, threading.Thread] = {}
        self._running = True

    @staticmethod
    def _stream_key(event_name: str) -> str:
        return f"aidd:events:{event_name}"

    def subscribe(self, event_name: str, handler: Callable[[Any], None]):
        self._listeners[event_name].append(handler)
        stream_key = self._stream_key(event_name)
        try:
            self._redis.xgroup_create(stream_key, self._group_name, id="0", mkstream=True)
        except Exception as e:
            if "BUSYGROUP" not in str(e):
                raise

        if event_name not in self._threads:
            t = threading.Thread(
                target=self._consume_loop, args=(event_name,),
                name=f"AIDD-EventBus-{event_name}", daemon=True
            )
            t.start()
            self._threads[event_name] = t

    def publish(self, event_name: str, payload: Dict[str, Any]):
        stream_key = self._stream_key(event_name)
        self._redis.xadd(stream_key, {"payload": json.dumps(payload, ensure_ascii=False)})

    def _consume_loop(self, event_name: str):
        stream_key = self._stream_key(event_name)
        while self._running:
            try:
                resp = self._redis.xreadgroup(
                    self._group_name, self._consumer_name,
                    {stream_key: ">"}, count=10, block=1000
                )
                for _stream_name, messages in resp:
                    for msg_id, fields in messages:
                        try:
                            payload = json.loads(fields["payload"])
                            for handler in self._listeners.get(event_name, []):
                                try:
                                    handler(payload)
                                except Exception as e:
                                    print(f"[EVENT_ERROR] Falha ao processar evento '{event_name}': {e}")
                            self._redis.xack(stream_key, self._group_name, msg_id)
                        except Exception as e:
                            print(f"[EVENT_ERROR] Falha ao decodificar mensagem {msg_id} de '{event_name}': {e}")
            except Exception as e:
                print(f"[EVENTBUS_ERROR] Falha no consumo do stream '{stream_key}': {e}")
                time.sleep(1)

    def stop(self):
        self._running = False


def _default_driver() -> EventBusDriver:
    eventbus_url = os.getenv("EVENTBUS_URL")
    if eventbus_url:
        return RedisStreamsDriver(eventbus_url)
    return InMemoryEventBusDriver()


class EventBus:
    """EventBus Pub/Sub com enriquecimento de metadados, tracing UUID e isolamento
    de erros. A API pública (on/emit) é idêntica independente do driver escolhido."""

    def __init__(self, driver: Optional[EventBusDriver] = None):
        self._driver = driver if driver is not None else _default_driver()

    def on(self, event_name: str, handler: Callable[[Any], None]):
        self._driver.subscribe(event_name, handler)

    def emit(self, event_name: str, data: Any = None, origin_module: str = "system") -> Dict[str, Any]:
        payload = data if isinstance(data, dict) else ({"value": data} if data is not None else {})
        if isinstance(payload, dict):
            if "event_id" not in payload:
                payload["event_id"] = uuid.uuid4().hex[:12]
            if "event_name" not in payload:
                payload["event_name"] = event_name
            if "origin_module" not in payload:
                payload["origin_module"] = origin_module
            if "timestamp" not in payload:
                payload["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

        self._driver.publish(event_name, payload)
        return payload
