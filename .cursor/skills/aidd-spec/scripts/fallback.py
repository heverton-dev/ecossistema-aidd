# -*- coding: utf-8 -*-
"""
Módulo de Fallback e Resiliência Operacional para aidd-spec (Ticket 5 / D11 / DoD 4).
Permite recuperação tolerante a falhas diante de arquivos com encoding corrompido ou seções truncadas.
"""

from __future__ import annotations

from typing import Dict, List, Tuple, Any

try:
    import parser as spec_parser
    import motor as spec_motor
except ImportError:
    from . import parser as spec_parser
    from . import motor as spec_motor


def extrair_spec_resiliente(texto: str) -> Tuple[Dict[str, Any], List[str]]:
    avisos = []
    
    # Tratamento de linhas nulas ou bytes corrompidos
    linhas = [l for l in texto.splitlines() if "\x00" not in l]
    texto_limpo = "\n".join(linhas)

    # Tenta parsing padrão
    secoes_presentes: Dict[str, str] = {}
    posicoes = []
    for sec in spec_parser.SECOES_OBRIGATORIAS:
        match = sec["padrao"].search(texto_limpo)
        if match:
            posicoes.append((match.start(), sec["id"], sec["titulo"]))
        else:
            avisos.append(f"Seção '{sec['titulo']}' ausente ou ilegível na entrada corrompida.")

    posicoes.sort(key=lambda x: x[0])
    for i in range(len(posicoes)):
        start, sec_id, _ = posicoes[i]
        end = posicoes[i + 1][0] if i + 1 < len(posicoes) else len(texto_limpo)
        secoes_presentes[sec_id] = texto_limpo[start:end].strip()

    dados_resilientes = {
        "secoes_presentes": list(secoes_presentes.keys()),
        "conteudo_parcial": secoes_presentes
    }

    if "invariantes" in secoes_presentes:
        invars = spec_motor.extrair_invariantes(secoes_presentes["invariantes"])
        dados_resilientes["invariantes"] = invars
    else:
        dados_resilientes["invariantes"] = []
        avisos.append("Invariantes não puderam ser recuperadas na íntegra.")

    if "criterios_binarios" in secoes_presentes:
        crits, erros_c = spec_motor.extrair_criterios_binarios(secoes_presentes["criterios_binarios"])
        dados_resilientes["criterios_binarios"] = crits
        if erros_c:
            avisos.extend(erros_c)
    else:
        dados_resilientes["criterios_binarios"] = []
        avisos.append("Critérios binários ausentes na entrada corrompida.")

    return dados_resilientes, avisos
