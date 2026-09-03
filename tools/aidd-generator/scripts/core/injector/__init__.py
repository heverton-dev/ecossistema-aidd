#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Injetor Universal de Componentes — aidd-generator

Auto-injecao e auto-integracao de Skills, MCPs, Rules, Specs e Configs
neste projeto, seguindo a Seção 5 do plano mestre ORCA 3
(PLANO-ORQUESTRACAO-ORCA3-UNIVERSAL-INJECTOR.md).

Uso programatico:
    from scripts.core.injector.injetor import injetar

    resultado = injetar(nome="minha-skill", descricao="...", tipo="skill")
"""

from scripts.core.injector.injetor import ResultadoInjecao, injetar

__all__ = ["injetar", "ResultadoInjecao"]
