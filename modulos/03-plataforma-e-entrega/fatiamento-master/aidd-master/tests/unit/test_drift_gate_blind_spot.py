# -*- coding: utf-8 -*-
"""
Teste do Gate G_DRIFT_NUCLEO_COMPARTILHADO contra o blind spot
de arquivos que desaparecem de um dos lados (com esperado_identico==True),
e deteccao de divergencia de conteudo sem regressao.

Desde o item 2 de docs/planos/fazendo/correcao-arquitetura-limpa/, o gate
compara varios pares de diretorios (PARES), nao so um. A logica de
comparacao por par vive em _checar_par(nome_par, dir_a, dir_b, baseline_par)
e e testada isoladamente aqui, sem depender do sistema de arquivos real do
monorepo.
"""

import importlib.util
import os
import pytest

DOS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
GATE_PATH = os.path.join(DOS_ROOT, "gates", "G_DRIFT_NUCLEO_COMPARTILHADO.py")


@pytest.fixture
def gate_module():
    spec = importlib.util.spec_from_file_location("G_DRIFT_NUCLEO_COMPARTILHADO", GATE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_gate_falha_quando_arquivo_identico_desaparece_de_dir_a(tmp_path, gate_module):
    dir_a = tmp_path / "dir_a"
    dir_b = tmp_path / "dir_b"
    dir_a.mkdir()
    dir_b.mkdir()

    (dir_b / "single.py").write_text("#_identico", encoding="utf-8")
    baseline_par = {"single.py": {"esperado_identico": True, "motivo": None}}

    erros = gate_module._checar_par("par-teste", str(dir_a), str(dir_b), baseline_par)

    assert any("single.py" in e and "desapareceu de DIR_A" in e for e in erros), erros


def test_gate_falha_quando_arquivo_identico_desaparece_de_dir_b(tmp_path, gate_module):
    dir_a = tmp_path / "dir_a"
    dir_b = tmp_path / "dir_b"
    dir_a.mkdir()
    dir_b.mkdir()

    (dir_a / "single.py").write_text("#_identico", encoding="utf-8")
    baseline_par = {"single.py": {"esperado_identico": True, "motivo": None}}

    erros = gate_module._checar_par("par-teste", str(dir_a), str(dir_b), baseline_par)

    assert any("single.py" in e and "desapareceu de DIR_B" in e for e in erros), erros


def test_gate_sucesso_quando_identicos(tmp_path, gate_module):
    dir_a = tmp_path / "dir_a"
    dir_b = tmp_path / "dir_b"
    dir_a.mkdir()
    dir_b.mkdir()

    (dir_a / "ok.py").write_text("conteudo_identico", encoding="utf-8")
    (dir_b / "ok.py").write_text("conteudo_identico", encoding="utf-8")
    baseline_par = {"ok.py": {"esperado_identico": True, "motivo": None}}

    erros = gate_module._checar_par("par-teste", str(dir_a), str(dir_b), baseline_par)

    assert erros == []


def test_gate_falha_quando_conteudo_diverge(tmp_path, gate_module):
    dir_a = tmp_path / "dir_a"
    dir_b = tmp_path / "dir_b"
    dir_a.mkdir()
    dir_b.mkdir()

    (dir_a / "div.py").write_text("conteudo_a", encoding="utf-8")
    (dir_b / "div.py").write_text("conteudo_b", encoding="utf-8")
    baseline_par = {"div.py": {"esperado_identico": True, "motivo": None}}

    erros = gate_module._checar_par("par-teste", str(dir_a), str(dir_b), baseline_par)

    assert any("div.py" in e and "conteudo diverge agora" in e for e in erros), erros


def test_checar_drift_percorre_todos_os_pares_reais(gate_module):
    """Prova de integracao minima: checar_drift() itera gate_module.PARES (varios pares),
    nao mais um unico DIR_A/DIR_B fixo, e cada par tem (nome, dir_a, dir_b) validos."""
    assert len(gate_module.PARES) >= 5
    nomes = [p[0] for p in gate_module.PARES]
    assert "src/core" in nomes
    assert "scripts" in nomes
    assert "templates/core" in nomes
    assert "templates/v2" in nomes
    assert len(nomes) == len(set(nomes)), "nomes de par duplicados quebrariam o baseline"
