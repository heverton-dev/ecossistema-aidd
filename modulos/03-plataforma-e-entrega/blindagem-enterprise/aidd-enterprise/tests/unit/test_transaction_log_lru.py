# -*- coding: utf-8 -*-
"""
Testes do Transaction Log com Cache LRU (PLAN-0017, item transactionlog-lru-cache).

Cobre:
- LruCache: capacity configurável, invalidação de capacity inválida, ordem de
  evicção MRU/LRU, métricas de uso (hits/misses/hit_ratio), evicção
  (evictions/size), atualização sem evicção extra, thread-safety e publicação
  de contadores Prometheus no MetricsRegistry existente.
- TransactionLogRepositoryImpl: write-through apenas após commit, read-through
  cache-first, persistência entre instâncias/DB, rollback não vaza no cache,
  cadeia de hash encadeada (prev_hash -> curr_hash), detecção de adulteração e
  escrita concorrente íntegra.
"""

import json
import threading

from database import Database
from metrics import MetricsRegistry
from transaction_log import (
    TransactionLogEntry,
    TransactionLogRepositoryImpl,
    LruCache,
    _ZERO_HASH,
)


# --------------------------------------------------------------------------- #
# LruCache — unidade
# --------------------------------------------------------------------------- #

def test_lru_capacity_padrao_e_configuravel():
    assert LruCache().capacity == 128
    assert LruCache(capacity=3).capacity == 3
    assert LruCache(capacity=1).capacity == 1


def test_lru_rejeita_capacity_invalida():
    for invalida in (0, -1, -5):
        try:
            LruCache(capacity=invalida)
            assert False, f"capacity {invalida} deveria ter sido rejeitada"
        except ValueError:
            pass


def test_lru_evicta_menos_recentemente_usado():
    cache = LruCache(capacity=3)
    for chave in ("a", "b", "c"):
        cache.put(chave, chave.upper())
    cache.get("a")  # 'a' vira MRU (mais recente)
    cache.put("d", "D")  # estoura a capacity -> evicta 'b' (LRU)
    assert len(cache) == 3
    assert "b" not in cache
    assert all(chave in cache for chave in ("a", "c", "d"))
    metricas = cache.metrics()
    assert metricas["evictions"] == 1
    assert metricas["size"] == 3


def test_lru_put_existente_atualiza_sem_evictar_extra():
    cache = LruCache(capacity=2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("a", 100)  # atualiza + move para MRU, sem mudanca de tamanho
    cache.put("c", 3)  # estoura: evicta 'b' (LRU), 'a' permanece
    assert cache.get("a") == 100
    assert len(cache) == 2
    assert "b" not in cache
    assert cache.get("c") == 3


def test_lru_hit_miss_metrics_e_hit_ratio():
    cache = LruCache(capacity=2)
    cache.get("x")  # miss
    cache.get("y")  # miss
    cache.put("z", 1)
    assert cache.get("z") == 1  # hit
    metricas = cache.metrics()
    assert metricas["hits"] == 1
    assert metricas["misses"] == 2
    assert metricas["hit_ratio"] == 1 / 3
    assert metricas["capacity"] == 2
    assert metricas["size"] == 1
    assert metricas["evictions"] == 0


def test_lru_thread_safety():
    cache = LruCache(capacity=8)
    faixas = [(f"chat-{group}", list(range(group, group + 30))) for group in range(4)]
    erros = []

    def operar(nome, chaves):
        try:
            for valor in chaves:
                cache.put(f"{nome}:{valor}", valor)
                cache.get(f"{nome}:{valor}")
        except Exception as exc:  # pragma: no cover
            erros.append(exc)

    threads = [threading.Thread(target=operar, args=(nome, chaves)) for nome, chaves in faixas]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert not erros
    assert len(cache) == 8
    assert cache.metrics()["hits"] > 0
    assert cache.metrics()["misses"] >= 0


def test_lru_publica_contadores_prometheus_no_registry():
    registry = MetricsRegistry()
    cache = LruCache(capacity=1, registry=registry)
    cache.put("a", 1)
    cache.put("b", 2)  # estoura: evicta 'a'
    cache.get("a")  # miss (já evictada)
    cache.get("b")  # hit
    texto = registry.render()
    assert "transaction_log_lru_hits_total 1" in texto
    assert "transaction_log_lru_misses_total 1" in texto
    assert "transaction_log_lru_evictions_total 1" in texto


# --------------------------------------------------------------------------- #
# TransactionLogRepositoryImpl — integração
# --------------------------------------------------------------------------- #

def _repo(db, capacity=128):
    return TransactionLogRepositoryImpl(db, cache_capacity=capacity)


def test_registrar_log_persiste_e_faz_write_through(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'tl1.db'}")
    repo = _repo(db)
    primeiro = repo.registrar_log("pedido.criado", {"id": 1})
    segundo = repo.registrar_log("pedido.pago", {"id": 1})
    assert repo.count() == 2
    # Write-through: entradas commitadas já estão no cache (hit sem tocar o banco)
    assert repo.get(primeiro.id).action == "pedido.criado"
    assert repo.cache_metrics()["hits"] >= 1
    # list_recent autoriza a ordenação pela persistência
    recentes = repo.list_recent(limit=10)
    assert [entrada.action for entrada in recentes] == ["pedido.pago", "pedido.criado"]
    assert len(recentes) == 2


def test_persistencia_entre_instancias_do_repositorio(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'tl2.db'}")
    repo1 = _repo(db)
    registrado = repo1.registrar_log("contrato.assinado", {"n": 1})
    # Nova instância com cache frio: leitura cai no banco (read-through)
    repo2 = TransactionLogRepositoryImpl(db, cache_capacity=5)
    recuperado = repo2.get(registrado.id)
    assert recuperado is not None
    assert recuperado.action == "contrato.assinado"
    assert recuperado.payload == {"n": 1}
    assert repo2.count() == 1
    assert repo2.cache_metrics()["misses"] == 1
    # Segundo acesso agora é hit (versão fria foi cacheada)
    assert repo2.get(registrado.id).id == registrado.id
    assert repo2.cache_metrics()["hits"] == 1


def test_rollback_nao_vaza_registro_no_cache(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'tl3.db'}")
    repo = _repo(db)
    with db.get_connection() as conn:
        pendente = repo.append(conn, "transacao.cancelada", {"x": 1})
        conn.rollback()  # simula falha antes do commit
    # append é nível baixo (sem commit do chamado): nada pode estar no cache
    assert repo.get(pendente.id) is None
    assert repo.count() == 0
    assert repo.cache_metrics()["misses"] == 1


def test_registrar_log_rejeita_mas_manter_consistente(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'tl3b.db'}")
    repo = _repo(db)
    entradas = [repo.registrar_log("op", {"i": i}) for i in range(3)]
    assert all(entrada.validar_integridade() for entrada in entradas)
    assert len({entrada.id for entrada in entradas}) == 3


def test_cadeia_hash_encadeada_detecta_adulteracao(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'tl4.db'}")
    repo = _repo(db)
    primeiro = repo.registrar_log("log.criado", {"ok": 1})
    segundo = repo.registrar_log("log.atualizado", {"ok": 2})
    terceiro = repo.registrar_log("log.finalizado", {"ok": 3})
    assert primeiro.prev_hash == _ZERO_HASH
    assert segundo.prev_hash == primeiro.curr_hash
    assert terceiro.prev_hash == segundo.curr_hash
    for entrada in (primeiro, segundo, terceiro):
        assert entrada.validar_integridade()
    # Adultera a linha direto no SQLite (à revelia do cache)
    with db.get_connection() as conn:
        conn.execute(
            "UPDATE _transaction_log SET payload = ? WHERE id = ?",
            (json.dumps({"ok": 999}), terceiro.id),
        )
        conn.commit()
    # Instância com cache frio relê do banco e detecta o desvio pela cadeia
    repo2 = TransactionLogRepositoryImpl(db, cache_capacity=5)
    corrompida = repo2.get(terceiro.id)
    assert corrompida is not None
    assert not corrompida.validar_integridade()


def test_eviccao_e_metricas_de_uso_com_capacity_baixa(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'tl5.db'}")
    repo = TransactionLogRepositoryImpl(db, cache_capacity=2)
    entradas = [repo.registrar_log("operacao", {"i": idx}) for idx in range(6)]
    # As 4 entradas mais antigas já foram evictadas na própria escrita
    metricas = repo.cache_metrics()
    assert metricas["capacity"] == 2
    assert metricas["size"] == 2
    assert metricas["evictions"] >= 4
    # As 2 mais recentes seguem no cache: hits sem tocar o banco
    assert repo.get(entradas[4].id).action == "operacao"
    assert repo.get(entradas[5].id).action == "operacao"
    # Entrada antiga evictada: read-through ao banco (miss) sem erro
    assert repo.get(entradas[0].id) is not None
    metricas = repo.cache_metrics()
    assert metricas["hits"] >= 2
    assert metricas["misses"] >= 1
    assert metricas["evictions"] >= 5


def test_get_de_id_inexistente_eh_miss_sem_erro(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'tl5b.db'}")
    repo = _repo(db)
    assert repo.get("id-que-nao-existe") is None
    assert repo.cache_metrics()["misses"] == 1


def test_list_recent_respeita_limit_e_rejeita_invalido(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'tl7.db'}")
    repo = _repo(db)
    for idx in range(5):
        repo.registrar_log("lote", {"n": idx})
    assert len(repo.list_recent(limit=2)) == 2
    assert len(repo.list_recent(limit=500)) == 5
    try:
        repo.list_recent(limit=0)
        assert False, "limit 0 deveria ter sido rejeitado"
    except ValueError:
        pass


def test_escrita_concorrente_persiste_tudo_e_manter_integridade(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'tl6.db'}")
    repo = TransactionLogRepositoryImpl(db, cache_capacity=64)
    erros = []

    def gravar(worker):
        try:
            for idx in range(10):
                repo.registrar_log(f"operacao_{worker}", {"w": worker, "i": idx})
        except Exception as exc:  # pragma: no cover
            erros.append(exc)

    threads = [threading.Thread(target=gravar, args=(worker,)) for worker in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not erros
    assert repo.count() == 50
    todos = repo.list_recent(limit=100)
    assert len(todos) == 50
    ids = [entrada.id for entrada in todos]
    assert len(set(ids)) == 50  # sem duplicidade de chaves primárias
    for entrada in todos:
        assert entrada.validar_integridade()


def test_list_recent_aquece_cache_para_leituras_subsequentes(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'tl8.db'}")
    repo = _repo(db)
    primeira = repo.registrar_log("primeiro", {"v": 1})
    repo.registrar_log("segundo", {"v": 2})
    repo2 = TransactionLogRepositoryImpl(db, cache_capacity=8)
    repo2.list_recent(limit=10)  # aquece o cache frio
    metricas = repo2.cache_metrics()
    assert metricas["size"] == 2
    assert repo2.get(primeira.id).id == primeira.id
    assert repo2.cache_metrics()["hits"] >= 1