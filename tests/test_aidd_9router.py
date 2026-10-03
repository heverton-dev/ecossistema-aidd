# -*- coding: utf-8 -*-
"""
Testes determinísticos dos scripts da skill aidd-9router (sem rede, sem Orca, sem VPS).
Cobrem montagem de argumentos por harness, stack da VPS, provedor do omp, avaliador do bench e atalhos.
"""

import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "componentes" / "compartilhado" / "skills" / "aidd-9router" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import bench  # noqa: E402
import deploy_vps  # noqa: E402
import harness_9router  # noqa: E402
import instalar_wrappers  # noqa: E402
import omp_provider  # noqa: E402

MAPA = {"opus": "code-pro", "sonnet": "code-fast", "haiku": "code-free"}
URL = "https://gw.exemplo"


def test_sem_flags_remove_as_duas_formas():
    args = ["--pure", "-m", "x/y", "--model=z", "--trust"]
    assert harness_9router.sem_flags(args, ("-m", "--model")) == ["--pure", "--trust"]


def test_claude_recebe_variaveis_de_nivel_e_mantem_argumentos():
    args, env = harness_9router.montar("claude", ["--model", "sonnet"], URL, "k", MAPA)
    assert args == ["--model", "sonnet"]
    assert env["ANTHROPIC_BASE_URL"] == URL and env["ANTHROPIC_AUTH_TOKEN"] == "k"
    assert env["ANTHROPIC_DEFAULT_SONNET_MODEL"] == "code-fast"
    assert env["ANTHROPIC_DEFAULT_HAIKU_MODEL"] == "code-free"


@pytest.mark.parametrize("harness,variavel", [("opencode", "OPENCODE_CONFIG_CONTENT"), ("mimo", "MIMOCODE_CONFIG_CONTENT")])
def test_opencode_e_mimo_trocam_modelo_e_injetam_provedor(harness, variavel):
    args, env = harness_9router.montar(harness, ["--pure", "-m", "xiaomi/mimo", "--trust"], URL, "k", MAPA)
    assert args == ["--pure", "--trust", "-m", "aidd9r/code-fast"]
    cfg = json.loads(env[variavel])
    assert cfg["provider"]["aidd9r"]["options"]["baseURL"] == f"{URL}/v1"
    assert cfg["provider"]["aidd9r"]["options"]["apiKey"] == "{env:NINEROUTER_KEY}"
    assert cfg["small_model"] == "aidd9r/code-free"
    assert env["NINEROUTER_KEY"] == "k"


def test_omp_troca_os_quatro_papeis():
    args, env = harness_9router.montar("omp", ["--auto-approve", "--model", "nemotron"], URL, "k", MAPA)
    assert args[0] == "--auto-approve" and "nemotron" not in args
    pares = dict(zip(args[1::2], args[2::2]))
    assert pares == {"--model": "aidd9r/code-fast", "--smol": "aidd9r/code-free",
                     "--plan": "aidd9r/code-pro", "--slow": "aidd9r/code-pro"}
    assert env == {"NINEROUTER_KEY": "k"}


def test_stack_renderizado_sem_placeholder(monkeypatch):
    monkeypatch.setenv("TRAEFIK_NETWORK", "rede_x")
    texto = deploy_vps.renderizar_stack("9router.exemplo.org", "0.5.95")
    assert "$" not in texto
    assert "decolua/9router:0.5.95" in texto and "Host(`9router.exemplo.org`)" in texto
    assert "REQUIRE_API_KEY=true" in texto and "rede_x" in texto


def test_bloco_omp_usa_nome_da_variavel_e_nao_a_chave():
    texto = omp_provider.bloco(URL, ["code-pro", "code-fast", "code-free", "code-fast"])
    assert "apiKey: NINEROUTER_KEY" in texto and f"baseUrl: {URL}/v1" in texto
    assert texto.count("- id: code-fast") == 1


def test_bench_avalia_codigo_certo_trapaca_e_quebrado():
    certo = '''
def calc(expr):
    import re
    toks = re.findall(r"\\d+\\.\\d+|\\d+|[-+*/^()]|\\S", expr)
    if not toks: raise ValueError
    pos = [0]
    def ver(): return toks[pos[0]] if pos[0] < len(toks) else None
    def tira(): t = ver(); pos[0] += 1; return t
    def soma():
        v = mult()
        while ver() in ("+", "-"):
            v = v + mult() if tira() == "+" else v - mult()
        return v
    def mult():
        v = unario()
        while ver() in ("*", "/"):
            op = tira(); d = unario()
            if op == "/" and d == 0: raise ZeroDivisionError
            v = v * d if op == "*" else v / d
        return v
    def unario():
        if ver() == "-": tira(); return -unario()
        return pot()
    def pot():
        b = prim()
        if ver() == "^": tira(); return b ** unario()
        return b
    def prim():
        t = tira()
        if t == "(":
            v = soma()
            if tira() != ")": raise ValueError
            return v
        try: return float(t)
        except (TypeError, ValueError): raise ValueError
    v = soma()
    if pos[0] != len(toks): raise ValueError
    return v
'''
    assert bench.avaliar(certo) == (len(bench.TESTES), "")
    assert bench.avaliar("def calc(e):\n    return eval(e)\n")[1] == "usou eval/ast"
    assert bench.avaliar("def calc(e) return")[0] == 0


def test_atalhos_chamam_o_launcher_com_o_harness():
    bash, cmd = instalar_wrappers.conteudos("omp")
    assert bash.startswith("#!/usr/bin/env bash") and 'harness_9router.py" omp "$@"' in bash
    assert cmd.startswith("@echo off") and "omp %*" in cmd and "\r\n" in cmd
