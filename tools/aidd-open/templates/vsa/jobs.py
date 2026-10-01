# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.0-Beta — FILA DE PROCESSAMENTO ASSÍNCRONO PERSISTENTE (JobQueue + DLQ)
=============================================================================
Executa tarefas em background (envio de webhooks, geração de relatórios, etc.)
sem bloquear requisições HTTP do servidor principal. Retentativas exponenciais
(2**tentativa * 5s) e encaminhamento para Dead Letter Queue (DLQ) após esgotar
max_tentativas. Quando `db` é informado, o estado de cada job é persistido na
tabela `_jobs` para observabilidade e reprocessamento manual via painel `/jobs`.

Nota de escopo: a persistência cobre o ESTADO do job (status, tentativas, erro)
de forma durável entre reinícios do processo. A RE-EXECUÇÃO de uma função
Python arbitrária (closure/callable) só é possível enquanto o processo que a
enfileirou continuar vivo — não há serialização de código entre processos.
"""

import json
import queue
import threading
import time
import uuid
import datetime
from typing import Callable, Any, Dict, Optional


def _default_backoff(tentativa: int) -> float:
    """Backoff exponencial: 2**tentativa * 5s (5s, 10s, 20s, 40s, ...)."""
    return (2 ** tentativa) * 5.0


class JobQueue:
    def __init__(self, max_workers: int = 2, db=None, max_tentativas: int = 3, backoff_fn: Optional[Callable[[int], float]] = None):
        self.db = db
        self.max_tentativas = max_tentativas
        self.backoff_fn = backoff_fn or _default_backoff
        self._queue: queue.Queue = queue.Queue()
        self._workers = []
        self._running = True
        self._jobs_status: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

        if self.db:
            self._init_jobs_table()

        for i in range(max_workers):
            t = threading.Thread(target=self._worker_loop, name=f"AIDD-JobWorker-{i}", daemon=True)
            t.start()
            self._workers.append(t)

    def _init_jobs_table(self):
        with self.db.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS _jobs (
                    id TEXT PRIMARY KEY,
                    func_ref TEXT,
                    args_json TEXT,
                    status TEXT NOT NULL DEFAULT 'ENFILEIRADO',
                    tentativas INTEGER NOT NULL DEFAULT 0,
                    max_tentativas INTEGER NOT NULL DEFAULT 3,
                    proxima_execucao TEXT,
                    criado_em TEXT,
                    concluido_em TEXT,
                    resultado TEXT,
                    erro TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_jobs_status ON _jobs(status);
            """)
            conn.commit()

    def enqueue(self, func: Callable, *args, **kwargs) -> str:
        """Enfileira uma tarefa assíncrona e retorna o ID do Job."""
        job_id = str(uuid.uuid4())
        job_info = {
            "id": job_id,
            "status": "ENFILEIRADO",
            "criado_em": time.time(),
            "iniciado_em": None,
            "concluido_em": None,
            "resultado": None,
            "erro": None,
            "tentativas": 0,
            "max_tentativas": self.max_tentativas,
            "_func": func,
            "_args": args,
            "_kwargs": kwargs,
        }
        with self._lock:
            self._jobs_status[job_id] = job_info

        self._persist_job(job_id, func, args, kwargs)
        self._queue.put((job_id, func, args, kwargs, 0))
        return job_id

    def get_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retorna o status atual de uma tarefa (sem os internals _func/_args/_kwargs)."""
        with self._lock:
            info = self._jobs_status.get(job_id)
            if not info:
                return None
            return {k: v for k, v in info.items() if not k.startswith("_")}

    def list_jobs(self, limit: int = 50) -> list:
        """Lista jobs para o painel /jobs. Usa a tabela persistida quando disponível."""
        if self.db:
            with self.db.get_connection() as conn:
                rows = conn.execute(
                    "SELECT id, func_ref, status, tentativas, max_tentativas, "
                    "proxima_execucao, criado_em, concluido_em, erro FROM _jobs "
                    "ORDER BY criado_em DESC LIMIT ?",
                    (limit,)
                ).fetchall()
                return [dict(r) for r in rows]
        with self._lock:
            return [
                {k: v for k, v in info.items() if not k.startswith("_")}
                for info in list(self._jobs_status.values())[-limit:]
            ]

    def reprocessar(self, job_id: str) -> Dict[str, Any]:
        """Reencaminha manualmente um job (tipicamente em DLQ) para a fila,
        zerando o contador de tentativas. Requer que o processo original que
        enfileirou o job ainda esteja vivo (referência de função em memória)."""
        with self._lock:
            info = self._jobs_status.get(job_id)
            if not info:
                return {"sucesso": False, "erro": "Job não encontrado (referência em memória indisponível)"}
            func_ref = info.get("_func")
            args = info.get("_args", ())
            kwargs = info.get("_kwargs", {})
            info["status"] = "ENFILEIRADO"
            info["tentativas"] = 0
            info["erro"] = None

        self._mark_reenfileirado(job_id)
        self._queue.put((job_id, func_ref, args, kwargs, 0))
        return {"sucesso": True, "id": job_id}

    def _worker_loop(self):
        while self._running:
            try:
                job_id, func, args, kwargs, tentativa = self._queue.get(timeout=1.0)
            except queue.Empty:
                continue
            self._run_job(job_id, func, args, kwargs, tentativa)
            self._queue.task_done()

    def _run_job(self, job_id, func, args, kwargs, tentativa):
        with self._lock:
            if job_id in self._jobs_status:
                self._jobs_status[job_id]["status"] = "PROCESSANDO"
                self._jobs_status[job_id]["iniciado_em"] = time.time()
        self._mark_processando(job_id, tentativa)

        try:
            res = func(*args, **kwargs)
            with self._lock:
                if job_id in self._jobs_status:
                    self._jobs_status[job_id]["status"] = "CONCLUIDO"
                    self._jobs_status[job_id]["concluido_em"] = time.time()
                    self._jobs_status[job_id]["resultado"] = res
            self._mark_concluido(job_id, tentativa, res)
        except Exception as e:
            nova_tentativa = tentativa + 1
            if nova_tentativa >= self.max_tentativas:
                with self._lock:
                    if job_id in self._jobs_status:
                        self._jobs_status[job_id]["status"] = "DLQ"
                        self._jobs_status[job_id]["concluido_em"] = time.time()
                        self._jobs_status[job_id]["erro"] = str(e)
                        self._jobs_status[job_id]["tentativas"] = nova_tentativa
                self._mark_dlq(job_id, nova_tentativa, str(e))
            else:
                backoff = self.backoff_fn(nova_tentativa)
                with self._lock:
                    if job_id in self._jobs_status:
                        self._jobs_status[job_id]["status"] = "AGUARDANDO_RETRY"
                        self._jobs_status[job_id]["erro"] = str(e)
                        self._jobs_status[job_id]["tentativas"] = nova_tentativa
                self._mark_aguardando_retry(job_id, nova_tentativa, str(e), time.time() + backoff)
                timer = threading.Timer(backoff, lambda: self._queue.put((job_id, func, args, kwargs, nova_tentativa)))
                timer.daemon = True
                timer.start()

    def _persist_job(self, job_id, func, args, kwargs):
        if not self.db:
            return
        try:
            args_repr = json.dumps({
                "args": [repr(a) for a in args],
                "kwargs": {k: repr(v) for k, v in kwargs.items()}
            }, ensure_ascii=False)
        except Exception:
            args_repr = "{}"
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO _jobs (id, func_ref, args_json, status, tentativas, max_tentativas, criado_em)
                VALUES (?, ?, ?, 'ENFILEIRADO', 0, ?, ?)
                """,
                (
                    job_id,
                    getattr(func, "__qualname__", str(func)),
                    args_repr,
                    self.max_tentativas,
                    datetime.datetime.now(datetime.timezone.utc).isoformat()
                )
            )
            conn.commit()

    # As transições de estado abaixo usam SQL 100% estático (nunca f-string
    # interpolando a query), uma por cenário, em vez de montar o SET
    # dinamicamente — mais fácil de auditar e evita falsos-positivos em
    # varreduras estáticas de SQL injection.

    def _mark_processando(self, job_id, tentativas):
        if not self.db:
            return
        with self.db.get_connection() as conn:
            conn.execute(
                "UPDATE _jobs SET status = 'PROCESSANDO', tentativas = ? WHERE id = ?",
                (tentativas, job_id)
            )
            conn.commit()

    def _mark_concluido(self, job_id, tentativas, resultado):
        if not self.db:
            return
        try:
            resultado_json = json.dumps(resultado, ensure_ascii=False, default=str)
        except Exception:
            resultado_json = None
        with self.db.get_connection() as conn:
            conn.execute(
                """
                UPDATE _jobs SET status = 'CONCLUIDO', tentativas = ?, resultado = ?, concluido_em = ?
                WHERE id = ?
                """,
                (tentativas, resultado_json, datetime.datetime.now(datetime.timezone.utc).isoformat(), job_id)
            )
            conn.commit()

    def _mark_dlq(self, job_id, tentativas, erro):
        if not self.db:
            return
        with self.db.get_connection() as conn:
            conn.execute(
                """
                UPDATE _jobs SET status = 'DLQ', tentativas = ?, erro = ?, concluido_em = ?
                WHERE id = ?
                """,
                (tentativas, str(erro), datetime.datetime.now(datetime.timezone.utc).isoformat(), job_id)
            )
            conn.commit()

    def _mark_aguardando_retry(self, job_id, tentativas, erro, proxima_execucao_epoch):
        if not self.db:
            return
        iso = datetime.datetime.fromtimestamp(proxima_execucao_epoch, datetime.timezone.utc).isoformat()
        with self.db.get_connection() as conn:
            conn.execute(
                """
                UPDATE _jobs SET status = 'AGUARDANDO_RETRY', tentativas = ?, erro = ?, proxima_execucao = ?
                WHERE id = ?
                """,
                (tentativas, str(erro), iso, job_id)
            )
            conn.commit()

    def _mark_reenfileirado(self, job_id):
        if not self.db:
            return
        with self.db.get_connection() as conn:
            conn.execute(
                "UPDATE _jobs SET status = 'ENFILEIRADO', tentativas = 0, erro = NULL WHERE id = ?",
                (job_id,)
            )
            conn.commit()
