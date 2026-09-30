# -*- coding: utf-8 -*-
"""
Módulo de Limpeza e Rollback para aidd-tickets (Ticket 8 / D14 / DoD 7).
Remove artefatos parciais ou corrompidos em caso de erro de validação.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Union


def limpar_artefatos_parciais(caminhos: List[Union[str, Path]]) -> bool:
    sucesso = True
    for c in caminhos:
        p = Path(c)
        try:
            if p.is_file():
                p.unlink(missing_ok=True)
            elif p.is_dir():
                for filho in p.glob("*"):
                    if filho.is_file():
                        filho.unlink(missing_ok=True)
                p.rmdir()
        except Exception:
            sucesso = False
    return sucesso
