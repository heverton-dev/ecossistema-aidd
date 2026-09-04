# -*- coding: utf-8 -*-
"""
Testes de compose_suite.py — cobertura que nao existia antes de 04/09/2026.

Contexto (nao remover esta nota): compose_suite.py e a implementacao real
por tras de `/master compose` (a funcionalidade mais visivel do produto:
gerar uma aplicacao inteira, com N modulos, servidor e front-end). Ate
04/09/2026 este modulo tinha ZERO testes — nenhum teste sequer importava
compose_suite.py. Isso permitiu 3 bugs reais sobreviverem sem ninguem
notar, ate alguem tentar rodar `/master compose` de ponta a ponta pela
primeira vez:

1. SyntaxError real no arquivo (uma docstring interna do template do
   server.py gerado usava aspas triplas, fechando prematuramente a string
   externa que envolve todo o server.py, linhas 70-640).
   Isso quebrava a IMPORTACAO do proprio compose_suite.py.
2. templates/core/database.py desatualizado (versao sem RLSConnection) —
   toda aplicacao composta recebia um database.py incompleto.
3. templates/core/logs.py nunca existia nem estava na lista de arquivos
   copiados (core_files), mas o server.py gerado faz
   `from core.logs import ...` — toda aplicacao composta tinha um
   servidor que nao subia (ModuleNotFoundError).

Estes testes existem para que nenhum desses 3 bugs (ou a mesma CLASSE de
bug: erro de sintaxe no modulo, template referenciando modulo nao copiado)
volte a passar despercebido.
"""

import ast
import os
import re
import shutil
import subprocess
import sys
import time

import pytest

SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

COMPOSE_SUITE_PATH = os.path.join(SCRIPTS_DIR, "compose_suite.py")


# =============================================================================
# 1. O modulo tem que sequer COMPILAR — o bug mais basico que existiu aqui.
# =============================================================================

def test_compose_suite_compila_sem_erro_de_sintaxe():
    """Bug real: uma docstring `\"\"\"` dentro do template gigante do
    server.py fechava a string externa prematuramente, quebrando a
    importacao do proprio compose_suite.py. Nenhum teste pegava isso
    porque nenhum teste importava o modulo."""
    with open(COMPOSE_SUITE_PATH, "r", encoding="utf-8") as f:
        source = f.read()
    ast.parse(source, filename=COMPOSE_SUITE_PATH)  # levanta SyntaxError se quebrado


def test_compose_suite_importa_de_verdade():
    """Redundante com o teste acima de proposito: um cobre erro de sintaxe
    puro, este cobre qualquer outro erro que só aparece na importacao real
    (import circular, NameError no nivel do modulo, etc.)."""
    import importlib
    import compose_suite  # noqa: F401
    importlib.reload(compose_suite)


# =============================================================================
# 2. O server.py GERADO nao pode referenciar modulo core/ que nao existe.
#    Esta e a classe de bug do logs.py — testa de forma generica pra
#    pegar qualquer modulo futuro que caia na mesma armadilha.
# =============================================================================

@pytest.fixture
def suite_composta(tmp_path):
    from compose_suite import compose_suite
    target = tmp_path / "suite-teste"
    compose_suite(str(target), "Suite Teste", ["produtos"])
    return target


def test_server_gerado_nao_referencia_modulo_core_ausente(suite_composta):
    server_path = suite_composta / "src" / "server.py"
    assert server_path.exists()
    server_src = server_path.read_text(encoding="utf-8")

    modulos_importados = set(re.findall(r"from core\.(\w+) import", server_src))
    assert modulos_importados, "esperava pelo menos 1 'from core.X import' no server.py gerado"

    core_dir = suite_composta / "src" / "core"
    ausentes = [
        f"core/{m}.py" for m in modulos_importados
        if not (core_dir / f"{m}.py").exists()
    ]
    assert not ausentes, (
        f"server.py gerado importa de módulo(s) core/ que não foram copiados "
        f"para o projeto: {ausentes}. Verifique a lista core_files em "
        f"compose_suite.py."
    )


def test_server_gerado_compila_sem_erro_de_sintaxe(suite_composta):
    server_path = suite_composta / "src" / "server.py"
    ast.parse(server_path.read_text(encoding="utf-8"), filename=str(server_path))


# =============================================================================
# 3. database.py copiado nao pode ser a versao desatualizada sem RLS.
# =============================================================================

def test_database_copiado_tem_rls_connection(suite_composta):
    database_path = suite_composta / "src" / "core" / "database.py"
    assert database_path.exists()
    conteudo = database_path.read_text(encoding="utf-8")
    assert "class RLSConnection" in conteudo, (
        "database.py copiado para o projeto composto está desatualizado "
        "(sem RLSConnection) — verifique se templates/core/database.py "
        "está sincronizado com src/core/database.py."
    )


# =============================================================================
# 4. Teste de fogo: o servidor gerado PRECISA subir e responder de verdade.
#    Sem isso, os 3 testes acima poderiam passar e o bug do logs.py ainda
#    assim existir (ex.: um 4o modulo core futuro com o mesmo problema).
# =============================================================================

def test_servidor_gerado_sobe_e_responde(suite_composta):
    import urllib.request
    import urllib.error

    processo = subprocess.Popen(
        [sys.executable, "src/server.py"],
        cwd=str(suite_composta),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        ultimo_erro = None
        deadline = time.time() + 15
        while time.time() < deadline:
            if processo.poll() is not None:
                saida = processo.stdout.read()
                pytest.fail(f"Servidor encerrou sozinho antes de responder (exit "
                            f"{processo.returncode}):\n{saida}")
            try:
                with urllib.request.urlopen("http://127.0.0.1:3000/api/produtos", timeout=1) as resp:
                    assert resp.status == 200
                    return
            except (urllib.error.URLError, ConnectionError) as e:
                ultimo_erro = e
                time.sleep(0.5)
        pytest.fail(f"Servidor não respondeu em 15s: {ultimo_erro}")
    finally:
        processo.terminate()
        try:
            processo.wait(timeout=5)
        except subprocess.TimeoutExpired:
            processo.kill()
