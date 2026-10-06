#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_g_arquitetura_deliverable.py - Testes determinísticos do gate G_ARQUITETURA_DELIVERABLE.
Valida que o gate reprova estritamente (exit 1) quando ocorrem violações de Clean Architecture
(SQL fora de infrastructure/ ou dependências de infraestrutura dentro da camada de domínio).
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
import pytest

from _gate_test_utils import rodar_gate

GATE_DIR = os.path.dirname(os.path.abspath(__file__))
GATE_PATH = os.path.join(GATE_DIR, "G_ARQUITETURA_DELIVERABLE.py")
ROOT_DIR = os.path.dirname(GATE_DIR)


def test_g_arquitetura_deliverable_reprova_sql_fora_de_infra(tmp_path):
    """Valida que G_ARQUITETURA_DELIVERABLE reprova (exit 1) quando há SQL fora de infrastructure/."""
    fake_gates = tmp_path / "gates"
    fake_gates.mkdir()
    shutil.copy2(GATE_PATH, fake_gates / "G_ARQUITETURA_DELIVERABLE.py")

    fake_src = tmp_path / "tools" / "aidd-master" / "src"
    fake_src.mkdir(parents=True)

    # Cria rota violando Clean Architecture com SQL direto
    arquivo_violador = fake_src / "routes.py"
    arquivo_violador.write_text(
        "import sqlite3\n"
        "def listar_usuarios():\n"
        "    conn = sqlite3.connect(':memory:')\n"
        "    return conn.execute('SELECT * FROM usuarios').fetchall()\n",
        encoding="utf-8"
    )

    proc = rodar_gate(str(fake_gates / "G_ARQUITETURA_DELIVERABLE.py"), cwd=str(tmp_path))
    assert proc.returncode == 1, f"Deveria ter retornado 1, retornou {proc.returncode}"
    assert "SQL-fora-infra" in proc.stdout
    assert "routes.py" in proc.stdout


def test_g_arquitetura_deliverable_reprova_import_infra_no_dominio(tmp_path):
    """Valida que G_ARQUITETURA_DELIVERABLE reprova (exit 1) quando a camada de domínio importa infraestrutura."""
    fake_gates = tmp_path / "gates"
    fake_gates.mkdir()
    shutil.copy2(GATE_PATH, fake_gates / "G_ARQUITETURA_DELIVERABLE.py")

    fake_domain = tmp_path / "tools" / "aidd-master" / "src" / "domain"
    fake_domain.mkdir(parents=True)

    # Entidade importando banco ou infra
    entidade = fake_domain / "usuario.py"
    entidade.write_text(
        "import sqlite3\n"
        "class Usuario:\n"
        "    pass\n",
        encoding="utf-8"
    )

    proc = rodar_gate(str(fake_gates / "G_ARQUITETURA_DELIVERABLE.py"), cwd=str(tmp_path))
    assert proc.returncode == 1, f"Deveria ter retornado 1, retornou {proc.returncode}"
    assert "Domain-puro" in proc.stdout or "SQL-fora-infra" in proc.stdout


def test_g_arquitetura_deliverable_passa_com_arquitetura_limpa(tmp_path):
    """Valida que G_ARQUITETURA_DELIVERABLE aprova (exit 0) quando o código está em conformidade."""
    fake_gates = tmp_path / "gates"
    fake_gates.mkdir()
    shutil.copy2(GATE_PATH, fake_gates / "G_ARQUITETURA_DELIVERABLE.py")

    fake_infra = tmp_path / "tools" / "aidd-master" / "src" / "infrastructure"
    fake_infra.mkdir(parents=True)
    (fake_infra / "repositorio.py").write_text(
        "import sqlite3\n"
        "class Repo:\n"
        "    def find(self):\n"
        "        pass\n",
        encoding="utf-8"
    )

    fake_domain = tmp_path / "tools" / "aidd-master" / "src" / "domain"
    fake_domain.mkdir(parents=True)
    (fake_domain / "modelo.py").write_text(
        "class Modelo:\n"
        "    def __init__(self, id: str):\n"
        "        self.id = id\n",
        encoding="utf-8"
    )

    proc = rodar_gate(str(fake_gates / "G_ARQUITETURA_DELIVERABLE.py"), cwd=str(tmp_path))
    assert proc.returncode == 0, f"Falhou inesperadamente:\n{proc.stdout}\n{proc.stderr}"
    assert "0 violacao(es)" in proc.stdout
    assert "APROVADO" in proc.stdout
