# -*- coding: utf-8 -*-
"""
Critério de rejeição determinístico e rollback transacional para aidd-handoff (D14 / Lei #13).
"""

from __future__ import annotations

import contextlib
from pathlib import Path
from typing import Generator


@contextlib.contextmanager
def executar_com_rollback(caminho_alvo: str | Path) -> Generator[Path, None, None]:
    p = Path(caminho_alvo).resolve()
    try:
        yield p
    except Exception:
        if p.exists():
            try:
                p.unlink()
            except OSError:
                pass
        raise
