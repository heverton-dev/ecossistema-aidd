# -*- coding: utf-8 -*-
"""
Item 7 — regressao do gate G_SEGURANCA.py:
1. Os novos checks comportamentais (SQLi via bind parameter, XSS via
   Webhook Studio) executam ataque real e passam contra o codigo real do
   proprio repositorio (nao stub).
2. O relatorio final nao usa mais linguagem de marketing ("Blindagem",
   "NOTA A+", "CERTIFICACAO CONCEDIDA", "HOMOLOGADA PARA PRODUCAO GLOBAL")
   e reporta quantos checks sao comportamentais/config/estaticos de verdade.
3. A logica de neutralizacao de SQLi (bind parameter vs concatenacao) de
   fato discrimina seguro de vulneravel usando o mesmo motor (sqlite3 real).
"""

import os
import sqlite3
import subprocess
import sys

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GATE_SCRIPT = os.path.join(REPO_ROOT, "scripts", "gates", "G_SEGURANCA.py")

TERMOS_MARKETING_PROIBIDOS = [
    "Score de Blindagem",
    "NOTA A+",
    "CERTIFICAÇÃO CONCEDIDA",
    "BLINDADA E HOMOLOGADA PARA PRODUÇÃO GLOBAL",
    "AUDITORIA MILITAR",
]


def _run_gate():
    return subprocess.run(
        [sys.executable, GATE_SCRIPT, "--dir", REPO_ROOT],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )


def test_gate_passa_contra_o_proprio_repo_e_roda_checks_comportamentais():
    resultado = _run_gate()
    saida = resultado.stdout + resultado.stderr

    assert resultado.returncode == 0, saida
    assert "Neutralização Comportamental de XSS (Webhook Studio)" in saida
    assert "Neutralização Comportamental (bind parameter)" in saida
    # As duas linhas dos novos checks devem estar marcadas como PASS, nao WARN/FAIL
    for linha in saida.splitlines():
        if "Neutralização Comportamental de XSS" in linha or "Neutralização Comportamental (bind parameter)" in linha:
            assert "[PASS]" in linha, f"Check comportamental nao passou: {linha}"


def test_relatorio_final_nao_usa_linguagem_de_marketing():
    resultado = _run_gate()
    saida = resultado.stdout + resultado.stderr

    for termo in TERMOS_MARKETING_PROIBIDOS:
        assert termo not in saida, f"Termo de marketing proibido ainda presente na saida: {termo!r}"

    assert "comportamentais" in saida
    assert "de configuração" in saida
    assert "estáticos" in saida


def test_bind_parameter_neutraliza_payload_real_sqlite():
    """Mesmo motor (sqlite3) e mesmo payload usado pela Camada 3b do gate:
    com bind parameter, o payload e tratado como dado literal."""
    payload = "' OR '1'='1"
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute("CREATE TABLE _sqli_probe (id INTEGER PRIMARY KEY, nome TEXT)")
        conn.execute("INSERT INTO _sqli_probe (nome) VALUES (?)", (payload,))
        conn.execute("INSERT INTO _sqli_probe (nome) VALUES (?)", ("registro_legitimo",))
        conn.commit()

        linhas_seguras = conn.execute(
            "SELECT * FROM _sqli_probe WHERE nome = ?", (payload,)
        ).fetchall()
        assert len(linhas_seguras) == 1, "Bind parameter deveria neutralizar o payload"
    finally:
        conn.close()


def test_sem_bind_parameter_o_mesmo_payload_seria_vulneravel():
    """Prova que a asserção acima de fato discrimina seguro de vulneravel:
    a mesma consulta, construida por concatenacao (sem bind), vaza dados."""
    payload = "' OR '1'='1"
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute("CREATE TABLE _sqli_probe (id INTEGER PRIMARY KEY, nome TEXT)")
        conn.execute("INSERT INTO _sqli_probe (nome) VALUES (?)", (payload,))
        conn.execute("INSERT INTO _sqli_probe (nome) VALUES (?)", ("registro_legitimo",))
        conn.commit()

        sql_inseguro = "SELECT * FROM _sqli_probe WHERE nome = '" + payload + "'"
        linhas_vulneraveis = conn.execute(sql_inseguro).fetchall()
        assert len(linhas_vulneraveis) == 2, (
            "Pre-condicao do teste de regressao quebrada: concatenacao deveria "
            "vazar as 2 linhas (payload sempre-verdadeiro)"
        )
    finally:
        conn.close()


def _carregar_gate_como_modulo():
    import importlib.util
    spec = importlib.util.spec_from_file_location("g_seguranca_gate_modulo", GATE_SCRIPT)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _pid_esta_vivo(pid: int) -> bool:
    if sys.platform == "win32":
        saida = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True
        ).stdout
        return str(pid) in saida
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def test_run_matando_arvore_em_timeout_mata_processo_neto(tmp_path):
    """Achado real na validação E2E do Fluxo 01 (17/09/2026): pip-audit (Camada
    8: CVE Dependency Audit) cria um venv temporário e lança `pip install
    --upgrade pip wheel setuptools` (acesso real à rede) como subprocesso-neto.
    `subprocess.run(timeout=...)` só mata o processo direto — no Windows isso
    deixa o neto órfão, ainda tentando a rede indefinidamente, travando
    qualquer pre-commit que rode este gate com rede lenta/instável.
    `_run_matando_arvore_em_timeout` precisa matar a árvore inteira.

    Sem rede real e sem mockar subprocess: o "pai" simulado aqui lança um
    "filho" de longa duração e grava o PID dele num arquivo antes de também
    dormir, para o teste confirmar que o filho de fato morre junto."""
    import textwrap
    import time

    modulo = _carregar_gate_como_modulo()

    pid_filho_path = tmp_path / "pid_filho.txt"
    script_pai = tmp_path / "pai.py"
    script_pai.write_text(
        textwrap.dedent(f"""
            import subprocess, sys, time
            filho = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
            with open(r"{pid_filho_path}", "w") as f:
                f.write(str(filho.pid))
            time.sleep(60)
        """),
        encoding="utf-8",
    )

    with pytest.raises(subprocess.TimeoutExpired):
        modulo._run_matando_arvore_em_timeout(
            [sys.executable, str(script_pai)], timeout=2
        )

    for _ in range(30):
        if pid_filho_path.exists():
            break
        time.sleep(0.1)
    assert pid_filho_path.exists(), "processo pai simulado nunca chegou a spawnar o filho"
    pid_filho = int(pid_filho_path.read_text().strip())

    time.sleep(1)
    assert not _pid_esta_vivo(pid_filho), "processo neto ficou orfao vivo apos o timeout"
