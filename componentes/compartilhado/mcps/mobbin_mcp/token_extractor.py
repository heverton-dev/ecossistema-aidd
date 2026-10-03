# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — EXTRATOR DETERMINÍSTICO DE DESIGN TOKENS (DUAL MODE NATIVO)
=============================================================================
Extrai paleta de cores, contraste relativo WCAG 2.1, tipografia e espaçamentos
a partir de telas do Mobbin, gerando SEMPRE os dois modos: Light e Dark.
"""

from io import BytesIO
from typing import Any, Dict, List, Tuple
import requests

from componentes.compartilhado.mcps.mobbin_mcp.archetype_engine import classificar_arquetipo

try:
    from PIL import Image
except ImportError:
    Image = None


def rgb_para_hex(r: int, g: int, b: int) -> str:
    """Converte valores RGB (0-255) para string hexadecimal #RRGGBB."""
    return f"#{r:02x}{g:02x}{b:02x}"


def luminancia_relativa(r: int, g: int, b: int) -> float:
    """Calcula a luminância relativa conforme W3C WCAG 2.1."""
    def canal_linear(c: int) -> float:
        c_norm = c / 255.0
        return c_norm / 12.92 if c_norm <= 0.04045 else ((c_norm + 0.055) / 1.055) ** 2.4

    r_lin = canal_linear(r)
    g_lin = canal_linear(g)
    b_lin = canal_linear(b)
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def razao_contraste(lum1: float, lum2: float) -> float:
    """Calcula a razão de contraste entre duas luminâncias (1:1 a 21:1)."""
    mais_claro = max(lum1, lum2)
    mais_escuro = min(lum1, lum2)
    return (mais_claro + 0.05) / (mais_escuro + 0.05)


def extrair_paleta_imagem(dados_imagem: bytes, max_cores: int = 6) -> Dict[str, Any]:
    """
    Amostra a imagem da referência e deriva SEMPRE os dois temas: Light e Dark.
    Garante que a aplicação nasça nativamente com suporte a ambos os modos.
    """
    if not Image:
        return _fallback_tokens_duais()

    try:
        img = Image.open(BytesIO(dados_imagem)).convert("RGB")
        img.thumbnail((120, 120))

        cores = img.getcolors(maxcolors=20000)
        if not cores:
            return _fallback_tokens_duais()

        cores_ordenadas = sorted(cores, key=lambda item: item[0], reverse=True)

        # Cor de fundo dominante
        _, rgb_fundo = cores_ordenadas[0]
        lum_fundo = luminancia_relativa(*rgb_fundo)
        ref_is_dark = lum_fundo < 0.35

        paleta_hex: List[str] = []
        cor_primaria = None
        melhor_contraste_primaria = 0.0

        for _, rgb in cores_ordenadas:
            lum_c = luminancia_relativa(*rgb)
            contraste = razao_contraste(lum_fundo, lum_c)
            h = rgb_para_hex(*rgb)
            if h not in paleta_hex:
                paleta_hex.append(h)

            delta_cor = max(rgb) - min(rgb)
            if delta_cor > 30 and contraste >= 3.0 and contraste > melhor_contraste_primaria:
                cor_primaria = h
                melhor_contraste_primaria = contraste

            if len(paleta_hex) >= max_cores:
                break

        if not cor_primaria:
            cor_primaria = paleta_hex[1] if len(paleta_hex) > 1 else "#3b82f6"

        # Constrói os dois modos de forma determinística
        tokens_dark = {
            "background": rgb_para_hex(*rgb_fundo) if ref_is_dark else "#0d1117",
            "surface": "#161b22" if not ref_is_dark else "#181818",
            "primary": cor_primaria,
            "foreground": "#f0f6fc",
            "muted": "#8b949e",
            "border": "rgba(255, 255, 255, 0.12)"
        }

        tokens_light = {
            "background": rgb_para_hex(*rgb_fundo) if not ref_is_dark else "#f8fafc",
            "surface": "#ffffff",
            "primary": cor_primaria,
            "foreground": "#0f172a",
            "muted": "#64748b",
            "border": "rgba(0, 0, 0, 0.08)"
        }

        return {
            "modo": "dark" if ref_is_dark else "light",
            "modo_nativo_referencia": "dark" if ref_is_dark else "light",
            "light": tokens_light,
            "dark": tokens_dark,
            "paleta_extraida": paleta_hex[:max_cores]
        }
    except Exception:
        return _fallback_tokens_duais()


def _fallback_tokens_duais() -> Dict[str, Any]:
    """Retorna tokens duais de fallback calibrados com alto contraste WCAG AA."""
    return {
        "modo": "dark",
        "modo_nativo_referencia": "dark",
        "dark": {
            "background": "#0b0d13",
            "surface": "#12151e",
            "primary": "#3b82f6",
            "foreground": "#f8fafc",
            "muted": "#94a3b8",
            "border": "rgba(255, 255, 255, 0.08)"
        },
        "light": {
            "background": "#f8fafc",
            "surface": "#ffffff",
            "primary": "#2563eb",
            "foreground": "#0f172a",
            "muted": "#64748b",
            "border": "rgba(0, 0, 0, 0.08)"
        },
        "paleta_extraida": ["#3b82f6", "#10b981", "#f59e0b", "#ef4444"]
    }


def _derivar_stack_tipografico(app_name: str) -> Dict[str, str]:
    """Deriva a família tipográfica nativa conforme o DNA real do aplicativo."""
    nome_norm = (app_name or "").lower()

    if any(k in nome_norm for k in ["supabase", "linear", "vercel", "github", "render"]):
        return {
            "font_sans": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            "font_mono": "'JetBrains Mono', 'SF Mono', monospace"
        }

    if any(k in nome_norm for k in ["stripe", "ramp", "brex", "mercury"]):
        return {
            "font_sans": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            "font_mono": "'SF Mono', 'Roboto Mono', monospace"
        }

    return {
        "font_sans": "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        "font_mono": "ui-monospace, SFMono-Regular, Menlo, monospace"
    }


def extrair_tokens_mobbin(tela: Dict[str, Any]) -> Dict[str, Any]:
    """Gera especificação de design tokens contendo nativamente os modos Light e Dark."""
    app_name = tela.get("app_name", "Referência Mobbin")
    img_url = tela.get("image_url") or (tela.get("image", {}).get("url") if isinstance(tela.get("image"), dict) else None)

    tokens_cores = None
    if img_url and requests:
        try:
            resp = requests.get(img_url, timeout=10)
            if resp.status_code == 200:
                tokens_cores = extrair_paleta_imagem(resp.content)
        except Exception:
            pass

    if not tokens_cores:
        tokens_cores = _fallback_tokens_duais()

    stack_tipografia = _derivar_stack_tipografico(app_name)
    plataforma = tela.get("platform", "web")
    diretrizes_arquetipo = classificar_arquetipo(tela, plataforma)

    return {
        "origem_referencia": {
            "app_name": app_name,
            "screen_id": tela.get("id"),
            "mobbin_url": tela.get("mobbin_url"),
            "plataforma": plataforma
        },
        "arquetipo_layout": diretrizes_arquetipo,
        "cores": tokens_cores,
        "tipografia": {
            "font_sans": stack_tipografia["font_sans"],
            "font_mono": stack_tipografia["font_mono"],
            "escala": {
                "xs": "11px",
                "sm": "12px",
                "base": "14px",
                "md": "16px",
                "lg": "18px",
                "xl": "24px",
                "2xl": "32px",
                "hero": "44px"
            }
        },
        "espacamentos": {
            "grid_base": "4px",
            "padding_container": "24px",
            "gap_secoes": "32px",
            "gap_elementos": "16px"
        },
        "raios_borda": {
            "btn": "6px",
            "card": "8px",
            "pill": "9999px"
        },
        "regras_craft_floor": [
            "Proibição estrita de emojis em interfaces corporativas: utilizar exclusivamente vetores SVG com stroke e fill semânticos",
            "Suporte nativo dual e espelhado a Light e Dark modes via :root e data-theme com transição atômica",
            "Responsividade fluida mobile-first com breakpoints declarados (mobile: <640px, tablet: 640-1024px, desktop: >1024px)",
            "Ergonomia móvel estrita: touch targets mínimos de 48px e suporte a env(safe-area-inset-*)",
            "Proibido usar classes de cor arbitrárias fora da paleta extraída",
            "Proibido aninhar cards soltos (usar divisores border/gap-px padrão KpiStrip)",
            "Razão mínima de 1.25x entre títulos e texto de apoio para evitar flat-type-hierarchy",
            "Botões devem possuir obrigatoriamente estados hover, active e focus-visible acessíveis"
        ]
    }
