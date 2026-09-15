# -*- coding: utf-8 -*-
"""Re-exporta o Result padrao do ecossistema.

Fonte unica: componentes/compartilhado/src-core/result.py
"""
import os as _os
import sys as _sys

_COMP_DIR = _os.path.join(
    _os.path.dirname(_os.path.abspath(__file__)),
    "..", "..", "..", "componentes", "compartilhado", "src-core"
)
if _os.path.isdir(_COMP_DIR) and _COMP_DIR not in _sys.path:
    _sys.path.insert(0, _COMP_DIR)

from result import Result, Success, Failure, safe, ReturnsResult

__all__ = ["Result", "Success", "Failure", "safe", "ReturnsResult"]
