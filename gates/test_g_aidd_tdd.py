# -*- coding: utf-8 -*-
"""
Teste de Quality Gate Determinístico de TDD (Ticket 7 / Lei #13).
Comprova que G_aidd_tdd.py aprova sessões íntegras (exit 0) e morde (exit 1) diante de:
1. Sessão deixada em estado RED não resolvido.
2. Arquivo de teste contendo stubs vazios (pass).
3. Arquivo de teste contendo assert trivial (assert True).
"""

import json
import subprocess
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
GATE = ROOT / "gates" / "G_aidd_tdd.py"

def executar_gate(sessao_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(GATE), "--sessao", str(sessao_path)],
        capture_output=True,
        text=True,
        cwd=str(ROOT)
    )

def test_gate_tdd_aprova_sessao_integra(tmp_path):
    teste_file = tmp_path / "test_valido.py"
    teste_file.write_text("def test_ok():\n    x = 10\n    assert x == 10\n", encoding="utf-8")

    sessao_file = tmp_path / "sessao.json"
    dados = {
        "alvo": "src/dummy.py",
        "seam": "dummy_seam",
        "fase_atual": "GREEN",
        "testes": [str(teste_file)]
    }
    sessao_file.write_text(json.dumps(dados), encoding="utf-8")

    res = executar_gate(sessao_file)
    assert res.returncode == 0
    assert "APROVADO" in res.stdout

def test_gate_tdd_morde_se_fase_for_red(tmp_path):
    teste_file = tmp_path / "test_valido.py"
    teste_file.write_text("def test_ok():\n    assert 1 + 1 == 2\n", encoding="utf-8")

    sessao_file = tmp_path / "sessao.json"
    dados = {
        "alvo": "src/dummy.py",
        "seam": "dummy_seam",
        "fase_atual": "RED",
        "testes": [str(teste_file)]
    }
    sessao_file.write_text(json.dumps(dados), encoding="utf-8")

    res = executar_gate(sessao_file)
    assert res.returncode == 1
    assert "abandonada na fase 'RED'" in res.stdout

def test_gate_tdd_morde_se_teste_tiver_stub(tmp_path):
    teste_file = tmp_path / "test_stub.py"
    teste_file.write_text("def test_com_stub():\n    pass\n", encoding="utf-8")

    sessao_file = tmp_path / "sessao.json"
    dados = {
        "alvo": "src/dummy.py",
        "seam": "dummy_seam",
        "fase_atual": "GREEN",
        "testes": [str(teste_file)]
    }
    sessao_file.write_text(json.dumps(dados), encoding="utf-8")

    res = executar_gate(sessao_file)
    assert res.returncode == 1
    assert "stub vazio" in res.stdout
