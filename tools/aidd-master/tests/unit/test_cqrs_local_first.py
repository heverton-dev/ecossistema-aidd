import threading
import pytest
import sys
import os

TEMPLATES_V2 = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "templates", "v2"))
if TEMPLATES_V2 not in sys.path:
    sys.path.insert(0, TEMPLATES_V2)

from cqrs import ReadModelCache
from local_first import CRDTSet
from circuit_breaker import CircuitBreaker, CircuitState
from saga import SagaOrchestrator, SagaStep


def _aguardar_condicao(condicao, timeout=5.0, intervalo=0.01):
    """Polling determinístico com deadline (Item 4): nunca dorme mais do que o
    necessário e falha com mensagem clara se a condição não chegar a tempo."""
    import time
    prazo = time.monotonic() + timeout
    while time.monotonic() < prazo:
        if condicao():
            return True
        time.sleep(intervalo)
    return False


def test_read_model_cache_set_and_get():
    cache = ReadModelCache()
    cache.set("test_key", "value", ttl=10)
    val, stale = cache.get("test_key")
    assert val == "value"
    assert not stale

def test_read_model_cache_stale_after_ttl():
    cache = ReadModelCache()
    cache.set("short_ttl", "data", ttl=-1) # Already expired
    val, stale = cache.get("short_ttl")
    assert val == "data"
    assert stale

def test_read_model_stale_while_revalidate_returns_stale_immediately():
    cache = ReadModelCache()
    cache.set("swr_key", "old_data", ttl=-1)

    revalidado = threading.Event()
    set_original = cache.set

    def set_observado(key, value, ttl=60):
        set_original(key, value, ttl)
        revalidado.set()

    cache.set = set_observado

    def fetcher():
        return "new_data"

    # Should return 'old_data' immediately because it's in cache (though stale)
    res = cache.get_or_revalidate("swr_key", fetcher, ttl=10)
    assert res == "old_data"

    # Espera a thread de revalidação gravar (polling com deadline, sem sleep fixo)
    assert _aguardar_condicao(lambda: cache.get("swr_key") == ("new_data", False)), (
        "revalidação em background não atualizou o cache a tempo"
    )
    val, stale = cache.get("swr_key")
    assert val == "new_data"
    assert not stale


# ---------------------------------------------------------------------------
# Item 4 (clock injection): TTL via relógio virtual — zero time.sleep
# ---------------------------------------------------------------------------

class RelogioVirtual:
    """Relógio fake determinístico: avança só quando o teste manda."""

    def __init__(self, agora=1000.0):
        self._agora = agora

    def __call__(self) -> float:
        return self._agora

    def avancar(self, segundos: float):
        self._agora += segundos


def test_read_model_cache_ttl_expira_via_relogio_injetado():
    """TTL respeitado usando relógio virtual: nada de dormir tempo real."""
    relogio = RelogioVirtual()
    cache = ReadModelCache(now_fn=relogio)

    cache.set("k", "v1", ttl=60)
    val, stale = cache.get("k")
    assert (val, stale) == ("v1", False)

    relogio.avancar(59)  # ainda dentro do TTL
    assert cache.get("k") == ("v1", False)

    relogio.avancar(2)  # 61s total — expirou
    val, stale = cache.get("k")
    assert val == "v1"
    assert stale


def test_read_model_cache_stale_while_revalidate_com_relogio_virtual():
    """Stale-While-Revalidate com relógio virtual: expiração instantânea
    sem manipular ttl negativo nem dormir."""
    relogio = RelogioVirtual()
    cache = ReadModelCache(now_fn=relogio)

    cache.set("swr", "old_data", ttl=60)
    relogio.avancar(120)  # cache ficou velho

    res = cache.get_or_revalidate("swr", lambda: "new_data", ttl=60)
    assert res == "old_data"  # retorna stale imediatamente

    # Revalidação roda em background; espera com deadline (sem sleep fixo)
    assert _aguardar_condicao(lambda: cache.get("swr") == ("new_data", False))
    assert cache.get("swr") == ("new_data", False)


def test_read_model_cache_agora_padrao_e_tempo_real():
    """Compatibilidade: sem now_fn explícito, comporta-se como antes."""
    cache = ReadModelCache()
    cache.set("k", "v", ttl=-1)  # já expirou
    _, stale = cache.get("k")
    assert stale is True


def test_crdt_add_is_idempotent():
    crdt = CRDTSet("node1")
    key1 = crdt.add({"id": 1, "name": "Item A"})
    key2 = crdt.add({"id": 1, "name": "Item A"})
    assert key1 == key2
    assert len(crdt.to_list()) == 1

def test_crdt_merge_union_no_conflicts():
    crdt1 = CRDTSet("node1")
    crdt2 = CRDTSet("node2")
    crdt1.add({"id": 1, "name": "Item A"})
    crdt2.add({"id": 2, "name": "Item B"})
    
    merged = crdt1.merge(crdt2)
    items = merged.to_list()
    assert len(items) == 2
    names = [i["name"] for i in items]
    assert "Item A" in names
    assert "Item B" in names

def test_crdt_pending_sync_returns_only_unsynced():
    crdt = CRDTSet("node1")
    k1 = crdt.add({"id": 1})
    k2 = crdt.add({"id": 2})
    
    pending = crdt.pending_sync([k1])
    assert len(pending) == 1
    assert pending[0]["id"] == 2

def test_circuit_breaker_opens_after_threshold():
    cb = CircuitBreaker("test_cb", failure_threshold=2, timeout=1)
    
    def fail_fn():
        raise ValueError("Error")
        
    with pytest.raises(ValueError):
        cb.call(fail_fn)
        
    with pytest.raises(ValueError):
        cb.call(fail_fn)
        
    # Threshold reached, should be open now
    assert cb.state == CircuitState.OPEN
    
    with pytest.raises(RuntimeError) as exc:
        cb.call(lambda: "Success")
    assert "OPEN" in str(exc.value)

def test_saga_compensates_on_failure():
    compensations = []
    
    step1 = SagaStep(
        name="step1",
        execute=lambda ctx: ctx.update({"s1": True}),
        compensate=lambda ctx: compensations.append("s1_undone")
    )
    
    def fail_execute(ctx):
        raise ValueError("Failed step2")
        
    step2 = SagaStep(
        name="step2",
        execute=fail_execute,
        compensate=lambda ctx: compensations.append("s2_undone")
    )
    
    orchestrator = SagaOrchestrator([step1, step2])
    
    with pytest.raises(RuntimeError) as exc:
        orchestrator.run({})
        
    assert "Saga 'step2' falhou" in str(exc.value)
    # Step 1 should be compensated because step 2 failed
    assert compensations == ["s1_undone"]
