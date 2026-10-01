import threading, time, json, hashlib
from typing import Callable, Any

class ReadModelCache:
    """Cache CQRS: snapshots pré-computados de queries de leitura (Materialized View em memória)."""
    def __init__(self, now_fn: Callable[[], float] = time.time):
        self._store: dict = {}
        self._lock = threading.Lock()
        self._now_fn = now_fn

    def set(self, key: str, value: Any, ttl: int = 60):
        with self._lock:
            self._store[key] = {"value": value, "expires": self._now_fn() + ttl, "stale": False}

    def get(self, key: str):
        with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None, False
            stale = self._now_fn() > entry["expires"]
            return entry["value"], stale

    def invalidate(self, key: str):
        with self._lock:
            self._store.pop(key, None)

    def invalidate_prefix(self, prefix: str):
        with self._lock:
            keys_to_del = [k for k in self._store if k.startswith(prefix)]
            for k in keys_to_del:
                self._store.pop(k, None)

    def get_or_revalidate(self, key: str, fetcher: Callable, ttl: int = 60):
        """Stale-While-Revalidate: retorna o cache imediatamente e revalida em background."""
        value, stale = self.get(key)
        if value is not None:
            if stale:
                threading.Thread(target=lambda: self.set(key, fetcher(), ttl), daemon=True).start()
            return value
        fresh = fetcher()
        self.set(key, fresh, ttl)
        return fresh

read_model = ReadModelCache()  # Singleton global
