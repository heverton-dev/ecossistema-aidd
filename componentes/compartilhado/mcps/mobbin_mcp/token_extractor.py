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


RODAPE_PX_EM_768 = 48  # barra escura "curated by Mobbin" das imagens da API (medida em 768 px de largura)


def recortar_rodape(img):
    """Tira a barra de rodapé do Mobbin (proporcional à largura) antes de amostrar as cores."""
    corte = round(RODAPE_PX_EM_768 * img.width / 768)
    if corte and img.height > corte * 3:
        return img.crop((0, 0, img.width, img.height - corte))
    return img


def _agrupar_tons(img):
    """Funde tons quase iguais (anti-aliasing, degradês de fundo) em 16 níveis por canal."""
    return img.point(lambda v: (v // 16) * 16 + 8)


def extrair_paleta_imagem(dados_imagem: bytes, max_cores: int = 6) -> Dict[str, Any]:
    """
    Amostra a imagem da referência e deriva SEMPRE os dois temas: Light e Dark.
    Garante que a aplicação nasça nativamente com suporte a ambos os modos.
    """
    if not Image:
        return _fallback_tokens_duais()

    try:
        img = Image.open(BytesIO(dados_imagem)).convert("RGB")
        img = _agrupar_tons(recortar_rodape(img))
        img.thumbnail((160, 160))

        cores = img.getcolors(maxcolors=40000)
        if not cores:
            return _fallback_tokens_duais()

        cores_ordenadas = sorted(cores, key=lambda item: item[0], reverse=True)

        # Cor de fundo dominante
        _, rgb_fundo = cores_ordenadas[0]
        lum_fundo = luminancia_relativa(*rgb_fundo)
        ref_is_dark = lum_fundo < 0.35

        paleta_hex: List[str] = []
        cor_primaria = None
        melhor_pontuacao = 0.0
        relaxada = None
        melhor_relaxada = 0.0

        # Percorre TODAS as cores (o defeito antigo parava ao juntar 6 tons de fundo e nunca via a cor
        # da marca). A primária é a mais saturada e frequente com contraste mínimo de 3:1 sobre o fundo.
        for contagem, rgb in cores_ordenadas:
            h = rgb_para_hex(*rgb)
            if h not in paleta_hex and len(paleta_hex) < max_cores:
                paleta_hex.append(h)

            delta_cor = max(rgb) - min(rgb)
            contraste = razao_contraste(lum_fundo, luminancia_relativa(*rgb))
            if delta_cor > 30:
                pontuacao = contagem * (delta_cor / 255.0)
                if contraste >= 3.0 and pontuacao > melhor_pontuacao:
                    cor_primaria = h
                    melhor_pontuacao = pontuacao
                elif contraste >= 1.8 and pontuacao > melhor_relaxada:
                    relaxada = h
                    melhor_relaxada = pontuacao

        # Telas quase cinzas (ex.: Linear) não têm cor de marca confiável. Segundo passe com contraste
        # menor; se ainda assim não houver, declara "não detectada" em vez de inventar um tom de fundo.
        cor_primaria = cor_primaria or relaxada
        primaria_detectada = cor_primaria is not None
        if not primaria_detectada:
            cor_primaria = "#3b82f6"

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
            "paleta_extraida": paleta_hex[:max_cores],
            "primaria_detectada": primaria_detectada
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
        "paleta_extraida": ["#3b82f6", "#10b981", "#f59e0b", "#ef4444"],
        "primaria_detectada": False
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


def _url_da_imagem(tela: Dict[str, Any]):
    """`image.url` é o campo atual da API; `image_url` está deprecado e só vale se faltar o novo."""
    imagem = tela.get("image")
    if isinstance(imagem, dict) and imagem.get("url"):
        return imagem["url"]
    return tela.get("image_url")


def _baixar_padrao(url: str) -> bytes:
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.content


def extrair_tokens_mobbin(tela: Dict[str, Any], baixar=None) -> Dict[str, Any]:
    """Gera especificação de design tokens contendo nativamente os modos Light e Dark."""
    app_name = tela.get("app_name", "Referência Mobbin")
    img_url = _url_da_imagem(tela)
    baixar = baixar or _baixar_padrao

    tokens_cores = None
    if img_url:
        try:
            tokens_cores = extrair_paleta_imagem(baixar(img_url))
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
        "nao_extraido_da_imagem": ["tipografia", "espacamentos", "raios_borda"],
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


def _distancia_rgb(a: str, b: str) -> int:
    return sum(abs(int(a[i:i + 2], 16) - int(b[i:i + 2], 16)) for i in (1, 3, 5))


def extrair_tokens_de_telas(telas: List[Dict[str, Any]], baixar=None) -> Dict[str, Any]:
    """Agrega as telas de referência: a cor primária é a do maior grupo de cores parecidas (voto).

    Telas cuja imagem não baixa são ignoradas (não derrubam as outras). Tipografia, espaçamentos e raios
    são convenção do ecossistema: a imagem não informa fonte nem raio, e isso vem declarado no resultado.
    """
    baixar = baixar or _baixar_padrao
    paletas = []
    origem = []
    for tela in telas:
        url = _url_da_imagem(tela)
        if not url:
            continue
        try:
            paleta = extrair_paleta_imagem(baixar(url))
        except Exception:
            continue
        paletas.append(paleta)
        origem.append({"screen_id": tela.get("id"), "app_name": tela.get("app_name"), "mobbin_url": tela.get("mobbin_url")})

    if not paletas:
        base = extrair_tokens_mobbin({"app_name": "Referência Mobbin"}, baixar=lambda _u: b"")
        base["telas_analisadas"] = 0
        base["origem_referencias"] = []
        return base

    detectadas = [p for p in paletas if p.get("primaria_detectada")]
    if detectadas:
        primarias = [p["light"]["primary"] for p in detectadas]
        grupos = [[c for c in primarias if _distancia_rgb(c, centro) < 60] for centro in primarias]
        vencedora = max(grupos, key=len)[0]
        escolhida = next(p for p in detectadas if p["light"]["primary"] == vencedora)
    else:
        escolhida = paletas[0]  # nenhuma tela tem cor de marca: o neutro declarado, com primaria_detectada=False

    tokens = extrair_tokens_mobbin({**telas[0], "image": None, "image_url": None}, baixar=lambda _u: b"")
    tokens["cores"] = escolhida
    tokens["telas_analisadas"] = len(paletas)
    tokens["origem_referencias"] = origem
    return tokens
