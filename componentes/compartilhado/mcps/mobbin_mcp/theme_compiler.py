# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — GERADOR DE DESIGN SYSTEM DETERMINÍSTICO GLOBAL (DUAL MODE)
=============================================================================
Compila os tokens canônicos do Mobbin emitindo nativamente os blocos Light e Dark
(:root / data-theme="dark" / data-theme="light") para garantir suporte universal.
"""

import json
from pathlib import Path
from typing import Any, Dict


def compilar_contrato_design(tokens: Dict[str, Any], saida_dir: Path) -> Dict[str, Path]:
    """
    Grava os artefatos canônicos do Design System com suporte nativo a Light e Dark:
    1. theme-tokens.json
    2. design-system.css
    """
    saida_dir.mkdir(parents=True, exist_ok=True)
    json_path = saida_dir / "theme-tokens.json"
    css_path = saida_dir / "design-system.css"

    cores = tokens.get("cores", {})
    modo_nativo = cores.get("modo_nativo_referencia", "dark")

    # Suporte tanto à nova estrutura dual quanto à legada
    t_light = cores.get("light") or {
        "background": "#f8fafc",
        "surface": "#ffffff",
        "primary": cores.get("primary", "#2563eb"),
        "foreground": "#0f172a",
        "muted": "#64748b",
        "border": "rgba(0, 0, 0, 0.08)"
    }

    t_dark = cores.get("dark") or {
        "background": cores.get("background", "#0d1117"),
        "surface": cores.get("surface", "#161b22"),
        "primary": cores.get("primary", "#3b82f6"),
        "foreground": cores.get("foreground", "#f0f6fc"),
        "muted": cores.get("muted", "#8b949e"),
        "border": cores.get("border", "rgba(255, 255, 255, 0.12)")
    }

    tipo = tokens.get("tipografia", {})
    escala = tipo.get("escala", {})
    espacos = tokens.get("espacamentos", {})
    raios = tokens.get("raios_borda", {})

    # 1. Grava JSON estruturado canônico
    json_path.write_text(json.dumps(tokens, indent=2, ensure_ascii=False), encoding="utf-8")

    # Define o tema padrão inicial no :root baseado no modo nativo da referência
    def_padrao = t_dark if modo_nativo == "dark" else t_light

    # 2. Gera CSS com suporte nativo dual
    css_conteudo = f"""/* ==========================================================================
   CONTRATO CANÔNICO DE DESIGN SYSTEM — ECOSSISTEMA AIDD (CAMADA 1 DUAL)
   Origem da Referência: {tokens.get('origem_referencia', {}).get('app_name', 'Mobbin')}
   ID: {tokens.get('origem_referencia', {}).get('screen_id', 'n/a')}
   Modo Nativo: {modo_nativo.upper()}
   ========================================================================== */

:root {{
  /* Cores Padrão (Base: {modo_nativo}) */
  --bg-app: {def_padrao.get('background')};
  --bg-surface: {def_padrao.get('surface')};
  --color-primary: {def_padrao.get('primary')};
  --color-foreground: {def_padrao.get('foreground')};
  --color-muted: {def_padrao.get('muted')};
  --color-border: {def_padrao.get('border')};

  /* Tipografia Nativa */
  --font-family-sans: {tipo.get('font_sans', 'system-ui, sans-serif')};
  --font-family-mono: {tipo.get('font_mono', 'monospace')};

  /* Escala Modular Tipográfica */
  --font-size-xs: {escala.get('xs', '11px')};
  --font-size-sm: {escala.get('sm', '12px')};
  --font-size-base: {escala.get('base', '14px')};
  --font-size-md: {escala.get('md', '16px')};
  --font-size-lg: {escala.get('lg', '18px')};
  --font-size-xl: {escala.get('xl', '24px')};
  --font-size-2xl: {escala.get('2xl', '32px')};
  --font-size-hero: {escala.get('hero', '44px')};

  /* Espaçamentos e Grid */
  --spacing-base: {espacos.get('grid_base', '4px')};
  --spacing-container: {espacos.get('padding_container', '24px')};
  --spacing-gap-sections: {espacos.get('gap_secoes', '32px')};
  --spacing-gap-elements: {espacos.get('gap_elementos', '16px')};

  /* Raios de Borda */
  --radius-btn: {raios.get('btn', '6px')};
  --radius-card: {raios.get('card', '8px')};
  --radius-pill: {raios.get('pill', '9999px')};

  /* Engenharia Mobile & PWA (Safe Areas e Touch Targets) */
  --touch-target-min: 48px;
  --safe-area-top: env(safe-area-inset-top, 0px);
  --safe-area-bottom: env(safe-area-inset-bottom, 0px);
}}

/* Sobrescritas Explícitas de Tema */
:root[data-theme="light"],
body[data-theme="light"] {{
  --bg-app: {t_light.get('background')};
  --bg-surface: {t_light.get('surface')};
  --color-primary: {t_light.get('primary')};
  --color-foreground: {t_light.get('foreground')};
  --color-muted: {t_light.get('muted')};
  --color-border: {t_light.get('border')};
}}

:root[data-theme="dark"],
body[data-theme="dark"] {{
  --bg-app: {t_dark.get('background')};
  --bg-surface: {t_dark.get('surface')};
  --color-primary: {t_dark.get('primary')};
  --color-foreground: {t_dark.get('foreground')};
  --color-muted: {t_dark.get('muted')};
  --color-border: {t_dark.get('border')};
}}

/* Preferência do Sistema Operacional */
@media (prefers-color-scheme: light) {{
  :root:not([data-theme="dark"]) {{
    --bg-app: {t_light.get('background')};
    --bg-surface: {t_light.get('surface')};
    --color-primary: {t_light.get('primary')};
    --color-foreground: {t_light.get('foreground')};
    --color-muted: {t_light.get('muted')};
    --color-border: {t_light.get('border')};
  }}
}}

@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --bg-app: {t_dark.get('background')};
    --bg-surface: {t_dark.get('surface')};
    --color-primary: {t_dark.get('primary')};
    --color-foreground: {t_dark.get('foreground')};
    --color-muted: {t_dark.get('muted')};
    --color-border: {t_dark.get('border')};
  }}
}}

/* Reset e Base Global */
body {{
  background-color: var(--bg-app);
  color: var(--color-foreground);
  font-family: var(--font-family-sans);
  margin: 0;
  padding: 0;
  -webkit-font-smoothing: antialiased;
  transition: background-color 0.15s ease, color 0.15s ease;
}}

/* Botão Primário com Estados Canônicos de Produção */
.btn-primary {{
  background-color: var(--color-primary);
  color: #ffffff;
  border-radius: var(--radius-btn);
  padding: 8px 16px;
  font-size: var(--font-size-base);
  font-weight: 600;
  border: 1px solid transparent;
  cursor: pointer;
  transition: opacity 0.15s ease, transform 0.05s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}}

.btn-primary:hover {{
  opacity: 0.9;
}}

.btn-primary:active {{
  transform: scale(0.98);
}}

.btn-primary:focus-visible {{
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}}
"""
    css_path.write_text(css_conteudo, encoding="utf-8")

    return {
        "json": json_path,
        "css": css_path
    }
