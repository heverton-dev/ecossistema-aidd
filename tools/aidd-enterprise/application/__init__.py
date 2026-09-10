# -*- coding: utf-8 -*-
"""
Camada de Aplicação do AIDD Master (Item 03 — extrair-camada-aplicacao-dos-clis-master-enterprise).

A camada de aplicação concentra os Use Cases de cada comando da CLI em
application/commands/, deixando scripts/aidd.py como casca fina de parsing
(argparse/Click) sem lógica de negócio.
"""

__all__ = ["commands"]