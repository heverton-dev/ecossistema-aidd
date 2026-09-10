# -*- coding: utf-8 -*-
"""
Facade de Rotas da fatia vertical modulo1 (compatibilidade com server.py).

Roteamento real agora vive em ``interfaces/routes.py``; este módulo apenas
repassa para o registrador de rotas da camada de Interfaces.
"""

from .interfaces.routes import registrar_rotas

__all__ = ["registrar_rotas"]