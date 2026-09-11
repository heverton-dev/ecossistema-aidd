# -*- coding: utf-8 -*-
"""
Higiene e Manutenção Preventiva Multi-Harness
Monitora e previne estouro de memória/disco em:
- OpenCode (SQLite)
- MiMoCode (SQLite)
- Claude Code (Cache/Logs)
- Cursor (Cache)
- Antigravity (Brain/Logs)
"""

import os
import sys
import shutil
import sqlite3
import subprocess
from datetime import datetime

MAX_DB_MB_THRESHOLD = 500  # Aciona limpeza se banco ultrapassar 500 MB
KEEP_RECENT_SESSIONS = 30   # Quantidade de sessões recentes a preservar


def is_process_running(proc_name):
    """Verifica se há processo ativo com o nome fornecido no Windows."""
    try:
        out = subprocess.check_output(
            ["tasklist", "/FI", f"IMAGENAME eq {proc_name}.exe", "/NH"],
            stderr=subprocess.DEVNULL,
            text=True
        )
        return proc_name.lower() in out.lower()
    except Exception:
        return False


def get_dir_size_mb(path):
    """Calcula tamanho total de um diretório em MB."""
    if not os.path.exists(path):
        return 0.0
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            fp = os.path.join(root, f)
            try:
                total += os.path.getsize(fp)
            except OSError:
                pass
    return total / (1024 * 1024)


def get_file_size_mb(path):
    """Calcula tamanho de um arquivo em MB."""
    if not os.path.isfile(path):
        return 0.0
    try:
        return os.path.getsize(path) / (1024 * 1024)
    except OSError:
        return 0.0


def prune_sqlite_database(db_path, app_name, proc_name, keep_sessions=KEEP_RECENT_SESSIONS):
    """
    Higieniza banco SQLite (OpenCode/MiMoCode) preservando as últimas sessões
    e realizando VACUUM com backup obrigatório.
    """
    if not os.path.exists(db_path):
        return True, f"{app_name}: Banco de dados não encontrado."

    size_mb = get_file_size_mb(db_path)
    if size_mb < MAX_DB_MB_THRESHOLD:
        return True, f"{app_name}: Tamanho saudável ({size_mb:.1f} MB < {MAX_DB_MB_THRESHOLD} MB)."

    # Trava 1: Checar se o processo está em execução
    if is_process_running(proc_name):
        return False, f"{app_name}: Processo '{proc_name}' ativo no momento. Limpeza postergada por segurança."

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.bak_{timestamp}"

    # Trava 2: Backup prévio obrigatório
    try:
        shutil.copy2(db_path, backup_path)
    except Exception as e:
        return False, f"{app_name}: Falha ao criar backup: {e}"

    # Se o banco for gigantesco (> 3 GB), rotaciona o arquivo antigo e inicia limpo
    if size_mb > 3000:
        try:
            wal_path = f"{db_path}-wal"
            shm_path = f"{db_path}-shm"
            if os.path.exists(wal_path):
                shutil.move(wal_path, f"{wal_path}.bak_{timestamp}")
            if os.path.exists(shm_path):
                shutil.move(shm_path, f"{shm_path}.bak_{timestamp}")
            shutil.move(db_path, f"{db_path}.archive_{timestamp}")
            return True, f"{app_name}: Banco crítico ({size_mb:.1f} MB) rotacionado para '{os.path.basename(db_path)}.archive_{timestamp}'. Novo banco limpo será recriado no próximo boot."
        except Exception as e:
            return False, f"{app_name}: Erro ao rotacionar banco crítico: {e}"

    # Para bancos moderados (> 500 MB e < 3 GB): poda de sessões antigas + VACUUM
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='session';")
        has_session = cur.fetchone() is not None

        if has_session:
            cur.execute(f"SELECT id FROM session ORDER BY rowid DESC LIMIT {keep_sessions}")
            recent_ids = [r[0] for r in cur.fetchall()]

            if recent_ids:
                placeholders = ",".join(["?"] * len(recent_ids))
                cur.execute(f"DELETE FROM part WHERE message_id IN (SELECT id FROM message WHERE session_id NOT IN ({placeholders}))", recent_ids)
                cur.execute(f"DELETE FROM message WHERE session_id NOT IN ({placeholders})", recent_ids)
                cur.execute(f"DELETE FROM session WHERE id NOT IN ({placeholders})", recent_ids)
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='event';")
                if cur.fetchone():
                    cur.execute("DELETE FROM event WHERE rowid NOT IN (SELECT rowid FROM event ORDER BY rowid DESC LIMIT 5000)")
                conn.commit()

        cur.execute("VACUUM;")
        conn.close()

        new_size = get_file_size_mb(db_path)
        return True, f"{app_name}: Compactado com sucesso ({size_mb:.1f} MB -> {new_size:.1f} MB). Preservadas {keep_sessions} sessões."
    except Exception as e:
        return False, f"{app_name}: Erro durante compactação: {e}"


def clean_dir_logs_and_cache(dir_path, app_name, max_mb=1000, target_subdirs=None):
    """Higieniza pastas de cache e logs se excederem o limite."""
    if not os.path.exists(dir_path):
        return True, f"{app_name}: Pasta não encontrada."

    size_mb = get_dir_size_mb(dir_path)
    if size_mb < max_mb:
        return True, f"{app_name}: Tamanho saudável ({size_mb:.1f} MB < {max_mb} MB)."

    targets = target_subdirs or ["cache", "logs", "tmp", "temp"]

    for sub in targets:
        target_path = os.path.join(dir_path, sub)
        if os.path.exists(target_path):
            try:
                shutil.rmtree(target_path)
                os.makedirs(target_path, exist_ok=True)
            except Exception:
                pass

    new_size = get_dir_size_mb(dir_path)
    return True, f"{app_name}: Cache limpo ({size_mb:.1f} MB -> {new_size:.1f} MB)."


def audit_all():
    """Gera diagnóstico de armazenamento de todos os harnesses."""
    home = os.path.expanduser("~")
    report = []

    opencode_db = os.path.join(home, ".local", "share", "opencode", "opencode.db")
    report.append(("OpenCode DB", opencode_db, get_file_size_mb(opencode_db), MAX_DB_MB_THRESHOLD))

    mimo_db = os.path.join(home, ".local", "share", "mimocode", "mimocode.db")
    report.append(("MiMoCode DB", mimo_db, get_file_size_mb(mimo_db), MAX_DB_MB_THRESHOLD))

    claude_dir = os.path.join(home, ".claude")
    report.append(("Claude Code", claude_dir, get_dir_size_mb(claude_dir), 1000))

    cursor_dir = os.path.join(home, ".cursor")
    report.append(("Cursor", cursor_dir, get_dir_size_mb(cursor_dir), 1000))

    agy_brain = os.path.join(home, ".gemini", "antigravity-cli", "brain")
    report.append(("Antigravity Brain", agy_brain, get_dir_size_mb(agy_brain), 800))

    return report


def relatar_sem_alterar(quiet=False):
    """Modo SOMENTE LEITURA: mede e avisa, nunca apaga, move ou arquiva nada.

    E o unico modo que o pre-commit pode chamar. A faxina de verdade
    (`clean`) apaga sessoes antigas e chega a arquivar bancos inteiros —
    fazer isso automatico a cada commit ja custou historico de harness e
    quebrou o religamento de sessao do ORCA (`--resume <id>` apontando pra
    sessao que a faxina levou).
    """
    alertas = []
    for nome, caminho, tamanho, limite in audit_all():
        if tamanho > limite:
            alertas.append(
                f"{nome}: {tamanho:.1f} MB (limite {limite} MB) - "
                f"rode 'python scripts/harness_hygiene.py clean' quando o harness estiver fechado."
            )
    if alertas and not quiet:
        print("[higiene] Atencao (nada foi apagado):")
        for a in alertas:
            print(f"[higiene]   - {a}")
    elif alertas:
        for a in alertas:
            print(f"[higiene] {a}")
    return alertas


def run_hygiene(quiet=False):
    """DESTRUTIVO e MANUAL: apaga sessoes antigas, limpa caches e pode arquivar
    bancos inteiros. Nunca deve ser chamado por hook automatico — so por
    `python scripts/harness_hygiene.py clean`, com o harness fechado."""
    home = os.path.expanduser("~")
    results = []

    opencode_db = os.path.join(home, ".local", "share", "opencode", "opencode.db")
    ok, msg = prune_sqlite_database(opencode_db, "OpenCode", "opencode")
    results.append((ok, msg))

    mimo_db = os.path.join(home, ".local", "share", "mimocode", "mimocode.db")
    ok, msg = prune_sqlite_database(mimo_db, "MiMoCode", "mimo")
    results.append((ok, msg))

    claude_dir = os.path.join(home, ".claude")
    ok, msg = clean_dir_logs_and_cache(claude_dir, "Claude Code", max_mb=1000, target_subdirs=["cache", "telemetry"])
    results.append((ok, msg))

    cursor_dir = os.path.join(home, ".cursor")
    ok, msg = clean_dir_logs_and_cache(cursor_dir, "Cursor", max_mb=1000, target_subdirs=["cache", "logs"])
    results.append((ok, msg))

    if not quiet:
        print("\n--- Relatório de Higiene de Harnesses ---")
        for ok, msg in results:
            prefix = "[OK]" if ok else "[ALERTA]"
            print(f"{prefix} {msg}")

    return all(r[0] for r in results)


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    if action == "status":
        print("\n=== STATUS DE ARMAZENAMENTO DOS HARNESSES ===")
        print(f"{'Harness':<20} {'Tamanho':<15} {'Limite':<15} {'Status'}")
        print("-" * 65)
        for name, path, size, limit in audit_all():
            status = "CRITICO" if size > limit * 2 else ("ALTO" if size > limit else "NORMAL")
            print(f"{name:<20} {size:>8.2f} MB   {limit:>8} MB   {status}")
    elif action in ("check", "check-silent"):
        # Somente leitura. Nunca apaga nada. Exit 0 sempre: e aviso, nao gate.
        relatar_sem_alterar(quiet=(action == "check-silent"))
    elif action == "clean":
        run_hygiene(quiet=False)
    else:
        print("Uso: python harness_hygiene.py [status|check|check-silent|clean]")
        print("  status       - tabela de tamanhos (nao altera nada)")
        print("  check        - avisa o que passou do limite (nao altera nada)")
        print("  check-silent - igual ao check, so imprime se houver alerta")
        print("  clean        - DESTRUTIVO: faxina de verdade, manual, harness fechado")
