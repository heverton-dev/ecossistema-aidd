# -*- coding: utf-8 -*-
"""
Suíte de testes unitários para o módulo 'modulo1'.
Valida isolamento de schema, persistência SQLite WAL, regras de negócio e disparo de eventos.

Nota (não remover): os testes abaixo cobrem o fixture ESTÁTICO
`src/modules/modulo1/`, commitado por uma versão ANTIGA de `add_module.py` —
ele já diverge do que o gerador produz hoje (ordem de código em models.py
diferente, ainda que equivalente em comportamento). Ou seja, estes testes
provam que o fixture estático funciona, não que o GERADOR ATUAL funciona.
Por isso, ao final do arquivo, há um teste complementar que gera um módulo
novo via `add_module.py` (o gerador de verdade) dentro de um diretório
temporário, sobe o servidor real gerado e exercita CRUD via HTTP — qualquer
edição futura no gerador que quebre o módulo produzido é pega automaticamente
por esse teste, mesmo que o fixture estático continue intocado.
"""

import pytest
import os
import sys

# Garante que src esteja no PYTHONPATH
SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from core.database import Database
from core.events import EventBus
from modules.modulo1.models import init_schema
from modules.modulo1.services import Modulo1Service


@pytest.fixture
def test_env(tmp_path):
    """Fixture que isola o banco de dados e o EventBus para cada teste."""
    db_file = str(tmp_path / "test_modulo1.db")
    db = Database(f"sqlite:///{db_file}")
    with db.get_connection() as conn:
        init_schema(conn)

    events = EventBus()
    eventos_capturados = []
    events.on("modulo1_criado", lambda d: eventos_capturados.append(("criado", d)))
    events.on("modulo1_atualizado", lambda d: eventos_capturados.append(("atualizado", d)))
    events.on("modulo1_deletado", lambda d: eventos_capturados.append(("deletado", d)))

    service = Modulo1Service(db, events)
    return {"service": service, "events": eventos_capturados, "db": db}


def test_fluxo_completo_crud_modulo1(test_env):
    service = test_env["service"]
    eventos = test_env["events"]

    # 1. CREATE
    res_cria = service.criar(
        titulo="Item Teste Unitário Modulo1",
        descricao="Validação automatizada de integridade",
        status="ativo",
        dados={"valor": 150.0, "prioridade": "alta"}
    )
    assert res_cria["sucesso"] is True
    novo_id = res_cria["id"]
    assert novo_id > 0
    assert len(eventos) == 1
    assert eventos[0][0] == "criado"
    assert eventos[0][1]["id"] == novo_id

    # 2. READ (Obter por ID)
    item = service.obter_por_id(novo_id)
    assert item is not None
    assert item["titulo"] == "Item Teste Unitário Modulo1"
    assert item["status"] == "ativo"

    # 3. LIST
    lista = service.listar()
    assert len(lista) >= 1
    assert any(i["id"] == novo_id for i in lista)

    # 4. UPDATE
    res_up = service.atualizar(
        item_id=novo_id,
        titulo="Item Teste Modulo1 Atualizado",
        status="concluido"
    )
    assert res_up["sucesso"] is True
    assert len(eventos) == 2
    assert eventos[1][0] == "atualizado"

    item_mod = service.obter_por_id(novo_id)
    assert item["titulo"] != item_mod["titulo"]
    assert item_mod["titulo"] == "Item Teste Modulo1 Atualizado"
    assert item_mod["status"] == "concluido"

    # 5. DELETE
    res_del = service.deletar(novo_id)
    assert res_del["sucesso"] is True
    assert len(eventos) == 3
    assert eventos[2][0] == "deletado"

    item_deletado = service.obter_por_id(novo_id)
    assert item_deletado is None
    lista_pos = service.listar()
    assert all(i["id"] != novo_id for i in lista_pos)


def test_validacao_titulo_obrigatorio_modulo1(test_env):
    service = test_env["service"]
    with pytest.raises(ValueError):
        service.criar(titulo="   ")


# =============================================================================
# Teste dinâmico: gera um módulo com o GERADOR ATUAL (add_module.py) dentro
# de um diretório temporário — ao contrário dos testes acima, que validam o
# fixture estático `src/modules/modulo1/` já desatualizado em relação ao que
# o gerador produz hoje. Qualquer edição futura em add_module.py/
# compose_suite.py que quebre o módulo gerado (models/services/routes) é
# pega automaticamente aqui, via uma requisição HTTP real contra o servidor
# real gerado — nenhum mock, nenhuma leitura estática de código.
# =============================================================================

import json
import subprocess
import time
import urllib.error
import urllib.request

SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)


def _aguardar_servidor(processo, url, deadline_segundos=15):
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


def _post_json(url, payload):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get_json(url):
    with urllib.request.urlopen(url, timeout=5) as resp:
        return json.loads(resp.read().decode("utf-8"))


def test_modulo_gerado_pelo_add_module_py_atual_crud_via_http(tmp_path):
    """Compõe uma suíte real com um módulo gerado agora mesmo pelo gerador
    atual e exercita o fluxo CRUD completo via HTTP contra o servidor real."""
    from compose_suite import compose_suite

    target = tmp_path / "suite-modulo-dinamico"
    compose_suite(str(target), "Suite Dinamica Teste", ["itemdinamico"])

    processo = subprocess.Popen(
        [sys.executable, "src/server.py"],
        cwd=str(target),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        base = "http://127.0.0.1:3000"
        status = _aguardar_servidor(processo, f"{base}/api/itemdinamico")
        assert status == 200

        criado = _post_json(f"{base}/api/itemdinamico/criar", {"titulo": "Item Dinâmico"})
        assert criado["sucesso"] is True
        item_id = criado["id"]

        obtido = _get_json(f"{base}/api/itemdinamico/obter?id={item_id}")
        assert obtido["titulo"] == "Item Dinâmico"

        atualizado = _post_json(f"{base}/api/itemdinamico/atualizar", {"id": item_id, "status": "concluido"})
        assert atualizado["sucesso"] is True

        deletado = _post_json(f"{base}/api/itemdinamico/deletar", {"id": item_id})
        assert deletado["sucesso"] is True

        obtido_pos_delete = _get_json(f"{base}/api/itemdinamico/obter?id={item_id}")
        assert obtido_pos_delete.get("sucesso") is False
    finally:
        processo.terminate()
        try:
            processo.wait(timeout=5)
        except subprocess.TimeoutExpired:
            processo.kill()
