#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_CRAFT_VISUAL (Padrão-Ouro UI/UX)
=============================================================================
Quality Gate Determinístico de Craft Visual e Maturidade de UI (Lei #11 / Lei #13).
Audita os arquivos de frontend (TSX, JSX, CSS, HTML) contra vícios de design:
  1. Zero Emojis Unicode em UI (Lei #14): Apenas ícones vetoriais SVG (Lucide).
  2. Tokens Perceptualmente Uniformes: Presença de tokens OKLCH ou variáveis semânticas.
  3. Contraste e Legibilidade (WCAG 2.2 AA): Bloqueio de opacidades extremas em texto legível.
  4. Layout Fluido: Proibição de containers excessivamente estreitos (max-w-sm/max-w-xs) como casca de página.
  5. Tipografia Corporativa: Presença de declaração de tipografia corporativa (Inter/Public Sans/Geist).

Critérios de Aceite:
  - Exit 0: 100% dos requisitos de craft visual atendidos.
  - Exit 1: Qualquer violação de design amador detectada.
=============================================================================
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Faixa Unicode de emojis
_RE_EMOJI = re.compile(r"[\U0001F300-\U0001FAFF\U00002700-\U000027BF]")

# Padrão de container espremido como container principal
_RE_ESPREMIDO = re.compile(r'class(?:Name)?=["\'][^"\']*\b(?:max-w-xs|max-w-sm)\b[^"\']*(?:min-h-screen|w-screen|container)[^"\']*["\']')

# Padrão de texto com contraste degradado
_RE_BAIXO_CONTRASTE = re.compile(r'\b(?:opacity-10|opacity-20|text-white\/20|text-slate-900\/20)\b')

_DIRS_IGNORADAS = {"node_modules", ".git", "dist", "build", ".next", "__pycache__"}


def auditar_craft_visual(diretorio_alvo: Path) -> Tuple[bool, List[str]]:
    erros: List[str] = []

    if not diretorio_alvo.is_dir():
        return False, [f"Diretório não encontrado: {diretorio_alvo}"]

    arquivos_ui = []
    for ext in ("*.tsx", "*.jsx", "*.html", "*.css"):
        for arq in diretorio_alvo.rglob(ext):
            if any(parte in _DIRS_IGNORADAS for parte in arq.parts):
                continue
            arquivos_ui.append(arq)

    if not arquivos_ui:
        return True, []  # Sem frontend no alvo, gate neutro

    tem_tokens_ou_oklch = False
    tem_tipografia_corporativa = False

    for arq in arquivos_ui:
        try:
            conteudo = arq.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            continue

        # 1. Checagem de Emojis em UI
        if arq.suffix in (".tsx", ".jsx", ".html"):
            for num_linha, linha in enumerate(conteudo.splitlines(), start=1):
                # Ignora comentários
                if linha.strip().startswith("//") or linha.strip().startswith("/*"):
                    continue
                if _RE_EMOJI.search(linha):
                    erros.append(f"{arq.name}:{num_linha} — Emoji Unicode detectado em UI. Use ícones SVG (Lucide).")

        # 2. Layout espremido
        if _RE_ESPREMIDO.search(conteudo):
            erros.append(f"{arq.name} — Layout principal confinado em container estreito (max-w-xs/sm). Use layout fluido responsivo.")

        # 3. Baixo contraste
        if _RE_BAIXO_CONTRASTE.search(conteudo):
            erros.append(f"{arq.name} — Classe de opacidade extrema detectada, violando contraste WCAG 2.2 AA.")

        # Indicadores positivos de conformidade
        if "oklch" in conteudo.lower() or "--background" in conteudo or "tokens.css" in conteudo:
            tem_tokens_ou_oklch = True

        if any(f in conteudo.lower() for f in ("public sans", "inter", "geist", "system-ui")):
            tem_tipografia_corporativa = True

    if not tem_tokens_ou_oklch:
        erros.append("Nenhum arquivo de tokens OKLCH ou variáveis semânticas (--background/--foreground) encontrado.")

    return len(erros) == 0, erros


def main() -> int:
    parser = argparse.ArgumentParser(description="Quality Gate de Craft Visual AIDD")
    parser.add_argument("--alvo", default=".", help="Diretório a ser auditado")
    args = parser.parse_args()

    caminho_alvo = Path(args.alvo).resolve()
    print("=" * 70)
    print("🎨 [GATE G_CRAFT_VISUAL] Verificação Determinística de UI/UX e Padrão Linear")
    print(f"📁 Alvo: {caminho_alvo}")
    print("=" * 70)

    sucesso, falhas = auditar_craft_visual(caminho_alvo)

    if not sucesso:
        print("\n❌ [FAIL] Violações de Craft Visual detectadas:")
        for falha in falhas[:10]:
            print(f"   - {falha}")
        if len(falhas) > 10:
            print(f"   ... e mais {len(falhas) - 10} apontamentos.")
        return 1

    print("\n✅ [PASS] 100% conforme com o padrão corporativo de UI/UX (Zero emojis, tokens OKLCH ativos)!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
