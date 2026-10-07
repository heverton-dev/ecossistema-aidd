# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — CLIENTE E CLI UNIVERSAL DO MOBBIN ENTERPRISE
=============================================================================
Permite busca determinística de telas do Mobbin via API REST oficial
(POST /v1/screens/search) para consumo agnóstico por qualquer harness
(Claude, OpenCode, MiMo, Goose, Copilot, etc.) ou esteira de planejamento.

Consome MOBBIN_API_KEY e MOBBIN_API_URL centralizados no .env raiz.
"""

from src.core_planner.mobbin_client import (
    obter_config,
    executar_busca,
    cmd_status,
    cmd_search,
    main,
)

__all__ = [
    "obter_config",
    "executar_busca",
    "cmd_status",
    "cmd_search",
    "main",
]
