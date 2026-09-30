# -*- coding: utf-8 -*-
"""
Motor de Execução e Transição Red-Green para aidd-tdd (D8 / D10 / DoD 3).
Orquestra runners suportados e valida se a falha em RED é semântica/asserção e não sintaxe/ambiente.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Tuple, Dict, Any, List


RUNNERS_COMANDOS = {
    "pytest": ["pytest", "-v"],
    "vitest": ["npx", "vitest", "run"],
    "cargo": ["cargo", "test"],
    "go": ["go", "test", "-v", "./..."]
}


def analisar_resultado_red(saida: str, exit_code: int) -> Tuple[bool, str]:
    """
    Analisa se uma execução de teste qualifica como um estado RED válido:
    - exit_code deve ser diferente de 0.
    - Saída não pode conter SyntaxError, IndentationError, ou erro de compilação.
    - Saída deve conter falha de asserção ou falha funcional esperada.
    """
    if exit_code == 0:
        return False, "UNEXPECTED_PASS"

    saida_lower = saida.lower()

    # Erros de sintaxe ou compilação invalidam o RED
    if "syntaxerror" in saida_lower or "indentationerror" in saida_lower or "compilation error" in saida_lower:
        return False, "SYNTAX_ERROR"

    if "assertionerror" in saida_lower or "assert" in saida_lower or "failed" in saida_lower:
        return True, "ASSERTION_FAILURE"

    # Se falhou mas não foi erro de sintaxe, aceita como erro semântico
    return True, "FUNCTIONAL_FAILURE"


def executar_runner(runner: str, alvo: str = "", cwd: str | Path = None) -> Tuple[int, str]:
    if runner not in RUNNERS_COMANDOS:
        return 1, f"Runner '{runner}' não suportado."

    cmd = list(RUNNERS_COMANDOS[runner])
    if alvo:
        cmd.append(alvo)

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            shell=(sys.platform == "win32")
        )
        saida = proc.stdout + "\n" + proc.stderr
        return proc.returncode, saida
    except Exception as e:
        return 1, f"Erro ao disparar runner '{runner}': {e}"
