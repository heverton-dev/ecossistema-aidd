# -*- coding: utf-8 -*-
"""
Facade de Schema da fatia vertical modulo1 (compatibilidade com server.py).

A definição real do DDL agora vive em ``infrastructure/schema.py``; este
módulo apenas re-exporta ``init_schema`` para preservar o contrato público
``modules.modulo1.models.init_schema(conn)`` usado pelo servidor e testes.
"""

from .infrastructure.schema import init_schema

__all__ = ["init_schema"]