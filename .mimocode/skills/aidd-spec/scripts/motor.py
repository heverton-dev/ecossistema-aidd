# -*- coding: utf-8 -*-
"""
Motor de Validação de Critérios Binários e Invariantes para aidd-spec (Ticket 4 / D8 / DoD 3).
Verifica a objetividade mecânica dos critérios de aceitação e a enumeração das invariantes.
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple, Any

PADROES_MECANICOS = [
    re.compile(r"\bexit\s*(?:code\s*)?[01]\b", re.IGNORECASE),
    re.compile(r"\bstatus\s*(?:code\s*)?[1-5]\d\d\b", re.IGNORECASE),
    re.compile(r"\bHTTP\s*[1-5]\d\d\b", re.IGNORECASE),
    re.compile(r"\bassert\b", re.IGNORECASE),
    re.compile(r"\bpytest\b|\btest_\w+\b", re.IGNORECASE),
    re.compile(r"\b(?:retorna|retorne|raises?|lan[cç]a)\s+(?:True|False|None|\w+Error|\w+Exception)\b", re.IGNORECASE),
    re.compile(r"[<>!=]=?\s*\d+(?:\.\d+)?\s*(?:ms|s|seg|bytes|kb|mb|%)", re.IGNORECASE),
    re.compile(r"\b(?:deve\s+conter|deve\s+existir|chave\s+obrigat[oó]ria|schema\s+v[aá]lido)\b", re.IGNORECASE)
]

TERMOS_SUBJETIVOS_PROIBIDOS = [
    re.compile(r"\b(?:deve\s+ser\s+r[aá]pido|sistema\s+[aá]gil|interface\s+bonita|f[aá]cil\s+de\s+usar|c[oó]digo\s+limpo|amig[aá]vel)\b", re.IGNORECASE)
]


def extrair_invariantes(conteudo_invariantes: str) -> List[str]:
    invariantes = []
    for linha in conteudo_invariantes.splitlines():
        linha_limpa = linha.strip()
        if re.match(r"^(?:\d+[\.\)]|\-\s*\*{0,2}INV\d+)\s*", linha_limpa):
            invariantes.append(linha_limpa)
    return invariantes


def extrair_criterios_binarios(conteudo_criterios: str) -> Tuple[List[str], List[str]]:
    criterios = []
    erros = []
    
    linhas = conteudo_criterios.splitlines()
    for linha in linhas:
        linha_limpa = linha.strip()
        if linha_limpa.startswith("-") or re.match(r"^\d+[\.\)]", linha_limpa):
            item = re.sub(r"^(?:[\-\*]|\d+[\.\)])\s*", "", linha_limpa).strip()
            if not item:
                continue
            
            # Checa proibição de subjetividade sem condição mecânica
            tem_subjetivo = any(p.search(item) for p in TERMOS_SUBJETIVOS_PROIBIDOS)
            tem_mecanico = any(p.search(item) for p in PADROES_MECANICOS)

            if tem_subjetivo and not tem_mecanico:
                erros.append(f"Critério subjetivo rejeitado sem condição mecânica: '{item}'.")
            elif not tem_mecanico:
                erros.append(f"Critério não verificável mecanicamente: '{item}'. Deve conter condição binária explícita (exit code, status HTTP, assert, métrica com unidade).")
            else:
                criterios.append(item)

    if not criterios and not erros:
        erros.append("Nenhum critério de aceitação binário listado.")

    return criterios, erros


def validar_regras_especificacao(secoes: Dict[str, str]) -> Tuple[Dict[str, Any], List[str]]:
    erros = []
    invariantes = extrair_invariantes(secoes.get("invariantes", ""))
    if not invariantes:
        erros.append("Seção de invariantes não contém regras numeradas ou identificadas.")

    criterios, erros_crit = extrair_criterios_binarios(secoes.get("criterios_binarios", ""))
    if erros_crit:
        erros.extend(erros_crit)

    resumo = {
        "total_invariantes": len(invariantes),
        "invariantes": invariantes,
        "total_criterios_binarios": len(criterios),
        "criterios_binarios": criterios
    }
    return resumo, erros
