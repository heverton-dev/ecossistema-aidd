# -*- coding: utf-8 -*-
"""
Módulo de Fallback e Resiliência Operacional para aidd-tickets (Ticket 5 / D11 / DoD 4).
Permite recuperação tolerante a falhas diante de arquivos corrompidos ou entradas parciais.
"""

from __future__ import annotations

import re
from typing import List, Dict, Any, Tuple

try:
    import parser as tickets_parser
except ImportError:
    from . import parser as tickets_parser


def extrair_tickets_resiliente(texto: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    avisos = []
    # Checa blocos de texto descartados
    linhas = texto.strip().splitlines()
    linhas_com_lixo = [l for l in linhas if l.strip() and not l.strip().startswith("- **") and not l.strip().startswith("### [TICKET-")]
    if len(linhas_com_lixo) > 0:
        avisos.append(f"Detectadas {len(linhas_com_lixo)} linhas não conformes descartadas no fallback.")

    tickets_brutos, erros = tickets_parser.parsear_tickets_markdown(texto)
    if erros:
        avisos.extend(erros)

    tickets_recuperados = []
    for t in tickets_brutos:
        if t.get("target_files") and t.get("validation_command"):
            tickets_recuperados.append(t)
        else:
            avisos.append(f"Ticket '{t.get('id')}' descartado por campos incompletos no fallback.")

    return tickets_recuperados, avisos
