#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
TESTES DE QUALIDADE: G_LEI_DECLARA_PORTAO (ISSUE-0010 & Lei #13)
=============================================================================
Testa o meta-gate G_LEI_DECLARA_PORTAO tanto no caminho feliz (aprovação com
o AGENTS.md real) quanto nos caminhos de reprovação deliberada (exit 1).
"""

import os
import subprocess
import sys
import tempfile
import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from gates.G_LEI_DECLARA_PORTAO import auditar_declaracoes_leis

GATE_SCRIPT = os.path.join(ROOT_DIR, "gates", "G_LEI_DECLARA_PORTAO.py")


def test_gate_aprova_estado_atual_agents_md():
    """Valida que o AGENTS.md atual do repositório está 100% conforme (exit 0)."""
    code, erros, conformes, total = auditar_declaracoes_leis()
    assert code == 0
    assert len(erros) == 0
    assert total >= 12
    assert len(conformes) >= total


def test_gate_aprova_multiplos_portoes_por_lei():
    """Valida que uma lei pode declarar mais de um portão verificador (exit 0)."""
    conteudo_valido = """
## 2. Inviolable Laws

1. **Tool Testing Discipline:** Protocolo de testes de ferramentas.
   - Portão: gates/G_ENV_ROT.py (provado)
   - Portão: gates/G_SKILL_ROT.py (provado)

---
"""
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(conteudo_valido)
        temp_path = f.name

    try:
        code, erros, conformes, total = auditar_declaracoes_leis(temp_path)
        assert code == 0
        assert len(erros) == 0
        assert total == 1
        assert len(conformes) == 2
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_gate_reprova_quando_lei_sem_declaracao():
    """Cenário deliberado de violação: uma lei não possui linha de declaração de portão (exit 1)."""
    conteudo_invalido = """
# Governance

## 2. Inviolable Laws

1. **Determinism First:** Use deterministic scripts.
   - Portão: sem gate — cumprimento por convenção (sem-gate)
2. **Binary Quality:** Every change must pass Quality Gates.
3. **Structured Persistence:** Persist state in files.
   - Portão: sem gate — cumprimento por convenção (sem-gate)

---
## 3. Flows
"""
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(conteudo_invalido)
        temp_path = f.name

    try:
        code, erros, conformes, total = auditar_declaracoes_leis(temp_path)
        assert code == 1
        assert any("Lei #2" in e and "Ausência de linha de declaração" in e for e in erros)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_gate_reprova_quando_forca_invalida():
    """Cenário deliberado de violação: força de enforcement com valor não permitido (exit 1)."""
    conteudo_invalido = """
## 2. Inviolable Laws

1. **Determinism First:** Use deterministic scripts.
   - Portão: sem gate — cumprimento por convenção (forca-desconhecida)

---
"""
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(conteudo_invalido)
        temp_path = f.name

    try:
        code, erros, conformes, total = auditar_declaracoes_leis(temp_path)
        assert code == 1
        assert any("Força 'forca-desconhecida' inválida" in e for e in erros)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_gate_reprova_quando_portao_declarado_nao_existe():
    """Cenário deliberado de violação: declara portão fantasma que não existe no disco (exit 1)."""
    conteudo_invalido = """
## 2. Inviolable Laws

1. **Determinism First:** Use deterministic scripts.
   - Portão: gates/G_PORTAO_FANTASMA_INEXISTENTE.py (provado)

---
"""
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(conteudo_invalido)
        temp_path = f.name

    try:
        code, erros, conformes, total = auditar_declaracoes_leis(temp_path)
        assert code == 1
        assert any("Portão declarado não existe no disco" in e for e in erros)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_gate_reprova_quando_sem_gate_tem_forca_inconsistente():
    """Cenário deliberado de violação: declara 'sem gate' mas marca como 'provado' (exit 1)."""
    conteudo_invalido = """
## 2. Inviolable Laws

1. **Determinism First:** Use deterministic scripts.
   - Portão: sem gate — cumprimento por convenção (provado)

---
"""
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(conteudo_invalido)
        temp_path = f.name

    try:
        code, erros, conformes, total = auditar_declaracoes_leis(temp_path)
        assert code == 1
        assert any("DEVE ser 'sem-gate'" in e for e in erros)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_gate_reprova_quando_secao_leis_ausente():
    """Cenário deliberado de violação: arquivo sem a seção de leis invariantes (exit 1)."""
    conteudo_invalido = """
# Governance sem secao 2
## 3. The 3 Flows
"""
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(conteudo_invalido)
        temp_path = f.name

    try:
        code, erros = auditar_declaracoes_leis(temp_path)
        assert code == 1
        assert "não encontrada ou vazia" in erros[0]
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_gate_subprocess_exit_1_com_violacao():
    """Verifica execução real de ponta a ponta via subprocess retornando código 1 em falha."""
    conteudo_invalido = """
## 2. Inviolable Laws

1. **Lei Sem Declaracao:** Descricao qualquer.

---
"""
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(conteudo_invalido)
        temp_path = f.name

    try:
        res = subprocess.run(
            [sys.executable, GATE_SCRIPT, "--agents-file", temp_path],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert res.returncode == 1
        assert "[VIOLAÇÃO]" in res.stdout
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
