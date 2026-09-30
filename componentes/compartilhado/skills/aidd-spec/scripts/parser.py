# -*- coding: utf-8 -*-
"""
Parser Canônico de Especificação Técnica para aidd-spec (Ticket 3 / D4 / DoD 3).
Valida a presença obrigatória das 5 seções canônicas de especificação técnica.
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple, Any

SECOES_OBRIGATORIAS = [
    {
        "id": "contexto",
        "titulo": "Context & Explicit Non-Goals",
        "padrao": re.compile(r"##\s*(?:1\.?\s*)?(?:Context\s*&\s*Explicit\s*Non-Goals|Contexto\s*e\s*Non-Goals|Contexto)", re.IGNORECASE)
    },
    {
        "id": "contratos",
        "titulo": "Contracts & Typed Interfaces",
        "padrao": re.compile(r"##\s*(?:2\.?\s*)?(?:Contracts\s*&\s*Typed\s*Interfaces|Contratos\s*e\s*Interfaces|Contratos)", re.IGNORECASE)
    },
    {
        "id": "invariantes",
        "titulo": "Invariants & Business Rules",
        "padrao": re.compile(r"##\s*(?:3\.?\s*)?(?:Invariants\s*&\s*Business\s*Rules|Invariantes\s*e\s*Regras\s*de\s*Neg[oó]cio|Invariantes)", re.IGNORECASE)
    },
    {
        "id": "criterios_binarios",
        "titulo": "Binary Acceptance Criteria",
        "padrao": re.compile(r"##\s*(?:4\.?\s*)?(?:Binary\s*Acceptance\s*Criteria|Crit[eé]rios\s*de\s*Aceita[cç][aã]o\s*Bin[aá]rios|Crit[eé]rios\s*Bin[aá]rios)", re.IGNORECASE)
    },
    {
        "id": "modos_falha",
        "titulo": "Failure & Degradation Modes",
        "padrao": re.compile(r"##\s*(?:5\.?\s*)?(?:Failure\s*&\s*Degradation\s*Modes|Modos\s*de\s*Falha\s*e\s*Degrada[cç][aã]o|Modos\s*de\s*Falha)", re.IGNORECASE)
    }
]


def parsear_especificacao_markdown(texto: str) -> Tuple[Dict[str, Any], List[str]]:
    erros = []
    secoes_encontradas: Dict[str, str] = {}

    if not texto or not texto.strip():
        return {}, ["Documento de especificação vazio ou inexistente."]

    # Localiza o índice de início de cada seção
    posicoes = []
    for sec in SECOES_OBRIGATORIAS:
        match = sec["padrao"].search(texto)
        if match:
            posicoes.append((match.start(), sec["id"], sec["titulo"]))
        else:
            erros.append(f"Seção obrigatória ausente: '{sec['titulo']}'.")

    if erros:
        return {}, erros

    # Ordena as seções por ordem de aparição no documento
    posicoes.sort(key=lambda x: x[0])

    for i in range(len(posicoes)):
        start, sec_id, _ = posicoes[i]
        end = posicoes[i + 1][0] if i + 1 < len(posicoes) else len(texto)
        conteudo = texto[start:end].strip()
        secoes_encontradas[sec_id] = conteudo

    return secoes_encontradas, []
