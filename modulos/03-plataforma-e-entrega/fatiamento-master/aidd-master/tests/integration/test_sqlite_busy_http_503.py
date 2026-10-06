# -*- coding: utf-8 -*-
"""
Teste de integração REAL (sem mocks, sem stubs) do mapeamento SQLITE_BUSY
na fronteira HTTP (PLAN-0017, item retry-backoff-sqlite).

Prova, com suíte composta de verdade + servidor real em subprocess + lock
externo real via sqlite3 cru:

  A) Rotina que retorna `Result.fail(codigo='DB_LOCKED')` é serializada como
     HTTP 503 + header `Retry-After` + body {sucesso:false, codigo:DB_LOCKED};
  B) Rotina que ESCREVE no SQLite enquanto outra conexão real segura um write
     lock (BEGIN IMMEDIATE) dispara retry automatico, esgota as tentativas e
     responde HTTP 503 (não crash e nem 500); após liberar o lock, a mesma
     rotina responde 200 com escrita persistida;
  C) Rota não relacionada (/api/crm) continua respondendo 200.

Para manter o teste rápido, a constante `SQLITE_BUSY_PRAGMA_TIMEOUT_MS` da
suíte gerada é reduzida de 5000ms para 50ms (apenas configuração de teste —
o mecanismo de retry/503 em si não é alterado).
"""

import json
import os
import sqlite3
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

import pytest

SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

BUSY_TIMEOUT_FAST_MS = 50
LIMITE_ESPERA_BOOT_S = 20
ROTA_LOCKTEST_RESULT = "/api/locktest-result"
ROTA_LOCKTEST_WRITE = "/api/locktest-write"


def _http(method, url, body=None, timeout=10):
    """Requisicao HTTP real; retorna (status, headers, json|None). HTTPError
    nao e silenciado — o status/propagacao e justamente o que se mede."""
    dados = None
    if body is not None:
        dados = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=dados, method=method)
    if dados is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            corpo = resp.read()
            return resp.status, resp.headers, (json.loads(corpo) if corpo else None)
    except urllib.error.HTTPError as e:
        corpo = e.read()
        return e.code, e.headers, (json.loads(corpo) if corpo else None)


def _aguardar_servidor(processo, url, deadline_segundos=LIMITE_ESPERA_BOOT_S):
    deadline = time.time() + deadline_segundos
    ultimo_erro = None
    while time.time() < deadline:
        if processo.poll() is not None:
            saida = processo.stdout.read() if processo.stdout else ""
            pytest.fail(
                f"Servidor encerrou sozinho antes de responder em {url} "
                f"(exit {processo.returncode}):\n{saida}"
            )
        try:
            status, _, _ = _http("GET", url, timeout=1)
            return status
        except (urllib.error.URLError, OSError) as e:
            ultimo_erro = e
            time.sleep(0.05)
    pytest.fail(f"Servidor não respondeu em {url}: {ultimo_erro}")


def _porta_livre():
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _caminho_db_da_suite(target):
    server_src = (target / "src" / "server.py").read_text(encoding="utf-8")
    for linha in server_src.splitlines():
        if linha.strip().startswith("DB_PATH"):
            expressao = linha.split("=", 1)[1].strip()
            if expressao.startswith(("'", '"')):
                return expressao.strip("'\"")
            ns = {"os": os, "CURRENT_DIR": str(target / "src")}
            return os.path.abspath(eval(expressao, ns))
    pytest.fail("Nao encontrei DB_PATH em src/server.py da suite gerada")


@pytest.fixture
def suite_com_rotas_locktest(tmp_path):
    from compose_suite import compose_suite

    target = tmp_path / "suite-busy"
    compose_suite(str(target), "Suite Busy Lock", ["crm"], db_engine="sqlite")

    db_core = target / "src" / "core" / "database.py"
    origem = db_core.read_text(encoding="utf-8")
    assert "SQLITE_BUSY_PRAGMA_TIMEOUT_MS" in origem, (
        "Suite composta nao contem o knob SQLITE_BUSY_PRAGMA_TIMEOUT_MS "
        "(core/database.py fora de sync?)."
    )
    assert "def _run_com_retry" in origem, (
        "Suite composta nao contem o retry SQLITE_BUSY (core/database.py fora de sync?)."
    )
    db_core.write_text(
        origem.replace(
            "SQLITE_BUSY_PRAGMA_TIMEOUT_MS = 5000",
            f"SQLITE_BUSY_PRAGMA_TIMEOUT_MS = {BUSY_TIMEOUT_FAST_MS}",
        ),
        encoding="utf-8",
    )

    server_src = (target / "src" / "server.py").read_text(encoding="utf-8")
    marcador = 'if __name__ == "__main__":'
    assert marcador in server_src, "Marcador de entrada do server.py ausente."
    rotas_extra = (
        "\n\n"
        "@registry.route(\"GET\", \"" + ROTA_LOCKTEST_RESULT + "\")\n"
        "def _rota_locktest_result(_query):\n"
        "    return Result.fail(\n"
        '        "Banco de dados temporariamente bloqueado por outra conexão.",\n'
        '        codigo="DB_LOCKED",\n'
        '        detalhes={"retry_after_segundos": RETRY_AFTER_DB_LOCKED_S},\n'
        "    )\n"
        "\n\n"
        "@registry.route(\"POST\", \"" + ROTA_LOCKTEST_WRITE + "\")\n"
        "def _rota_locktest_write(data):\n"
        "    with db.get_connection() as conn:\n"
        "        conn.execute(\n"
        '            "INSERT INTO _locktest (v) VALUES (?)",\n'
        '            (str(data.get("v", "x"))[:64],),\n'
        "        )\n"
        "    return {\"sucesso\": True, \"v\": data.get(\"v\", \"x\")}\n"
        "\n\n"
    )
    server_src = server_src.replace(marcador, rotas_extra + marcador, 1)
    (target / "src" / "server.py").write_text(server_src, encoding="utf-8")
    return target


@pytest.fixture
def servidor_rodando(suite_com_rotas_locktest):
    target = suite_com_rotas_locktest
    porta = _porta_livre()
    env = os.environ.copy()
    env["PORT"] = str(porta)
    processo = subprocess.Popen(
        [sys.executable, "src/server.py"],
        cwd=str(target),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )
    base = f"http://127.0.0.1:{porta}"
    try:
        assert _aguardar_servidor(processo, f"{base}/api/crm") == 200
    except BaseException:
        processo.terminate()
        raise
    yield target, base, processo
    processo.terminate()
    try:
        processo.wait(timeout=5)
    except subprocess.TimeoutExpired:
        processo.kill()


def test_result_db_locked_vira_503_retry_after(servidor_rodando):
    _, base, processo = servidor_rodando
    assert processo.poll() is None
    status, headers, body = _http("GET", f"{base}{ROTA_LOCKTEST_RESULT}")
    assert status == 503, f"Esperava 503, veio {status}"
    assert headers.get("Retry-After") == "2", headers.get("Retry-After")
    assert body["sucesso"] is False
    assert body["codigo"] == "DB_LOCKED"
    assert body["detalhes"]["retry_after_segundos"] == 2


def test_escrita_sob_lock_real_vira_503_e_apos_liberar_vira_200(servidor_rodando):
    target, base, processo = servidor_rodando
    assert processo.poll() is None
    db_path = _caminho_db_da_suite(target)

    ext = sqlite3.connect(db_path, check_same_thread=False)
    try:
        ext.execute("PRAGMA busy_timeout=50")
        ext.execute("CREATE TABLE IF NOT EXISTS _locktest (id INTEGER PRIMARY KEY, v TEXT)")
        ext.execute("BEGIN IMMEDIATE")
        ext.execute("INSERT INTO _locktest (v) VALUES ('externo')")

        status, headers, body = _http(
            "POST", f"{base}{ROTA_LOCKTEST_WRITE}", body={"v": "servidor"}
        )
        assert status == 503, f"Esperava 503 sob lock real, veio {status}"
        assert headers.get("Retry-After") == "2", headers.get("Retry-After")
        assert body["sucesso"] is False
        assert body["codigo"] == "DB_LOCKED"

        ext.rollback()
        ext.close()

        status, _, body = _http("POST", f"{base}{ROTA_LOCKTEST_WRITE}", body={"v": "servidor"})
        assert status == 200, f"Esperava 200 apos liberar lock, veio {status}"
        assert body["sucesso"] is True

        status, _, _ = _http("GET", f"{base}/api/crm")
        assert status == 200, "Rota nao relacionada deveria seguir funcionando."

        verif = sqlite3.connect(db_path)
        try:
            qtd = verif.execute(
                "SELECT COUNT(*) FROM _locktest WHERE v='servidor'"
            ).fetchone()[0]
        finally:
            verif.close()
        assert qtd == 1, f"Escrita 'servidor' deveria estar persistida; qtd={qtd}"
    finally:
        try:
            ext.close()
        except Exception:
            pass