# -*- coding: utf-8 -*-
from pathlib import Path
import pytest
from scripts.micro_gates_worktree import (
    verificar_sintaxe_python,
    verificar_stubs_fatia,
    executar_micro_gates,
)


def test_verificar_sintaxe_python_ok(tmp_path: Path):
    arquivo = tmp_path / "modulo.py"
    arquivo.write_text("def soma(a, b):\n    return a + b\n", encoding="utf-8")
    ok, erros = verificar_sintaxe_python(tmp_path, ["modulo.py"])
    assert ok is True
    assert len(erros) == 0


def test_verificar_sintaxe_python_com_erro(tmp_path: Path):
    arquivo = tmp_path / "erro.py"
    arquivo.write_text("def quebrado(\n", encoding="utf-8")
    ok, erros = verificar_sintaxe_python(tmp_path, ["erro.py"])
    assert ok is False
    assert len(erros) == 1
    assert "Erro de sintaxe" in erros[0]


def test_verificar_stubs_fatia_detecta_todo(tmp_path: Path):
    arquivo = tmp_path / "stub.py"
    arquivo.write_text("x = 1\nresult = 'TODO: implementar'\n", encoding="utf-8")
    ok, erros = verificar_stubs_fatia(tmp_path, ["stub.py"])
    assert ok is False
    assert len(erros) == 1
    assert "Stub detectado" in erros[0]


def test_verificar_stubs_fatia_limpo(tmp_path: Path):
    arquivo = tmp_path / "limpo.py"
    arquivo.write_text("x = 1\n# Comentario sem stub no codigo ativo\nreturn x\n", encoding="utf-8")
    ok, erros = verificar_stubs_fatia(tmp_path, ["limpo.py"])
    assert ok is True
    assert len(erros) == 0


def test_executar_micro_gates_integrado_sucesso(tmp_path: Path):
    arquivo = tmp_path / "slice.py"
    arquivo.write_text("def executar():\n    return 42\n", encoding="utf-8")
    ok, erros = executar_micro_gates(
        worktree_path=tmp_path,
        slice_id="slice_teste",
        arquivos_esperados=["slice.py"],
        comandos_teste=["python -c \"import sys; sys.exit(0)\""],
        verbose=False,
    )
    assert ok is True
    assert len(erros) == 0


def test_executar_micro_gates_rejeita_teste_falho(tmp_path: Path):
    arquivo = tmp_path / "slice.py"
    arquivo.write_text("def executar():\n    return 42\n", encoding="utf-8")
    ok, erros = executar_micro_gates(
        worktree_path=tmp_path,
        slice_id="slice_teste",
        arquivos_esperados=["slice.py"],
        comandos_teste=["python -c \"import sys; sys.exit(1)\""],
        verbose=False,
    )
    assert ok is False
    assert len(erros) == 1
