# -*- coding: utf-8 -*-
"""Ticket 9-B: o passo a passo do Mobbin por harness (claude, agy, mimo, opencode, omp) mapeado e testado.

Os testes comuns travam o mapa (cada harness tem passos, a URL certa e um nível de verificação honesto).
Os testes `real_` rodam os comandos de verdade no harness instalado; ficam atrás de
AIDD_TESTE_HARNESS_REAL=1 porque mexem (e desfazem) a configuração de MCP do usuário, sempre com um nome
descartável. Sem o binário instalado, o teste real é pulado.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import uuid

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core_planner import ambiente

HARNESSES = ("claude-code", "antigravity", "mimocode", "opencode", "omp", "gemini-cli")
REAL = os.environ.get("AIDD_TESTE_HARNESS_REAL") == "1"


@pytest.mark.parametrize("harness", HARNESSES)
def test_cada_harness_tem_passos_com_a_url_e_um_nivel_valido(harness):
    passos = ambiente.passo_a_passo_mcp(harness)
    assert len(passos) >= 3
    assert any(ambiente.URL_MCP_MOBBIN in p for p in passos)
    assert ambiente.nivel_verificacao(harness) in ambiente.NIVEIS_VERIFICACAO
    assert f"[verificação deste passo a passo: {ambiente.nivel_verificacao(harness)}]" in passos[-1]


def test_niveis_declarados_sao_os_que_foram_realmente_exercitados():
    assert ambiente.nivel_verificacao("claude-code") == "executado"
    assert ambiente.nivel_verificacao("antigravity") == "executado"
    assert ambiente.nivel_verificacao("mimocode") == "help"
    assert ambiente.nivel_verificacao("omp") == "binario"
    assert ambiente.nivel_verificacao("opencode") == "documentacao"
    assert ambiente.nivel_verificacao("desconhecido") is None


def test_opencode_nao_manda_usar_um_comando_que_nao_existe():
    texto = "\n".join(ambiente.passo_a_passo_mcp("opencode"))
    assert "opencode mcp add mobbin" not in texto
    assert '"type": "remote"' in texto and "opencode mcp auth mobbin" in texto


def test_omp_usa_os_comandos_de_barra_e_nao_um_subcomando_inexistente():
    texto = "\n".join(ambiente.passo_a_passo_mcp("omp"))
    assert "/mcp add mobbin" in texto and "--transport http" in texto and "/mcp reauth mobbin" in texto
    assert "omp mcp" not in texto


@pytest.mark.parametrize("env,esperado", [
    ({"OMP_PLUGIN_ROOT": "x"}, "omp"),
    ({"OMP_PROFILE": "x"}, "omp"),
    ({"AGY_HOME": "x"}, "antigravity"),
    ({"OMP_NUM_THREADS": "4"}, "desconhecido"),  # variável do OpenMP, não do omp
    ({"CLAUDECODE": "1", "OMP_PROFILE": "x"}, "claude-code"),  # omp dentro do Claude Code: vale o Claude Code
])
def test_deteccao_dos_harnesses_novos(env, esperado):
    assert ambiente.detectar_harness(env) == esperado


# --- execução real (opt-in) -----------------------------------------------------------------------------

def _rodar(cmd, cwd, timeout=60):
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=timeout)


@pytest.mark.skipif(not (REAL and shutil.which("claude")), reason="AIDD_TESTE_HARNESS_REAL=1 e `claude` instalado")
def test_real_claude_mcp_add_get_remove(tmp_path):
    nome = "mobbin-teste-" + uuid.uuid4().hex[:6]
    try:
        add = _rodar(["claude", "mcp", "add", "--transport", "http", nome, ambiente.URL_MCP_MOBBIN], tmp_path)
        assert add.returncode == 0, add.stderr
        get = _rodar(["claude", "mcp", "get", nome], tmp_path)
        assert ambiente.URL_MCP_MOBBIN in get.stdout and "http" in get.stdout.lower()
    finally:
        _rodar(["claude", "mcp", "remove", nome], tmp_path)
    assert nome not in _rodar(["claude", "mcp", "list"], tmp_path, timeout=120).stdout


@pytest.mark.skipif(not (REAL and shutil.which("agy")), reason="AIDD_TESTE_HARNESS_REAL=1 e `agy` instalado")
def test_real_agy_mcp_add_list_remove(tmp_path):
    nome = "mobbin-teste-" + uuid.uuid4().hex[:6]
    try:
        add = _rodar(["agy", "mcp", "add", nome, ambiente.URL_MCP_MOBBIN], tmp_path)
        assert add.returncode == 0 and "(http)" in add.stdout
        assert nome in _rodar(["agy", "mcp", "list"], tmp_path).stdout
    finally:
        _rodar(["agy", "mcp", "remove", nome], tmp_path)
    assert nome not in _rodar(["agy", "mcp", "list"], tmp_path).stdout


@pytest.mark.skipif(not (REAL and shutil.which("mimo")), reason="AIDD_TESTE_HARNESS_REAL=1 e `mimo` instalado")
def test_real_mimo_tem_add_auth_e_list():
    res = _rodar(["mimo", "mcp", "--help"], os.getcwd(), timeout=40)
    ajuda = res.stdout + res.stderr  # o yargs do mimo escreve a ajuda no stderr fora de um terminal
    for subcomando in ("mimo mcp add", "mimo mcp auth", "mimo mcp list"):
        assert subcomando in ajuda
