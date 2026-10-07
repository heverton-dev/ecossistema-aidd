# -*- coding: utf-8 -*-
"""Fonte única ferramenta -> pasta canônica em modulos/ (ciclo-03 VSA, decisão A).

O mapa mora no campo "pasta" de componentes/compartilhado/specs/MAPA-DONOS-FERRAMENTAS.json.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional

RAIZ = Path(__file__).resolve().parents[1]
MAPA_DONOS = RAIZ / "componentes" / "compartilhado" / "specs" / "MAPA-DONOS-FERRAMENTAS.json"


@lru_cache(maxsize=1)
def pastas() -> Dict[str, str]:
    """{"aidd-forge": "modulos/01-governanca-e-qualidade/core/aidd-forge", ...}"""
    mapa = json.loads(MAPA_DONOS.read_text(encoding="utf-8"))
    return {nome: dados["pasta"] for nome, dados in mapa.items() if isinstance(dados, dict) and "pasta" in dados}


def pasta_ferramenta(nome: str, raiz: Path = RAIZ) -> Path:
    return Path(raiz) / pastas()[nome]


def ferramenta_do_caminho(caminho: str) -> Optional[str]:
    """Nome da ferramenta dona de um caminho relativo (modulos/.../aidd-<x>/...), ou None."""
    rel = caminho.replace("\\", "/")
    while rel.startswith("./"):
        rel = rel[2:]
    for nome, pasta in pastas().items():
        if rel == pasta or rel.startswith(pasta + "/"):
            return nome
    return None
