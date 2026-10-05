# -*- coding: utf-8 -*-
"""
Motor determinístico de validação e serialização de handoff (D8).
- Validação das 5 seções obrigatórias
- Verificação e bloqueio de código colado (def, class, import)
"""

from __future__ import annotations

import re
from typing import Dict, List

SECOES_CANONICAS = [
    "Initial Goal",
    "Completed Work",
    "Quality Gate State",
    "Next Actions",
    "Discovered Invariants & Gotchas",
]

PADRAO_CODIGO = re.compile(r"^\s*(def\s+\w+|class\s+\w+|import\s+\w+|from\s+\w+\s+import)", re.MULTILINE)


def validar_conteudo(conteudo: str) -> Dict[str, object]:
    faltantes: List[str] = []
    for secao in SECOES_CANONICAS:
        if not re.search(rf"^##\s+{re.escape(secao)}", conteudo, re.MULTILINE):
            faltantes.append(secao)

    codigo_detectado = bool(PADRAO_CODIGO.search(conteudo))
    valido = (len(faltantes) == 0) and not codigo_detectado

    return {
        "valido": valido,
        "secoes_faltantes": faltantes,
        "codigo_colado_detectado": codigo_detectado,
    }
