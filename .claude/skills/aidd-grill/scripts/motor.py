# -*- coding: utf-8 -*-
"""
Motor de Validação de Recomendações e Justificativas para aidd-grill (Ticket 4 / D8 / DoD 3).
Exige conectivo causal e justificativa técnica explícita em cada recomendação.
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple, Any

CONECTIVOS_CAUSAIS = [
    re.compile(r"\bpor\s*que\b", re.IGNORECASE),
    re.compile(r"\bporque\b", re.IGNORECASE),
    re.compile(r"\bpois\b", re.IGNORECASE),
    re.compile(r"\bdevido\s*(?:a|ao|à|aos|às)\b", re.IGNORECASE),
    re.compile(r"\bvisto\s*que\b", re.IGNORECASE),
    re.compile(r"\bj[aá]\s*que\b", re.IGNORECASE),
    re.compile(r"\bbecause\b", re.IGNORECASE),
    re.compile(r"\bsince\b", re.IGNORECASE),
    re.compile(r"\bdue\s*to\b", re.IGNORECASE),
    re.compile(r"\bpara\s+garantir\b", re.IGNORECASE),
    re.compile(r"\bafim\s+de\b", re.IGNORECASE),
    re.compile(r"\bpara\s+evitar\b", re.IGNORECASE)
]


def validar_justificativa_recomendacao(recomendacao: str) -> Tuple[bool, str]:
    if not recomendacao or not recomendacao.strip():
        return False, "Recomendação vazia."

    tem_causal = any(p.search(recomendacao) for p in CONECTIVOS_CAUSAIS)
    if not tem_causal:
        return False, f"Recomendação '{recomendacao}' rejeitada por falta de justificativa causal técnica (deve conter 'porque', 'pois', 'because', etc.)."

    return True, ""


def validar_perguntas_socromaticas(perguntas: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], List[str]]:
    erros = []
    premissas_consolidadas = []

    for p in perguntas:
        rec = p.get("recomendacao")
        if not rec:
            erros.append(f"Pergunta {p['numero']} ('{p['titulo']}') está sem recomendação.")
            continue

        valido, motivo = validar_justificativa_recomendacao(rec)
        if not valido:
            erros.append(f"Pergunta {p['numero']}: {motivo}")
        else:
            premissas_consolidadas.append({
                "pergunta_id": p["numero"],
                "titulo": p["titulo"],
                "decisao_recomendada": rec
            })

    resumo = {
        "total_perguntas": len(perguntas),
        "total_validadas": len(premissas_consolidadas),
        "premissas_consolidadas": premissas_consolidadas
    }
    return resumo, erros
