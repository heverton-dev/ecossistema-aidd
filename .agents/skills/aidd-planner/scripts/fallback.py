# -*- coding: utf-8 -*-
"""
Tratamento de exceções e resolução de colisões para aidd-planner-runner (D11).
"""

from pathlib import Path


def resolver_colisao_pasta(caminho_pasta: Path | str) -> Path:
    p = Path(caminho_pasta).resolve()
    if not p.exists():
        return p

    contador = 2
    while True:
        candidato = p.parent / f"{p.name}-{contador}"
        if not candidato.exists():
            return candidato
        contador += 1
