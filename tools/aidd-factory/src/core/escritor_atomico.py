# -*- coding: utf-8 -*-
"""Re-exporta o escritor atomico do ecossistema.

Fonte unica: componentes/compartilhado/src-core/escritor_atomico.py
"""
import os as _os
import sys as _sys

_COMP_DIR = _os.path.join(
    _os.path.dirname(_os.path.abspath(__file__)),
    "..", "..", "..", "componentes", "compartilhado", "src-core"
)
if _os.path.isdir(_COMP_DIR) and _COMP_DIR not in _sys.path:
    _sys.path.insert(0, _COMP_DIR)

from escritor_atomico import escrever_json_atomico

__all__ = ["escrever_json_atomico"]
