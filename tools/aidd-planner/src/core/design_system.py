# -*- coding: utf-8 -*-
"""
Gera o DESIGN-SYSTEM.json de um projeto — a identidade visual única e dual mode
que os fluxos AIDD usam ao gerar o frontend Next.js (Leis Invioláveis #10 e #11).

Integra o motor topológico de arquétipos do Mobbin (Web/Desktop vs Mobile/PWA),
garante suporte nativo dual mode WCAG 2.1 e mantém retrocompatibilidade determinística.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional

_PLANNER_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ECOSSISTEMA_ROOT = os.path.join(_PLANNER_ROOT, "..", "..")
_COMP_DIR = os.path.join(_ECOSSISTEMA_ROOT, "componentes", "compartilhado", "src-core")
_MOBBIN_DIR = os.path.join(_ECOSSISTEMA_ROOT, "componentes", "compartilhado", "mcps", "mobbin_mcp")

for p in [_COMP_DIR, _MOBBIN_DIR]:
    if os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)

from design_catalog import escolher_paleta  # noqa: E402

try:
    from archetype_engine import classificar_arquetipo
except ImportError:
    classificar_arquetipo = None


def gerar_design_system(
    projeto_nome: str,
    slug: str,
    descricao: str,
    dominio: str,
    tela_referencia: Optional[Dict[str, Any]] = None,
    plataforma: str = "web"
) -> Dict[str, Any]:
    """Monta o DESIGN-SYSTEM.json (paleta dual mode e arquétipo topológico)."""
    paleta = escolher_paleta(f"{slug} {projeto_nome} {descricao}", dominio)

    arquetipo_info = None
    if classificar_arquetipo:
        ref = tela_referencia or {
            "app_name": projeto_nome,
            "tags": [dominio, slug],
            "screen_type": "dashboard"
        }
        arquetipo_info = classificar_arquetipo(ref, plataforma=plataforma)

    # Derivação nativa dual mode alinhada com WCAG 2.1
    cor_primaria = paleta.get("primary", "#3b82f6")
    tokens_dual = {
        "light": {
            "background": "#ffffff",
            "surface": "#f8fafc",
            "primary": cor_primaria,
            "foreground": "#0f172a",
            "muted": "#64748b",
            "border": "rgba(0, 0, 0, 0.08)"
        },
        "dark": {
            "background": "#0b0f17",
            "surface": "#111827",
            "primary": cor_primaria,
            "foreground": "#f8fafc",
            "muted": "#94a3b8",
            "border": "rgba(255, 255, 255, 0.12)"
        }
    }

    resultado: Dict[str, Any] = {
        "versao": "2.0.0",
        "projeto": slug,
        "gerado_em": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fonte": "catalogo-deterministico + motor topologico mobbin (zero LLM, Lei #1)",
        "paleta": paleta,
        "dual_mode": tokens_dual,
        "regras_craft_floor": [
            "Proibição estrita de emojis em interfaces corporativas: utilizar exclusivamente vetores SVG com stroke e fill semânticos",
            "Suporte nativo dual e espelhado a Light e Dark modes via :root e data-theme com transição atômica",
            "Responsividade fluida mobile-first com breakpoints declarados (mobile: <640px, tablet: 640-1024px, desktop: >1024px)",
            "Ergonomia móvel estrita: touch targets mínimos de 48px e suporte a env(safe-area-inset-*)",
            "Proibido usar classes de cor arbitrárias fora da paleta extraída",
            "Razão mínima de 1.25x entre títulos e texto de apoio para evitar flat-type-hierarchy",
            "Botões devem possuir obrigatoriamente estados hover, active e focus-visible acessíveis"
        ]
    }

    if arquetipo_info:
        resultado["arquetipo_topologico"] = arquetipo_info

    return resultado
