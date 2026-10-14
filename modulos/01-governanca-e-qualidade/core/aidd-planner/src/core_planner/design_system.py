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

def _achar_raiz_repo(inicio: str) -> str:
    """Sobe pastas até achar ecossistema.py (raiz do repo), sem depender da profundidade."""
    curr = os.path.abspath(inicio)
    while os.path.dirname(curr) != curr:
        if os.path.isfile(os.path.join(curr, "ecossistema.py")):
            return curr
        curr = os.path.dirname(curr)
    return os.path.abspath(inicio)


_PLANNER_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ECOSSISTEMA_ROOT = _achar_raiz_repo(_PLANNER_ROOT)
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


def _escurecer(cor_hex: str, fator: float = 0.85) -> str:
    """Hover da cor primária: a mesma cor 15% mais escura."""
    r, g, b = (int(cor_hex[i:i + 2], 16) for i in (1, 3, 5))
    return "#{:02X}{:02X}{:02X}".format(int(r * fator), int(g * fator), int(b * fator))


_RAIOS = {"reto": ("2px", "4px"), "suave": ("6px", "8px"), "arredondado": ("12px", "16px")}
_DENSIDADES = {
    "compacta": ("16px", "24px", "8px"),
    "confortavel": ("24px", "32px", "16px"),
    "ampla": ("32px", "48px", "24px"),
}
RAIOS_VALIDOS = tuple(_RAIOS)
DENSIDADES_VALIDAS = tuple(_DENSIDADES)


def tokens_da_direcao(direcao_visual: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Tipografia, raios e espaçamentos que a spec declarou (a imagem do Mobbin não informa nenhum deles).

    O que a spec não declarar não é inventado: fica listado em `convencao` e segue o padrão do ecossistema.
    """
    direcao = direcao_visual or {}
    resultado: Dict[str, Any] = {"declarado_na_spec": []}
    if direcao.get("fonte"):
        resultado["tipografia"] = {"font_sans": f'"{direcao["fonte"]}", system-ui, sans-serif'}
        resultado["declarado_na_spec"].append("fonte")
    if direcao.get("raio") in _RAIOS:
        btn, card = _RAIOS[direcao["raio"]]
        resultado["raios_borda"] = {"btn": btn, "card": card, "pill": "9999px"}
        resultado["declarado_na_spec"].append("raio")
    if direcao.get("densidade") in _DENSIDADES:
        padding, secoes, elementos = _DENSIDADES[direcao["densidade"]]
        resultado["espacamentos"] = {"grid_base": "4px", "padding_container": padding,
                                     "gap_secoes": secoes, "gap_elementos": elementos}
        resultado["declarado_na_spec"].append("densidade")
    resultado["convencao"] = [c for c in ("fonte", "raio", "densidade") if c not in resultado["declarado_na_spec"]]
    return resultado


def gerar_design_system(
    projeto_nome: str,
    slug: str,
    descricao: str,
    dominio: str,
    tela_referencia: Optional[Dict[str, Any]] = None,
    plataforma: str = "web",
    direcao_visual: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Monta o DESIGN-SYSTEM.json (paleta dual mode e arquétipo topológico)."""
    paleta = escolher_paleta(f"{slug} {projeto_nome} {descricao}", dominio)
    if direcao_visual and direcao_visual.get("cor_primaria"):
        # A cor decidida na entrevista/spec vale mais que a do catálogo por palavras-chave.
        primaria = direcao_visual["cor_primaria"]
        paleta = {**paleta, "nome": "Direção visual da spec", "primaria": primaria,
                  "primaria_hover": _escurecer(primaria)}

    arquetipo_info = None
    if classificar_arquetipo:
        ref = tela_referencia or {
            "app_name": projeto_nome,
            "tags": [dominio, slug],
            "screen_type": "dashboard"
        }
        arquetipo_info = classificar_arquetipo(ref, plataforma=plataforma)

    # Derivação nativa dual mode alinhada com WCAG 2.1
    cor_primaria = paleta.get("primaria", "#3b82f6")
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

    fonte_descricao = "catalogo-deterministico + motor topologico mobbin (zero LLM, Lei #1)"
    if direcao_visual:
        fonte_descricao = "spec/entrevista (Visual Direction) + motor topologico mobbin (zero LLM, Lei #1)"
    elif tela_referencia and tela_referencia.get("fonte") == "online_curated_galleries":
        fonte_descricao = "referencias abertas online (21st.dev/transitions.dev/dribbble) + catalogo-deterministico"
    elif tela_referencia and tela_referencia.get("fonte") == "mobbin_api":
        fonte_descricao = "mobbin enterprise api + motor topologico mobbin"

    resultado: Dict[str, Any] = {
        "versao": "2.0.0",
        "projeto": slug,
        "gerado_em": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fonte": fonte_descricao,
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
    if direcao_visual:
        resultado["direcao_visual"] = direcao_visual
        resultado["tokens_da_direcao"] = tokens_da_direcao(direcao_visual)

    return resultado
