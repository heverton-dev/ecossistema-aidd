# -*- coding: utf-8 -*-
"""
Testes do JobQueue persistente (Onda 2 / v5.0-Beta): valida o critério de
aceite "tarefa com erro simulado tenta 3 vezes com intervalo crescente antes
de ir para status DLQ", persistência de estado em `_jobs` e reprocessamento
manual. Usa um `backoff_fn` injetado (delay mínimo) para não depender de
tempo real de espera exponencial nos testes.
"""

import os
import sys
import time

TEMPLATES_V2 = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "templates", "v2"))
if TEMPLATES_V2 not in sys.path:
    sys.path.insert(0, TEMPLATES_V2)

from database import Database  # noqa: E402
from jobs import JobQueue, _default_backoff  # noqa: E402


def _aguardar(condicao, timeout=5.0, intervalo=0.02):
    prazo = time.time() + timeout
    while time.time() < prazo:
        if condicao():
            return True
        time.sleep(intervalo)
    return False


def test_default_backoff_is_exponential_base5s():
    assert _default_backoff(1) == 10.0   # 2**1 * 5
    assert _default_backoff(2) == 20.0   # 2**2 * 5
    assert _default_backoff(3) == 40.0   # 2**3 * 5


def test_job_succeeds_on_first_attempt_without_db():
    jq = JobQueue(max_workers=1, backoff_fn=lambda t: 0.01)
    job_id = jq.enqueue(lambda: 42)

    assert _aguardar(lambda: jq.get_status(job_id)["status"] == "CONCLUIDO")
    status = jq.get_status(job_id)
    assert status["resultado"] == 42
    assert status["tentativas"] == 0


def test_job_retries_exactly_max_tentativas_then_goes_to_dlq():
    tentativas_executadas = []

    def tarefa_sempre_falha():
        tentativas_executadas.append(time.time())
        raise RuntimeError("falha simulada")

    jq = JobQueue(max_workers=1, max_tentativas=3, backoff_fn=lambda t: 0.02)
    job_id = jq.enqueue(tarefa_sempre_falha)

    assert _aguardar(lambda: jq.get_status(job_id)["status"] == "DLQ", timeout=5.0)

    status = jq.get_status(job_id)
    assert status["status"] == "DLQ"
    assert status["tentativas"] == 3
    assert "falha simulada" in status["erro"]
    assert len(tentativas_executadas) == 3


def test_job_succeeds_after_transient_failures_before_exhausting_retries():
    tentativas = {"n": 0}

    def tarefa_falha_duas_vezes():
        tentativas["n"] += 1
        if tentativas["n"] < 3:
            raise RuntimeError(f"falha transitoria {tentativas['n']}")
        return "sucesso-na-terceira"

    jq = JobQueue(max_workers=1, max_tentativas=5, backoff_fn=lambda t: 0.02)
    job_id = jq.enqueue(tarefa_falha_duas_vezes)

    assert _aguardar(lambda: jq.get_status(job_id)["status"] == "CONCLUIDO", timeout=5.0)
    status = jq.get_status(job_id)
    assert status["resultado"] == "sucesso-na-terceira"
    assert status["tentativas"] == 2  # 2 falhas registradas antes do sucesso


def test_jobs_persist_state_across_a_new_jobqueue_instance(tmp_path):
    """A persistência do ESTADO sobrevive a reinício do processo mesmo que a
    função original (closure) não possa ser re-serializada — validando o
    limite de escopo documentado no módulo jobs.py."""
    db = Database(f"sqlite:///{tmp_path / 'jobs.db'}")

    jq1 = JobQueue(max_workers=1, db=db, backoff_fn=lambda t: 0.01)
    job_id = jq1.enqueue(lambda: "ok")
    assert _aguardar(lambda: jq1.get_status(job_id)["status"] == "CONCLUIDO")

    # Simula um novo processo lendo o estado persistido (mesmo db, nova instância)
    jq2 = JobQueue(max_workers=1, db=db, backoff_fn=lambda t: 0.01)
    jobs_persistidos = jq2.list_jobs()

    assert any(j["id"] == job_id and j["status"] == "CONCLUIDO" for j in jobs_persistidos)


def test_jobs_dlq_is_persisted_and_visible_in_list_jobs(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'jobs_dlq.db'}")
    jq = JobQueue(max_workers=1, db=db, max_tentativas=2, backoff_fn=lambda t: 0.01)

    def sempre_falha():
        raise ValueError("erro definitivo")

    job_id = jq.enqueue(sempre_falha)
    assert _aguardar(lambda: jq.get_status(job_id)["status"] == "DLQ", timeout=5.0)

    def _persistido_em_dlq():
        jobs = jq.list_jobs()
        job = next((j for j in jobs if j["id"] == job_id), None)
        return job is not None and job["status"] == "DLQ"

    # A escrita em memória e a escrita persistida no _jobs não são atômicas
    # entre si (ocorrem em sequência na mesma thread do worker); aguarda a
    # propagação para a tabela antes de inspecionar o estado persistido.
    assert _aguardar(_persistido_em_dlq, timeout=5.0)

    job_persistido = next(j for j in jq.list_jobs() if j["id"] == job_id)
    assert job_persistido["status"] == "DLQ"
    assert job_persistido["tentativas"] == 2
    assert "erro definitivo" in job_persistido["erro"]


def test_reprocessar_resets_attempts_and_requeues_job():
    execucoes = {"n": 0}

    def falha_uma_vez_depois_ok():
        execucoes["n"] += 1
        if execucoes["n"] == 1:
            raise RuntimeError("primeira falha")
        return "ok-apos-reprocessar"

    jq = JobQueue(max_workers=1, max_tentativas=1, backoff_fn=lambda t: 0.01)
    job_id = jq.enqueue(falha_uma_vez_depois_ok)

    assert _aguardar(lambda: jq.get_status(job_id)["status"] == "DLQ", timeout=5.0)

    resultado_reprocessar = jq.reprocessar(job_id)
    assert resultado_reprocessar["sucesso"] is True

    assert _aguardar(lambda: jq.get_status(job_id)["status"] == "CONCLUIDO", timeout=5.0)
    status = jq.get_status(job_id)
    assert status["resultado"] == "ok-apos-reprocessar"
    assert status["tentativas"] == 0
