# -*- coding: utf-8 -*-
"""
Módulo de Fallback e Resiliência Operacional Headless para aidd-grill (Ticket 5 / D11 / DoD 4).
Sintetiza deterministicamente premissas consolidadas em execuções headless ou em lote.
"""

from __future__ import annotations

from typing import Dict, List, Tuple, Any

try:
    import parser as grill_parser
    import motor as grill_motor
except ImportError:
    from . import parser as grill_parser
    from . import motor as grill_motor


def sintetizar_premissas_headless(texto: str) -> Tuple[str, List[Dict[str, Any]], List[str]]:
    perguntas, erros = grill_parser.parsear_rodada_socratica(texto)
    avisos = list(erros)

    linhas_premissas = ["### Consolidated Assumptions\n"]
    premissas_estruturadas = []

    for p in perguntas:
        rec = p.get("recomendacao")
        if not rec:
            rec = "Aceite padrão de arquitetura, para evitar bloqueio do pipeline"
            avisos.append(f"Pergunta {p['numero']} sem recomendação; premissa de contingência gerada.")
        elif not grill_motor.validar_justificativa_recomendacao(rec)[0]:
            rec = f"{rec} (porque é a recomendação padrão de menor raio de impacto)"
            avisos.append(f"Pergunta {p['numero']}: justificativa adicionada por contingência.")

        linha_premissa = f"{p['numero']}. **{p['titulo']}**: {rec}"
        linhas_premissas.append(linha_premissa)
        premissas_estruturadas.append({
            "numero": p["numero"],
            "titulo": p["titulo"],
            "premissa_assumida": rec
        })

    bloco_markdown = "\n".join(linhas_premissas)
    return bloco_markdown, premissas_estruturadas, avisos
