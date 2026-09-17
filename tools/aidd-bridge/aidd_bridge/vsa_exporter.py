# -*- coding: utf-8 -*-
"""
===============================================================================
VSA Exporter — aidd-bridge
===============================================================================
Harmoniza o projeto extraído/unificado com o padrão Monólito Modular VSA
do ecossistema AIDD, preparando o terreno para o aidd-master e gerando
os contratos dinâmicos do Quarteto Sine Qua Non (/swagger, /webhooks, /mcp, /docs).
===============================================================================
"""

import os
import json
from typing import Dict, Any, List


class BridgeVSAExporter:
    """Exporta contratos e mapeamento VSA a partir do manifesto do LovableScanner."""

    def __init__(self, manifest: Dict[str, Any], output_dir: str):
        self.manifest = manifest
        self.output_dir = os.path.abspath(output_dir)

    def export_quarteto_contracts(self) -> Dict[str, str]:
        """Gera os 4 contratos canônicos do Quarteto Sine Qua Non."""
        quarteto_dir = os.path.join(self.output_dir, "quarteto_sine_qua_non")
        os.makedirs(quarteto_dir, exist_ok=True)

        app_name = self.manifest.get("framework", "app")
        rotas = self.manifest.get("routes", [])
        paginas = self.manifest.get("pages", [])

        # 1. Swagger OpenAPI Contract
        openapi_spec = {
            "openapi": "3.0.3",
            "info": {
                "title": f"{app_name.capitalize()} — Contratos OpenAPI (Bridge VSA)",
                "version": "1.0.0",
                "description": "Especificação dinâmica gerada a partir de protótipo low-code desatado."
            },
            "paths": {}
        }
        for rota in rotas:
            openapi_spec["paths"][rota] = {
                "get": {
                    "summary": f"Acesso à rota {rota}",
                    "responses": {
                        "200": {"description": "Página/serviço renderizado com sucesso"}
                    }
                }
            }

        swagger_file = os.path.join(quarteto_dir, "swagger_spec.json")
        with open(swagger_file, "w", encoding="utf-8") as f:
            json.dump(openapi_spec, f, indent=2, ensure_ascii=False)

        # 2. Webhooks Contract
        webhooks_spec = {
            "title": "Webhook Studio — Bridge",
            "algorithm": "HMAC-SHA256",
            "events_supported": [
                "auth.user_created",
                "auth.user_updated",
                "database.record_inserted",
                "database.record_updated"
            ],
            "endpoints": [
                {"path": "/webhooks/events", "method": "POST", "auth": "HMAC-SHA256"}
            ]
        }
        webhooks_file = os.path.join(quarteto_dir, "webhooks_contract.json")
        with open(webhooks_file, "w", encoding="utf-8") as f:
            json.dump(webhooks_spec, f, indent=2, ensure_ascii=False)

        # 3. MCP Studio Tools
        mcp_tools = {
            "server": f"{app_name}-bridge-mcp",
            "tools": [
                {
                    "name": "list_pages",
                    "description": "Lista todas as páginas e rotas da interface",
                    "inputSchema": {"type": "object", "properties": {}}
                },
                {
                    "name": "get_database_schema",
                    "description": "Retorna o schema e tabelas do banco consolidado",
                    "inputSchema": {"type": "object", "properties": {}}
                }
            ]
        }
        mcp_file = os.path.join(quarteto_dir, "mcp_studio.json")
        with open(mcp_file, "w", encoding="utf-8") as f:
            json.dump(mcp_tools, f, indent=2, ensure_ascii=False)

        # 4. User Documentation
        docs_content = f"""# Guia do Utilizador — {app_name.capitalize()}

## Visão Geral
Aplicação low-code resgatada, desatada de vendor lock-in e preparada para Monólito Modular VSA.

## Rotas Mapeadas
Total de rotas detectadas: {len(rotas)}
{chr(10).join(f"- `{r}`" for r in rotas)}

## Páginas Principais
{chr(10).join(f"- `{p}`" for p in paginas)}

## Como Executar
1. `docker compose up -d` para iniciar banco PostgreSQL e PostgREST.
2. Acesse a interface local em `http://localhost:8080`.
"""
        docs_file = os.path.join(quarteto_dir, "USER_GUIDE.md")
        with open(docs_file, "w", encoding="utf-8") as f:
            f.write(docs_content)

        return {
            "swagger": swagger_file,
            "webhooks": webhooks_file,
            "mcp": mcp_file,
            "docs": docs_file
        }
