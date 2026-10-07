# -*- coding: utf-8 -*-
"""Re-exporta o Result padrao do ecossistema.

Fonte unica: componentes/compartilhado/src-core/result.py
"""
import os as _os
import sys as _sys

def _achar_raiz_repo(inicio: str) -> str:
    curr = inicio
    while curr and _os.path.dirname(curr) != curr:
        if _os.path.isfile(_os.path.join(curr, "ecossistema.py")):
            return curr
        curr = _os.path.dirname(curr)
    return _os.path.normpath(_os.path.join(inicio, "..", "..", ".."))

_RAIZ = _achar_raiz_repo(_os.path.dirname(_os.path.abspath(__file__)))
_COMP_DIR = _os.path.join(_RAIZ, "componentes", "compartilhado", "src-core")
if _os.path.isdir(_COMP_DIR) and _COMP_DIR not in _sys.path:
    _sys.path.insert(0, _COMP_DIR)

from result import Result, Success, Failure, safe, ReturnsResult

__all__ = ["Result", "Success", "Failure", "safe", "ReturnsResult"]
