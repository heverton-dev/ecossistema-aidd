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
