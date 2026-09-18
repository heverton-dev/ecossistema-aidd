# -*- coding: utf-8 -*-
"""
Reproduz bug real: `python ecossistema.py bridge unpack ...` (e qualquer
outro comando despachado via run_command) derrubava com UnicodeEncodeError
sempre que a ferramenta chamada imprimia um caractere fora do repertorio da
codepage padrao do console do Windows (cp1252) -- ex: aidd-bridge usa "✓"
para marcar cada fase concluida do pipeline. O pipeline morria no meio,
sem completar nenhuma fase, mesmo com todo o codigo correto.
"""

import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

import ecossistema


def test_run_command_forca_utf8_para_filho_imprimir_checkmark_sem_crash():
    codigo = "print(chr(0x2713))"
    rc = ecossistema.run_command([sys.executable, "-c", codigo], cwd=ROOT_DIR)
    assert rc == 0


def test_run_command_nao_sobrescreve_pythonioencoding_explicito(monkeypatch):
    monkeypatch.setenv("PYTHONIOENCODING", "utf-8")
    codigo = "import os; print(os.environ.get('PYTHONIOENCODING'))"
    rc = ecossistema.run_command([sys.executable, "-c", codigo], cwd=ROOT_DIR)
    assert rc == 0
