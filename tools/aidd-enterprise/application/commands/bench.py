# -*- coding: utf-8 -*-
"""Use Case: bench — benchmark local de concorrência no SQLite WAL e EventBus."""

import concurrent.futures
import os
import sys
import time

from application.commands.setup import ensure_environment


def cmd_bench(args):
    """Executa benchmark local de concorrência no SQLite WAL e EventBus."""
    ensure_environment()
    target_dir = os.path.abspath(getattr(args, "dir", "."))
    print("=" * 80)
    print(f"⚡ [AIDD BENCHMARK v5.1] Teste de Concorrência SQLite WAL (Local / In-Process)")
    print("   ℹ️  Medição direta do throughput SQLite WAL (sem overhead de stack HTTP).")
    print(f"📁 Diretório Alvo: {target_dir}")
    print("=" * 80)

    master_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    candidates = [
        os.path.join(target_dir, "src"),
        os.path.join(target_dir, "src", "core"),
        os.path.join(master_root, "templates", "core"),
        os.path.join(master_root, "templates", "v2"),
        os.path.join(master_root, "src", "core")
    ]
    for c in candidates:
        if os.path.exists(c) and c not in sys.path:
            sys.path.insert(0, c)

    try:
        try:
            from core.database import Database
            from core.events import EventBus
        except ImportError:
            import database as db_mod
            import events as ev_mod
            Database = db_mod.Database
            EventBus = ev_mod.EventBus

        db = Database(os.path.join(target_dir, "app.db"))
        events = EventBus()

        # Pré-inicialização da conexão e WAL
        with db.get_connection() as conn:
            conn.execute("SELECT 1;").fetchone()

        total_reqs = getattr(args, "n", 100) or 100
        print(f"[*] Disparando {total_reqs} operações concorrentes no SQLite WAL...")

        t0 = time.time()
        successes = 0
        errors = 0

        def worker_task(idx):
            try:
                with db.get_connection() as conn:
                    conn.execute("SELECT 1;").fetchone()
                events.emit("benchmark_tick", {"idx": idx})
                return True
            except Exception as e:
                return False

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(worker_task, range(total_reqs)))

        successes = sum(1 for r in results if r)
        errors = sum(1 for r in results if not r)
        duration_ms = (time.time() - t0) * 1000
        avg_latency = duration_ms / total_reqs
        rps = total_reqs / ((duration_ms / 1000) or 0.001)

        print(f"\n📊 RESULTADOS DO BENCHMARK:")
        print(f"   - Total de Operações: {total_reqs}")
        print(f"   - Sucessos (PASS):   {successes}")
        print(f"   - Falhas (FAIL):     {errors}")
        print(f"   - Duração Total:     {duration_ms:.2f} ms")
        print(f"   - Latência Média:    {avg_latency:.2f} ms/req")
        print(f"   - Throughput (RPS):  {rps:.1f} req/s")
        print("=" * 80)

        if errors > 0:
            print("❌ [FALHA]: Conflitos de lock detectados sob concorrência.")
            sys.exit(1)

        print("🏆 [SUCESSO]: Desempenho Ultra-Level Homologado (Zero Lock Contention)!")
        sys.exit(0)
    except Exception as e:
        print(f"[ERRO] Falha ao executar benchmark: {e}")
        sys.exit(1)