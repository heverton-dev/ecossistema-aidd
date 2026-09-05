# -*- coding: utf-8 -*-
"""
Teste de integração real (sem mocks) que prova que `add_module.py` religa
`src/server.py` de um projeto JÁ COMPOSTO.

Bug original: `src/server.py` é gerado estaticamente uma única vez, em
`compose_suite()`, por `generate_modular_server_code()`. `add_module.py`
gerava a fatia vertical completa (models/services/routes/UI/teste) e
atualizava o manifesto, mas nunca regenerava `src/server.py` — então a rota
do módulo adicionado depois da composição inicial nunca era registrada no
servidor em execução, respondendo 404 (ou nem chegava a subir, dependendo
do caso).

Estes testes usam subprocess real para chamar `add_module.py` e para subir
`src/server.py`, e fazem requisições HTTP reais contra o servidor gerado —
nenhum mock, nenhuma leitura estática de código.
"""

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

import pytest

SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)


def _aguardar_servidor(processo, url, deadline_segundos=15):
    """Faz polling em `url` até responder ou o processo do servidor morrer
    sozinho. Levanta AssertionError/pytest.fail em caso de timeout ou
    crash — nunca silencia uma falha real."""
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
            with urllib.request.urlopen(url, timeout=1) as resp:
                return resp.status
        except urllib.error.HTTPError as e:
            return e.code
        except (urllib.error.URLError, OSError) as e:
            ultimo_erro = e
            time.sleep(0.5)
    pytest.fail(f"Servidor não respondeu em {deadline_segundos}s para {url}: {ultimo_erro}")


def _compor_e_adicionar_modulo(target, db_engine="sqlite"):
    """Compõe uma suíte real com o módulo inicial 'crm' e, em seguida,
    chama `add_module.py` (subprocess real, mesmo comando documentado para
    o usuário final) para adicionar o módulo 'billing'."""
    from compose_suite import compose_suite

    compose_suite(str(target), "Suite Wiring Teste", ["crm"], db_engine=db_engine)

    resultado = subprocess.run(
        [sys.executable, "scripts/add_module.py", "billing"],
        cwd=str(target),
        capture_output=True,
        text=True,
    )
    assert resultado.returncode == 0, (
        f"add_module.py falhou ao adicionar 'billing':\n"
        f"stdout: {resultado.stdout}\nstderr: {resultado.stderr}"
    )
    return resultado


@pytest.fixture
def suite_com_modulo_adicionado(tmp_path):
    target = tmp_path / "suite-add-module"
    _compor_e_adicionar_modulo(target)
    return target


def test_rota_do_modulo_adicionado_depois_responde_200(suite_com_modulo_adicionado):
    """A rota do módulo INICIAL ('crm') e a rota do módulo ADICIONADO
    DEPOIS da composição ('billing') devem ambas responder 200. Antes da
    correção, 'billing' respondia 404 porque src/server.py nunca era
    religado por add_module.py."""
    target = suite_com_modulo_adicionado
    processo = subprocess.Popen(
        [sys.executable, "src/server.py"],
        cwd=str(target),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        status_inicial = _aguardar_servidor(processo, "http://127.0.0.1:3000/api/crm")
        assert status_inicial == 200

        status_adicionado = _aguardar_servidor(processo, "http://127.0.0.1:3000/api/billing")
        assert status_adicionado == 200
    finally:
        processo.terminate()
        try:
            processo.wait(timeout=5)
        except subprocess.TimeoutExpired:
            processo.kill()


def test_db_engine_postgres_preservado_ao_regenerar_server(tmp_path):
    """Regressão: sem persistir `db_engine` no manifesto, add_module.py
    cairia no fallback 'sqlite' ao regenerar src/server.py e reverteria
    silenciosamente uma suíte Postgres para SQLite."""
    target = tmp_path / "suite-postgres"
    _compor_e_adicionar_modulo(target, db_engine="postgres")

    plano = json.loads((target / "PLANO-EXECUCAO-ESTRUTURADO.json").read_text(encoding="utf-8"))
    assert plano["projeto"]["db_engine"] == "postgres"

    server_src = (target / "src" / "server.py").read_text(encoding="utf-8")
    assert "postgresql://" in server_src
    assert 'DB_PATH = os.path.join(CURRENT_DIR, "..", "suite.db")' not in server_src
