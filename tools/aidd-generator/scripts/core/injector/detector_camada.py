#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DETECTOR DE CAMADA — Deteccao hibrida de tipo/camada do componente
aidd-generator — Injetor Universal de Componentes

Infere `tipo` (skill/mcp/rule/spec/config) e `camada_alvo` (1-5, metodologia
AIDD) a partir de uma descricao em linguagem natural (PT-BR), quando o
chamador nao os informa explicitamente.

Estrategia hibrida:
  1. Heuristica determinista por palavras-chave (mesmo estilo de scoring
     usado por `scripts/phases/utils_intent_router.py`) — zero LLM, zero custo.
  2. Fallback delegado (`solicitar_llm`, de `scripts/phases/utils_delegacao.py`)
     apenas quando a heuristica fica abaixo do limiar de confianca.
"""

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

_PHASES_DIR = Path(__file__).resolve().parent.parent.parent / 'phases'
if str(_PHASES_DIR) not in sys.path:
    sys.path.insert(0, str(_PHASES_DIR))


LIMIAR_CONFIANCA_PADRAO = 0.55

# Mapa default de camada AIDD (1-5) sugerida por tipo de componente.
# Auxiliar/sugestivo — o chamador pode sempre sobrescrever via payload.
CAMADA_PADRAO_POR_TIPO: Dict[str, str] = {
    "spec": "1",     # Contratos e Schemas
    "config": "1",   # Contratos e Schemas
    "mcp": "2",      # Determinismo Primeiro
    "rule": "3",     # Gates Mecanicos
    "skill": "5",    # Bundles Modulares
}

# tipo -> lista de (regex, peso)
_PALAVRAS_CHAVE: Dict[str, List[Tuple[str, float]]] = {
    "mcp": [
        (r"\bmcp\b", 1.0),
        (r"model\s+context\s+protocol", 1.0),
        (r"servidor\s+mcp", 1.0),
        (r"tool\s*server", 0.6),
        (r"integra(?:ç|c)[aã]o\s+com\s+(?:api|ferramenta)\s+externa", 0.5),
    ],
    "skill": [
        (r"\bskill\b", 1.0),
        (r"habilidade", 0.8),
        (r"playbook", 0.6),
        (r"modo\s+de\s+trabalho", 0.5),
        (r"fluxo\s+de\s+trabalho\s+reutiliz[aá]vel", 0.5),
    ],
    "rule": [
        (r"\bregra\b", 1.0),
        (r"\brule\b", 1.0),
        (r"pol[ií]tica", 0.7),
        (r"diretriz", 0.6),
        (r"conven(?:ç|c)[aã]o\s+obrigat[oó]ria", 0.6),
    ],
    "spec": [
        (r"\bspec\b", 1.0),
        (r"especifica(?:ç|c)[aã]o", 1.0),
        (r"documento\s+t[eé]cnico", 0.6),
        (r"design\s+doc", 0.6),
    ],
    "config": [
        (r"\bconfig(?:ura(?:ç|c)[aã]o)?\b", 1.0),
        (r"arquivo\s+de\s+configura(?:ç|c)[aã]o", 1.0),
        (r"settings", 0.6),
        (r"par[aâ]metros", 0.4),
    ],
}


@dataclass
class ResultadoDeteccao:
    """Resultado da deteccao hibrida de tipo/camada."""

    tipo: Optional[str] = None
    camada_alvo: Optional[str] = None
    confianca: float = 0.0
    origem: str = "heuristica"  # 'heuristica' ou 'llm'
    scores: Dict[str, float] = field(default_factory=dict)


def _pontuar_heuristica(descricao: str) -> Dict[str, float]:
    """Pontua cada tipo candidato contra a descricao, via regex ponderado."""
    texto = (descricao or "").lower()
    scores: Dict[str, float] = {tipo: 0.0 for tipo in _PALAVRAS_CHAVE}

    for tipo, padroes in _PALAVRAS_CHAVE.items():
        pontos = 0.0
        for padrao, peso in padroes:
            if re.search(padrao, texto, re.IGNORECASE):
                pontos += peso
        scores[tipo] = min(pontos, 1.0)

    return scores


def detectar_tipo(
    descricao: str,
    tipo_hint: Optional[str] = None,
    limiar_confianca: float = LIMIAR_CONFIANCA_PADRAO,
    chamar_llm: Optional[Callable[[str], Optional[str]]] = None,
) -> ResultadoDeteccao:
    """
    Detecta o tipo (e camada AIDD sugerida) de um componente a partir da
    descricao em linguagem natural.

    Args:
        descricao: texto livre descrevendo o componente desejado.
        tipo_hint: se informado e valido, e usado diretamente (confianca 1.0,
            origem 'explicito') sem rodar heuristica/LLM.
        limiar_confianca: score minimo (0.0-1.0) para aceitar a heuristica
            sem cair no fallback delegado.
        chamar_llm: funcao opcional `(prompt) -> resposta_tipo_str | None`
            usada como fallback quando a heuristica for ambigua. Se None,
            usa `solicitar_llm` de `utils_delegacao` sob demanda (import
            tardio para nao forcar a dependencia em caminhos puramente
            heuristicos/testes).

    Returns:
        ResultadoDeteccao com `tipo` (pode ser None se nada foi decidido).
    """
    from .contrato import TIPOS_VALIDOS

    if tipo_hint and tipo_hint in TIPOS_VALIDOS:
        return ResultadoDeteccao(
            tipo=tipo_hint,
            camada_alvo=CAMADA_PADRAO_POR_TIPO.get(tipo_hint),
            confianca=1.0,
            origem="explicito",
            scores={},
        )

    scores = _pontuar_heuristica(descricao)
    tipo_top = max(scores, key=scores.get)
    score_top = scores[tipo_top]

    if score_top >= limiar_confianca:
        return ResultadoDeteccao(
            tipo=tipo_top,
            camada_alvo=CAMADA_PADRAO_POR_TIPO.get(tipo_top),
            confianca=score_top,
            origem="heuristica",
            scores=scores,
        )

    # Fallback delegado — heuristica ambigua.
    resposta_llm = _consultar_llm_fallback(descricao, scores, chamar_llm)
    if resposta_llm in TIPOS_VALIDOS:
        return ResultadoDeteccao(
            tipo=resposta_llm,
            camada_alvo=CAMADA_PADRAO_POR_TIPO.get(resposta_llm),
            confianca=max(score_top, 0.5),
            origem="llm",
            scores=scores,
        )

    # Nenhuma decisao confiavel — devolve o melhor palpite heuristico mesmo
    # abaixo do limiar, marcado com confianca real, para o chamador decidir.
    return ResultadoDeteccao(
        tipo=tipo_top if score_top > 0 else None,
        camada_alvo=CAMADA_PADRAO_POR_TIPO.get(tipo_top) if score_top > 0 else None,
        confianca=score_top,
        origem="heuristica",
        scores=scores,
    )


def _consultar_llm_fallback(
    descricao: str,
    scores: Dict[str, float],
    chamar_llm: Optional[Callable[[str], Optional[str]]],
) -> Optional[str]:
    """Executa o fallback delegado, isolando a dependencia opcional em utils_delegacao."""
    from .contrato import TIPOS_VALIDOS

    prompt = (
        "Classifique o componente descrito abaixo em exatamente um destes tipos: "
        f"{', '.join(TIPOS_VALIDOS)}.\n"
        f"Descricao: {descricao}\n"
        "Responda APENAS com a palavra do tipo, em minusculas, sem explicacao."
    )

    if chamar_llm is not None:
        resposta = chamar_llm(prompt)
        return resposta.strip().lower() if resposta else None

    try:
        from utils_delegacao import solicitar_llm
    except ImportError:
        return None

    resultado = solicitar_llm(prompt=prompt, contexto="Injetor: deteccao de tipo ambigua", fase="injector_detector")
    if not resultado or not resultado.get("conteudo"):
        return None

    return str(resultado["conteudo"]).strip().lower()
