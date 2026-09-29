# -*- coding: utf-8 -*-
"""
Zero stubs nos scripts do aidd-forge (TICKET-01 / D13 / Lei #5).

Usa o verificador canônico do portão `gates/G_aidd_forge.py`
(`verificar_stubs`) contra toda a árvore de `tools/aidd-forge/`:
qualquer função com corpo vazio, `pass`, `...` ou `raise NotImplementedError`
reprova (exit 1); árvore sem stubs aprova (exit 0).
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
GATES_DIR = ROOT_DIR / "gates"
FORGE_DIR = ROOT_DIR / "tools" / "aidd-forge"

sys.path.insert(0, str(GATES_DIR))
import G_aidd_forge  # noqa: E402  (portão canônico Lei #5)


def test_forge_scripts_zero_stubs_exit_0():
    assert FORGE_DIR.is_dir(), f"diretório do forge inexistente: {FORGE_DIR}"
    violacoes = G_aidd_forge.verificar_stubs(FORGE_DIR)
    assert not violacoes, (
        "stubs detectados nos scripts do aidd-forge (Lei #5):\n"
        + "\n".join(violacoes)
    )
