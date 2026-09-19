# -*- coding: utf-8 -*-
"""
Testes do meta-gate G_PORTAO_PROVA_QUE_MORDE (Lei #13).
Prova que o meta-gate aprova o estado 100% testado do repositório,
e morde (exit 1) se qualquer gate for introduzido sem teste ou com teste cosmético (apenas exit 0).
"""

import os
import subprocess
import sys
import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import gates.G_PORTAO_PROVA_QUE_MORDE as meta_gate
from gates.G_PORTAO_PROVA_QUE_MORDE import auditar_gates


def test_meta_gate_aprova_estado_atual():
    """No repositório íntegro, todos os 26 gates possuem testes de falha comprovados (exit 0)."""
    assert auditar_gates() == 0


def test_meta_gate_reprova_se_gate_novo_nao_tem_teste(tmp_path):
    """Lei #13: Prova que o meta-gate morde (exit 1) se um novo gate for criado sem arquivo de teste."""
    novo_gate = tmp_path / "G_NOVO_SEM_TESTE.py"
    novo_gate.write_text("# Novo gate sem teste espelhado\n", encoding="utf-8")

    codigo = auditar_gates(str(tmp_path))
    assert codigo == 1


def test_meta_gate_reprova_se_teste_e_apenas_caminho_feliz(tmp_path):
    """Lei #13: Prova que o meta-gate morde (exit 1) se o teste assertar apenas exit 0 (sem falha)."""
    novo_gate = tmp_path / "G_NOVO_COSMETICO.py"
    novo_gate.write_text("# Gate funcional\n", encoding="utf-8")

    # Teste cosmético que apenas testa caminho feliz
    teste_cosmetico = tmp_path / "test_g_novo_cosmetico.py"
    teste_cosmetico.write_text(
        "def test_sucesso_apenas():\n"
        "    resultado = 0\n"
        "    assert resultado == 0\n",
        encoding="utf-8"
    )

    codigo = auditar_gates(str(tmp_path))
    assert codigo == 1


def test_meta_gate_subprocess_exit_1_com_violacao(tmp_path):
    """Lei #13: Prova via processo CLI que o meta-gate retorna exit code 1 no shell."""
    novo_gate = tmp_path / "G_FACHADA.py"
    novo_gate.write_text("# Gate fachada\n", encoding="utf-8")

    cmd = [sys.executable, os.path.join(ROOT_DIR, "gates", "G_PORTAO_PROVA_QUE_MORDE.py")]
    # Monkeypatchando diretório via argumento / import
    # Criamos script wrapper para rodar subprocess no tmp_path
    wrapper = tmp_path / "run_meta.py"
    wrapper.write_text(
        f"import sys\n"
        f"sys.path.insert(0, r'{ROOT_DIR}')\n"
        f"from gates.G_PORTAO_PROVA_QUE_MORDE import auditar_gates\n"
        f"sys.exit(auditar_gates(r'{tmp_path}'))\n",
        encoding="utf-8"
    )

    res = subprocess.run([sys.executable, str(wrapper)], capture_output=True, text=True)
    assert res.returncode == 1
    assert "REGRA CANÔNICA VIOLADA (Lei #13)" in res.stdout
