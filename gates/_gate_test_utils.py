# -*- coding: utf-8 -*-
"""
Utilitário compartilhado pelos testes de gates de raiz que rodam o script
real de um gate via subprocess contra uma árvore/repositório sintético
(ver test_g_ecossistema_integridade.py e test_g_segredos.py). Não é um
arquivo de teste — não segue o padrão test_*.py nem G_*.py do pytest.ini,
então não é coletado como suíte.
"""

import os
import subprocess
import sys


def rodar_gate(gate_path, cwd):
    """Executa o gate copiado via subprocess, com ambiente UTF-8, e retorna o CompletedProcess."""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, gate_path],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env
    )
