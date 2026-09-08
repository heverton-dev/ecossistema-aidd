# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD-Ops Intake Web — Núcleo Compartilhado (Anti-NIH #19)
=============================================================================
Exposição web do pipeline determinístico de infraestrutura (Fases 1-3).
Implementação ZERO-duplicação: delega ao builder único
pipeline_ops.montar_plano_em_memoria — o MESMO que o CLI executa. Nenhum
LLM, nenhuma lógica reescrita para o browser; o JSON baixado aqui é
idêntico ao PLANO-INFRAESTRUTURA.json gerado por
`python scripts/pipeline_ops.py plan`.
=============================================================================
"""

import json
import os
import sys

_APPS_DIR = os.path.dirname(os.path.abspath(__file__))
_TOOL_ROOT = os.path.dirname(os.path.dirname(_APPS_DIR))
sys.path.insert(0, os.path.join(_TOOL_ROOT, "scripts"))
sys.path.insert(0, os.path.join(_TOOL_ROOT, "src"))

from pipeline_ops import montar_plano_em_memoria  # noqa: E402

_DATA_DIR = os.path.join(_TOOL_ROOT, "data")


def _carregar_catalogo() -> dict:
    """Carrega catalogo_nichos.json (fonte única dos nichos)."""
    caminho = os.path.join(_DATA_DIR, "catalogo_nichos.json")
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def listar_nichos() -> list:
    """Lista os nichos disponíveis: lista de dicts {slug, nome_exibicao, ferramentas}."""
    return _carregar_catalogo().get("nichos", [])


def gerar_plano(texto: str, nicho_explicito: str = None) -> dict:
    """Gera o PLANO-INFRAESTRUTURA completo EM MEMÓRIA (mesma estrutura do CLI).

    Sempre retorna o dict do plano; em caso de falha de fase o próprio plano
    carrega `erro` no slot correspondente (ver `primeiro_erro`). Nunca lança.
    """
    texto = (texto or "").strip()
    if not texto and nicho_explicito:
        texto = nicho_explicito
    plano = montar_plano_em_memoria(texto, nicho_explicito=nicho_explicito).valor
    return plano


def primeiro_erro(plano: dict) -> dict:
    """Retorna o primeiro erro estruturado das fases 1-3, ou None."""
    for chave in ("fase_1_intake", "fase_2_curadoria", "fase_3_sizing"):
        erro = plano.get(chave, {}).get("erro")
        if erro:
            return erro
    return None


def plano_para_json(plano: dict) -> str:
    """Serializa o plano para JSON indentado (download no browser)."""
    return json.dumps(plano, indent=2, ensure_ascii=False)


__all__ = ["listar_nichos", "gerar_plano", "primeiro_erro", "plano_para_json"]