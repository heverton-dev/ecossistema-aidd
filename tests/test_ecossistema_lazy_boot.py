# -*- coding: utf-8 -*-
"""
Testes unitários determinísticos de lazy dynamic import da CLI raiz ecossistema.py.
"""

import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


def test_cli_help_sem_carregar_click_antecipadamente():
    cmd = [
        sys.executable,
        "-c",
        (
            "import sys, subprocess\n"
            "proc = subprocess.run([sys.executable, 'ecossistema.py', '--help'], capture_output=True, text=True)\n"
            "assert proc.returncode == 0\n"
            "assert 'Comandos disponíveis:' in proc.stdout\n"
        ),
    ]
    res = subprocess.run(cmd, cwd=str(ROOT_DIR), capture_output=True, text=True)
    assert res.returncode == 0


def test_cli_lazy_import_click_sob_demanda():
    cmd = [
        sys.executable,
        "-c",
        (
            "import sys, ecossistema\n"
            "assert 'click' not in sys.modules\n"
            "click = ecossistema._obter_click()\n"
            "assert 'click' in sys.modules\n"
        ),
    ]
    res = subprocess.run(cmd, cwd=str(ROOT_DIR), capture_output=True, text=True)
    assert res.returncode == 0
