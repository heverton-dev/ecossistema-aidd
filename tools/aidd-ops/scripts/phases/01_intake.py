# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD-Ops MVP — Fase 1: Intake & Reconhecimento de Nicho
=============================================================================
Reconhece o nicho de mercado a partir de texto livre em PT-BR ou de um
slug explícito (bypass). Casamento de palavras-chave contra
data/catalogo_nichos.json, seguindo o padrão determinístico de
tools/aidd-master/src/core/detector_camada.py (nunca LLM, nunca escolha
silenciosa).

Resultados possíveis:
  - 1 nicho bate   → Result.ok(nicho)
  - 0 nichos batem → Result.fail(NICHO_NAO_RECONHECIDO)
  - 2+ nichos batem → Result.fail(NICHO_AMBIGUO, candidatos=[...])
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from core.result import Result

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")


def _normalizar(texto: str) -> str:
    """Remove acentos e baixa a caixa, preservando espaços e hífens."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return sem_acento.lower().strip()


def _carregar_catalogo() -> Dict[str, Any]:
    """Carrega catalogo_nichos.json como dict."""
    caminho = os.path.join(_DATA_DIR, "catalogo_nichos.json")
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def reconhecer_nicho(texto_ou_nicho: str, nicho_explicito: Optional[str] = None) -> Result:
    """Reconhece o nicho de mercado a partir de texto livre ou slug explícito.

    Args:
        texto_ou_nicho: Texto livre em PT-BR ou slug de nicho.
        nicho_explicito: Se fornecido, bypass do reconhecimento por texto
                         (ex.: --nicho clinicas).

    Returns:
        Result.ok(dados_do_nicho) ou Result.fail com código apropriado.
    """
    catalogo = _carregar_catalogo()
    nichos = catalogo.get("nichos", [])

    # Construir dict slug -> nicho
    mapa_slugs: Dict[str, Dict[str, Any]] = {n["slug"]: n for n in nichos}

    # Bypass: nicho explícito
    if nicho_explicito is not None:
        slug = nicho_explicito.lower().strip()
        if slug in mapa_slugs:
            nicho = mapa_slugs[slug]
            return Result.ok({
                "nicho_slug": nicho["slug"],
                "nicho_nome_exibicao": nicho["nome_exibicao"],
                "texto_original": texto_ou_nicho,
                "palavras_chave_candidatas": [],
            })
        return Result.fail(
            f"Nicho explícito '{nicho_explicito}' não encontrado no catálogo. "
            f"Slugs válidos: {', '.join(sorted(mapa_slugs.keys()))}",
            codigo="NICHO_NAO_RECONHECIDO",
            detalhes={"nicho_informado": nicho_explicito, "slugs_validos": sorted(mapa_slugs.keys())},
        )

    # Casamento por palavras-chave
    texto_norm = _normalizar(texto_ou_nicho)
    if not texto_norm:
        return Result.fail(
            "Texto de entrada vazio. Forneça um texto descritivo ou use --nicho <slug>.",
            codigo="NICHO_NAO_RECONHECIDO",
        )

    bateres: Dict[str, List[str]] = {}  # slug -> lista de palavras-chave que bateram
    for nicho in nichos:
        slug = nicho["slug"]
        palavras_que_bateram = []
        for palavra_chave in nicho.get("palavras_chave", []):
            # Normalizar a palavra-chave
            pc_norm = _normalizar(palavra_chave)
            # Casamento: a palavra-chave normalizada aparece no texto normalizado
            # ou o texto contém a palavra-chave como substring
            if pc_norm in texto_norm:
                palavras_que_bateram.append(palavra_chave)
        if palavras_que_bateram:
            bateres[slug] = palavras_que_bateram

    if len(bateres) == 0:
        candidatos_slugs = [n["slug"] for n in nichos]
        return Result.fail(
            f"Nenhum nicho reconhecido no texto: '{texto_ou_nicho}'",
            codigo="NICHO_NAO_RECONHECIDO",
            detalhes={
                "texto": texto_ou_nicho,
                "slugs_disponiveis": candidatos_slugs,
            },
        )

    if len(bateres) > 1:
        candidatos = []
        for slug, palavras in bateres.items():
            nicho = mapa_slugs[slug]
            candidatos.append({
                "slug": slug,
                "nome_exibicao": nicho["nome_exibicao"],
                "palavras_bateram": palavras,
            })
        return Result.fail(
            f"Texto bate com mais de 1 nicho — selecione explicitamente com --nicho <slug>.",
            codigo="NICHO_AMBIGUO",
            detalhes={"candidatos": candidatos},
        )

    # Exatamente 1 nicho
    slug_unico = list(bateres.keys())[0]
    nicho = mapa_slugs[slug_unico]
    return Result.ok({
        "nicho_slug": nicho["slug"],
        "nicho_nome_exibicao": nicho["nome_exibicao"],
        "texto_original": texto_ou_nicho,
        "palavras_chave_candidatas": bateres[slug_unico],
    })
