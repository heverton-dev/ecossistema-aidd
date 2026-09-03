"""Detector de camada AIDD (heuristica deterministica, zero LLM).

Mapeia cada `tipo` de componente injetavel para a camada arquitetural AIDD
(1 a 5) a que pertence. E uma heuristica pura por dicionario: dado o conjunto
fechado de tipos suportados pelo `FORGE_PROFILE`, nao ha ambiguidade que
justifique delegar a decisao a um LLM dentro do motor mecanico — qualquer
divergencia explicita vinda do chamador (`camada_alvo`) e tratada como erro
determinístico, nao como uma segunda opiniao a arbitrar.
"""

from __future__ import annotations

TIPO_PARA_CAMADA: dict[str, int] = {
    "rule": 1,
    "spec": 2,
    "mcp": 4,
    "skill": 5,
    "roteiro": 5,
}


class CamadaConflitanteError(ValueError):
    """Levantado quando `camada_alvo` explicito diverge da camada canonica do tipo."""


def detectar_camada(tipo: str, camada_alvo: int | None = None) -> int:
    """Resolve a camada AIDD de `tipo`; valida `camada_alvo` se fornecido."""
    if tipo not in TIPO_PARA_CAMADA:
        raise ValueError(f"tipo '{tipo}' nao possui camada mapeada")

    camada_canonica = TIPO_PARA_CAMADA[tipo]

    if camada_alvo is not None and camada_alvo != camada_canonica:
        raise CamadaConflitanteError(
            f"tipo '{tipo}' pertence a camada {camada_canonica}, "
            f"mas 'camada_alvo={camada_alvo}' foi solicitado"
        )

    return camada_canonica
