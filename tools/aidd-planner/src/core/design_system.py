# -*- coding: utf-8 -*-
"""
Gera o DESIGN-SYSTEM.json de um projeto — a identidade visual única que o
Fluxo 01/02 (aidd-generator/aidd-factory + aidd-master) deve usar ao gerar o
frontend Next.js (Lei Inviolável #11). Ver justificativa completa do
mecanismo determinístico (zero LLM) em
`componentes/compartilhado/src-core/design_catalog.py`.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict

_PLANNER_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ECOSSISTEMA_ROOT = os.path.join(_PLANNER_ROOT, "..", "..")
_COMP_DIR = os.path.join(_ECOSSISTEMA_ROOT, "componentes", "compartilhado", "src-core")
if os.path.isdir(_COMP_DIR) and _COMP_DIR not in sys.path:
    sys.path.insert(0, _COMP_DIR)

from design_catalog import escolher_paleta  # noqa: E402


def gerar_design_system(projeto_nome: str, slug: str, descricao: str, dominio: str) -> Dict[str, Any]:
    """Monta o DESIGN-SYSTEM.json (paleta única e determinística do projeto)."""
    paleta = escolher_paleta(f"{slug} {projeto_nome} {descricao}", dominio)
    return {
        "versao": "1.0.0",
        "projeto": slug,
        "gerado_em": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fonte": "catalogo-deterministico (zero LLM, Lei #1)",
        "paleta": paleta,
    }
