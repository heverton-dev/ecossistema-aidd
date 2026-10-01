# -*- coding: utf-8 -*-
"""
Parser Canônico de Rodadas Socráticas para aidd-grill (Ticket 3 / D4 / DoD 3).
Extrai perguntas numeradas e blocos de recomendação justificada.
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple, Any

RE_PERGUNTA = re.compile(
    r"^(?:###\s*)?(?:Pergunta\s*)?(\d+)[\.\)]\s*(.+)$",
    re.MULTILINE | re.IGNORECASE
)

RE_RECOMENDACAO = re.compile(
    r"(?:\*\*)?(?:Recomendad[oa]|Recommended)(?:\*\*)?:\s*([^\n\r]+)",
    re.IGNORECASE
)


def parsear_rodada_socratica(texto: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    erros = []
    perguntas: List[Dict[str, Any]] = []

    if not texto or not texto.strip():
        return [], ["Entrada socrática vazia ou inexistente."]

    # Divide por blocos de pergunta numerada
    linhas = texto.splitlines()
    bloco_atual = None
    blocos_perguntas = []

    for linha in linhas:
        match_p = RE_PERGUNTA.match(linha.strip())
        if match_p:
            if bloco_atual:
                blocos_perguntas.append(bloco_atual)
            bloco_atual = {
                "numero": int(match_p.group(1)),
                "titulo": match_p.group(2).strip(),
                "linhas": []
            }
        elif bloco_atual:
            bloco_atual["linhas"].append(linha)

    if bloco_atual:
        blocos_perguntas.append(bloco_atual)

    if not blocos_perguntas:
        erros.append("Nenhuma pergunta numerada (1, 2, 3...) encontrada na rodada socrática.")
        return [], erros

    for bp in blocos_perguntas:
        corpo = "\n".join(bp["linhas"]).strip()
        match_rec = RE_RECOMENDACAO.search(corpo)
        
        recomendacao = match_rec.group(1).strip() if match_rec else None
        if not recomendacao:
            erros.append(f"Pergunta {bp['numero']} não contém resposta recomendada explícita ('Recomendado: <resposta>, porque <motivo>').")

        # Extrai opções sugeridas (se houver bullets com - [A-Z] ou similar)
        opcoes = []
        for l in bp["linhas"]:
            l_strip = l.strip()
            if re.match(r"^[-*]\s*(?:\([a-zA-Z0-9]\)|[a-zA-Z0-9]\))\s*", l_strip):
                opcoes.append(l_strip)

        perguntas.append({
            "numero": bp["numero"],
            "titulo": bp["titulo"],
            "corpo": corpo,
            "opcoes": opcoes,
            "recomendacao": recomendacao
        })

    return perguntas, erros
