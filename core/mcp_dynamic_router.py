# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — MCP DYNAMIC ROUTER & SCHEMA UNLOADER
=============================================================================
Fachada centralizada de ferramentas MCP com descarregamento de schemas.
Em vez de registrar dezenas de ferramentas no boot do harness (o que consome
milhares de tokens fixos no system prompt), expoe apenas 2 funcoes essenciais:
  1. aidd_dispatch(tool_name, arguments)
  2. aidd_query_schema(tool_name)
"""

from typing import Any, Callable, Dict, List, Optional


class MCPDynamicRouter:
    """Roteador sob demanda de ferramentas e schemas MCP."""

    def __init__(self):
        self._tools_registry: Dict[str, Dict[str, Any]] = {}
        self._handlers: Dict[str, Callable[..., Any]] = {}

    def register_tool(self, name: str, description: str, schema: Dict[str, Any], handler: Callable[..., Any]) -> None:
        """Registra uma ferramenta no catalogo lazy sem poluir o system prompt."""
        self._tools_registry[name] = {
            "name": name,
            "description": description,
            "schema": schema
        }
        self._handlers[name] = handler

    def list_tool_names(self) -> List[str]:
        """Retorna apenas os identificadores das ferramentas disponiveis."""
        return list(self._tools_registry.keys())

    def get_tool_schema(self, name: str) -> Optional[Dict[str, Any]]:
        """Entrega o schema JSON de uma ferramenta especifica sob demanda estrita."""
        return self._tools_registry.get(name)

    def dispatch(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Executa a ferramenta sob demanda pelo nome."""
        handler = self._handlers.get(tool_name)
        if not handler:
            raise ValueError(f"Ferramenta MCP '{tool_name}' nao encontrada no roteador dinamico.")
        return handler(**arguments)


_router_instance: Optional[MCPDynamicRouter] = None


def get_mcp_router() -> MCPDynamicRouter:
    global _router_instance
    if _router_instance is None:
        _router_instance = MCPDynamicRouter()
    return _router_instance
