# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD Núcleo Compartilhado — Transaction Log com Cache LRU
(PLAN-0017, item transactionlog-lru-cache)
=============================================================================
Transaction log append-only com integridade por cadeia de hash (SHA-256
encadeado, mesmo padrão garantido pelo ``_audit_log``) e cache LRU de
capacity configurável para leituras por id.

Semânticas de persistência garantidas:

- **Escrita (write-through no commit):** ``registrar_log`` abre uma conexão,
  insere na tabela ``_transaction_log``, faz commit e SÓ ENTÃO alimenta o
  cache — o cache nunca expõe um registro que não foi persistido.
  ``append`` é o nível baixo: insere na transação do chamador e não toca o
  cache (o commit pertence ao chamador).
- **Leitura (read-through):** ``get`` consulta o cache primeiro (hit) e, no
  miss, cai no banco e popula o cache.
- **Métricas de uso e evicção:** hit/miss/hit_ratio/size/capacity/evictions
  expostos por ``cache_metrics()`` e, opcionalmente, publicados como
  contadores Prometheus no ``core.metrics.MetricsRegistry`` existente.

Zero dependências novas: apenas stdlib (``collections.OrderedDict``,
``threading``, ``hashlib``, ``json``) e a fachada ``Database`` já existente
(duck-typed — qualquer objeto com ``get_connection()``).
"""

from __future__ import annotations

import hashlib
import json
import threading
import uuid
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from logs import get_logger

logger = get_logger("core.transaction_log")

DEFAULT_CACHE_CAPACITY = 128
_ZERO_HASH = "0" * 64


class LruCache:
    """Cache LRU (Least Recently Used) thread-safe com métricas de uso e evicção.

    - ``get`` marca a chave como mais recentemente usada (MRU) e registra
      hit/miss.
    - ``put`` insere/atualiza e, ao estourar a ``capacity``, evicta a entrada
      menos recentemente usada (LRU), contabilizando a evicção.
    - ``registry`` opcional (``core.metrics.MetricsRegistry``) ainda publica
      os mesmos contadores no formato de exposição Prometheus.
    """

    def __init__(self, capacity: int = DEFAULT_CACHE_CAPACITY, registry: Any = None):
        if capacity < 1:
            raise ValueError(f"LRU capacity deve ser >= 1 (recebido: {capacity})")
        self._capacity = int(capacity)
        self._store: "OrderedDict[str, Any]" = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._registry = registry
        self._counters: Optional[Dict[str, Any]] = None

    # ------------------------------------------------------------------ #
    # API pública
    # ------------------------------------------------------------------ #

    @property
    def capacity(self) -> int:
        """Capacidade máxima configurada no construtor."""
        return self._capacity

    @property
    def size(self) -> int:
        """Número atual de chaves residentes no cache."""
        return len(self)

    def __len__(self) -> int:
        with self._lock:
            return len(self._store)

    def __contains__(self, key: str) -> bool:
        with self._lock:
            return key in self._store

    def get(self, key: str) -> Optional[Any]:
        """Retorna o valor de ``key`` ou None em caso de miss.

        Hit move a chave para a ponta MRU; miss registra métrica de miss.
        """
        with self._lock:
            valor = self._store.get(key)
            if valor is None:
                self._misses += 1
                self._bump("misses")
                return None
            self._store.move_to_end(key)
            self._hits += 1
            self._bump("hits")
            return valor

    def put(self, key: str, value: Any):
        """Insere/atualiza ``key``. Quando o tamanho excede a ``capacity``,
        evicta a entrada LRU e registra a métrica de evicção."""
        with self._lock:
            if key in self._store:
                self._store[key] = value
                self._store.move_to_end(key)
                return
            self._store[key] = value
            while len(self._store) > self._capacity:
                self._store.popitem(last=False)
                self._evictions += 1
                self._bump("evictions")

    def clear(self):
        """Remove todas as entradas. Contadores cumulative de hit/miss/evicção
        são preservados (medição do ciclo de vida do cache)."""
        with self._lock:
            self._store.clear()

    def metrics(self) -> Dict[str, Any]:
        """Métricas de uso e evicção do cache."""
        with self._lock:
            total = self._hits + self._misses
            hit_ratio = (self._hits / total) if total > 0 else 0.0
            return {
                "capacity": self._capacity,
                "size": len(self._store),
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "hit_ratio": hit_ratio,
            }

    # ------------------------------------------------------------------ #
    # Integração com o registry Prometheus existente (core.metrics)
    # ------------------------------------------------------------------ #

    def _bump(self, nome: str):
        if self._registry is None:
            return
        if self._counters is None:
            from metrics import Counter

            self._counters = {
                "hits": Counter(
                    "transaction_log_lru_hits_total",
                    "Hits no cache LRU do transaction log",
                ),
                "misses": Counter(
                    "transaction_log_lru_misses_total",
                    "Misses no cache LRU do transaction log",
                ),
                "evictions": Counter(
                    "transaction_log_lru_evictions_total",
                    "Eviccoes no cache LRU do transaction log",
                ),
            }
            for counter in self._counters.values():
                self._registry.register(counter)
        self._counters[nome].inc()


@dataclass(frozen=True)
class TransactionLogEntry:
    """Entrada imutável de transaction log, com cadeia de hash encadeada.

    ``curr_hash`` = SHA-256(``prev_hash`` | ``action`` | payload JSON canônico)
    permite detectar qualquer adulteração posterior da linha no banco.
    """

    id: str
    timestamp: str
    action: str
    payload: Dict[str, Any]
    prev_hash: str
    curr_hash: str

    @staticmethod
    def computar_hash(prev_hash: str, action: str, payload: Dict[str, Any]) -> str:
        """Recomputa o hash da cadeia a partir dos campos de negócio."""
        payload_json = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        material = f"{prev_hash}|{action}|{payload_json}".encode("utf-8")
        return hashlib.sha256(material).hexdigest()

    def validar_integridade(self) -> bool:
        """True se o ``curr_hash`` ainda é o hash derivado dos campos atuais."""
        return self.curr_hash == self.computar_hash(self.prev_hash, self.action, self.payload)

    @classmethod
    def from_row(cls, row: Any) -> "TransactionLogEntry":
        """Converte uma linha SQLite (``sqlite3.Row``/dict) em entidade."""
        dados = dict(row)
        return cls(
            id=dados["id"],
            timestamp=dados["timestamp"],
            action=dados["action"],
            payload=json.loads(dados["payload"]),
            prev_hash=dados["prev_hash"],
            curr_hash=dados["curr_hash"],
        )


class TransactionLogRepositoryImpl:
    """Implementação do repositório de transaction log sobre SQLite.

    Persistência: append-only na tabela ``_transaction_log`` com cadeia de
    hash (``prev_hash`` -> ``curr_hash``) para detecção de adulteração.

    Cache LRU (capacity configurável, padrão ``DEFAULT_CACHE_CAPACITY``):
    leituras por id são read-through (cache-first com fallback ao banco) e
    gravações são write-through apenas após o commit — o cache nunca expõe
    registro não persistido.
    """

    def __init__(
        self,
        db: Any,
        cache_capacity: int = DEFAULT_CACHE_CAPACITY,
        registry: Any = None,
    ):
        self._db = db
        self._cache = LruCache(capacity=cache_capacity, registry=registry)

    def _conectar(self):
        return self._db.get_connection()

    # ------------------------------------------------------------------ #
    # Schema
    # ------------------------------------------------------------------ #

    @staticmethod
    def criar_tabela(conn: Any):
        """Cria (idempotente) a tabela de transaction log e seu índice."""
        conn.execute(
            "CREATE TABLE IF NOT EXISTS _transaction_log ("
            "id TEXT PRIMARY KEY,"
            "timestamp TEXT NOT NULL,"
            "action TEXT NOT NULL,"
            "payload TEXT NOT NULL,"
            "prev_hash TEXT NOT NULL,"
            "curr_hash TEXT NOT NULL"
            ");"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_transaction_log_timestamp "
            "ON _transaction_log(timestamp);"
        )

    # ------------------------------------------------------------------ #
    # Escrita
    # ------------------------------------------------------------------ #

    def append(self, conn: Any, action: str, payload: Dict[str, Any]) -> TransactionLogEntry:
        """Insere um registro na transação do chamador (sem commit).

        Nível baixo: por não conhecer o ponto de commit, NÃO alimenta o cache
        — quem quiser o caminho completo com write-through usa ``registrar_log``.
        """
        self.criar_tabela(conn)
        anterior = conn.execute(
            "SELECT curr_hash FROM _transaction_log "
            "ORDER BY timestamp DESC, id DESC LIMIT 1"
        ).fetchone()
        prev_hash = (anterior["curr_hash"] if isinstance(anterior, dict) else anterior[0]) if anterior else _ZERO_HASH
        timestamp = datetime.now(timezone.utc).isoformat()
        log_id = uuid.uuid4().hex
        curr_hash = TransactionLogEntry.computar_hash(prev_hash, action, payload)
        conn.execute(
            "INSERT INTO _transaction_log (id, timestamp, action, payload, prev_hash, curr_hash) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                log_id,
                timestamp,
                action,
                json.dumps(payload, ensure_ascii=False),
                prev_hash,
                curr_hash,
            ),
        )
        return TransactionLogEntry(
            id=log_id,
            timestamp=timestamp,
            action=action,
            payload=dict(payload),
            prev_hash=prev_hash,
            curr_hash=curr_hash,
        )

    def registrar_log(self, action: str, payload: Dict[str, Any]) -> TransactionLogEntry:
        """Caminho de escrita completo (write-through no commit).

        Abre conexão própria, insere, commita e SÓ ENTÃO insere no cache.
        Se a transação falhar, o cache permanece intacto (nenhum registro
        não persistido é observável por ``get``).
        """
        with self._conectar() as conn:
            entry = self.append(conn, action, payload)
            conn.commit()
        self._cache.put(entry.id, entry)
        return entry

    # ------------------------------------------------------------------ #
    # Leitura
    # ------------------------------------------------------------------ #

    def get(self, log_id: str) -> Optional[TransactionLogEntry]:
        """Leitura por id em modo read-through: cache-first, fallback ao banco.

        Hit não toca o banco; miss consulta o SQLite e popula o cache.
        """
        cached = self._cache.get(log_id)
        if cached is not None:
            return cached
        with self._conectar() as conn:
            self.criar_tabela(conn)
            row = conn.execute(
                "SELECT * FROM _transaction_log WHERE id = ?",
                (log_id,),
            ).fetchone()
        if row is None:
            return None
        entry = TransactionLogEntry.from_row(row)
        self._cache.put(entry.id, entry)
        return entry

    def list_recent(self, limit: int = 100) -> List[TransactionLogEntry]:
        """Lista os registros mais recentes (ordem decrescente de timestamp).

        A leitura é autorizada pelo banco (ordenação é responsabilidade da
        persistência) e as entradas retornadas são usadas para aquecer o
        cache — leituras subsequentes por id saem de hit.
        """
        if limit < 1:
            raise ValueError(f"limit deve ser >= 1 (recebido: {limit})")
        with self._conectar() as conn:
            self.criar_tabela(conn)
            rows = conn.execute(
                "SELECT * FROM _transaction_log "
                "ORDER BY timestamp DESC, id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        entradas = [TransactionLogEntry.from_row(r) for r in rows]
        for entry in entradas:
            self._cache.put(entry.id, entry)
        return entradas

    def count(self) -> int:
        """Total de registros persistidos na tabela."""
        with self._conectar() as conn:
            self.criar_tabela(conn)
            row = conn.execute("SELECT count(*) FROM _transaction_log").fetchone()
        return int(row[0])

    # ------------------------------------------------------------------ #
    # Métricas do cache
    # ------------------------------------------------------------------ #

    def cache_metrics(self) -> Dict[str, Any]:
        """Métricas de uso e evicção do cache LRU (ver ``LruCache.metrics``)."""
        return self._cache.metrics()

    @property
    def cache_capacity(self) -> int:
        """Capacidade configurada do cache LRU."""
        return self._cache.capacity