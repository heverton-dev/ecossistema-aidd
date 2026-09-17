#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Runner integrado do aidd-generator com suporte nativo ao Protocolo Delegado.
Inicia o mediador de requisições em background e executa o pipeline completo.
"""

import sys
import os
import threading
from pathlib import Path

# Adiciona caminhos ao sys.path
SCRIPTS_DIR = Path(__file__).resolve().parent
GEN_DIR = SCRIPTS_DIR.parent
ROOT_DIR = GEN_DIR.parent.parent

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(GEN_DIR) not in sys.path:
    sys.path.insert(0, str(GEN_DIR))

from aidd_delegado_mediator import loop_mediador
import subprocess

def main():
    # Detecta pasta alvo se fornecida em --pasta ou --output
    pasta_alvo = None
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg in ('--pasta', '--output') and i + 1 < len(args):
            pasta_alvo = args[i + 1]
            break

    pastas_cache = [
        str(SCRIPTS_DIR / ".aidd" / "cache"),
        str(GEN_DIR / ".aidd" / "cache"),
        str(Path.cwd() / ".aidd" / "cache"),
    ]
    if pasta_alvo:
        pastas_cache.append(str(Path(pasta_alvo) / ".aidd" / "cache"))

    # Inicia thread mediadora do Protocolo Delegado
    stop_event = threading.Event()
    t = threading.Thread(target=loop_mediador, args=(pastas_cache, stop_event), daemon=True)
    t.start()

    # Executa o pipeline_completo.py passando os argumentos
    pipeline_script = str(SCRIPTS_DIR / "pipeline_completo.py")
    cmd = [sys.executable, pipeline_script] + args

    env = os.environ.copy()
    env["PYTHONPATH"] = str(GEN_DIR)

    try:
        res = subprocess.run(cmd, env=env)
        return res.returncode
    finally:
        stop_event.set()

if __name__ == '__main__':
    sys.exit(main())
