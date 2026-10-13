# -*- coding: utf-8 -*-
"""Bloco Ambiente do planner (Mobbin em 3 caminhos e variáveis de deploy); fonte em src/core_planner."""

from src.core_planner.ambiente import (
    CAMINHOS_MOBBIN,
    VARIAVEIS_DEPLOY_OBRIGATORIAS,
    carregar_env,
    cmd_ambiente,
    detectar_harness,
    passo_a_passo_mcp,
    validar_chave_mobbin,
    variaveis_deploy_faltando,
    verificar,
)

__all__ = [
    "CAMINHOS_MOBBIN",
    "VARIAVEIS_DEPLOY_OBRIGATORIAS",
    "carregar_env",
    "cmd_ambiente",
    "detectar_harness",
    "passo_a_passo_mcp",
    "validar_chave_mobbin",
    "variaveis_deploy_faltando",
    "verificar",
]
