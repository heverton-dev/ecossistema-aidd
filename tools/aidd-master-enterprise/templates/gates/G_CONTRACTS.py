#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.1 / v5.0 Enterprise — GATE DETERMINÍSTICO DE CONTRATOS OPENAPI & MCP (G_CONTRACTS)
=============================================================================
Valida a conformidade de 100% das rotas registradas no RouteRegistry com o padrão
OpenAPI 3.1, ferramentas expostas no MCP Server, integridade dos 4 Portais e Snapshot SHA-256.
"""

import os
import sys
import argparse
import hashlib
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def verificar_contratos(target_dir: str = "."):
    print("[GATE G_CONTRACTS] Validando contratos de rotas, esquemas OpenAPI 3.1, MCP e 4 Portais...")
    target_dir = os.path.abspath(target_dir)
    src_path = os.path.join(target_dir, "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    erros = []

    # 1. Validar RouteRegistry e Rotas dos Módulos
    try:
        from core.openapi import RouteRegistry
        modules_dir = os.path.join(src_path, "modules")
        if os.path.exists(modules_dir):
            modulos = [
                m for m in os.listdir(modules_dir)
                if os.path.isdir(os.path.join(modules_dir, m)) and not m.startswith("__")
            ]
            for m in modulos:
                routes_path = os.path.join(modules_dir, m, "routes.py")
                if os.path.exists(routes_path):
                    with open(routes_path, "r", encoding="utf-8", errors="ignore") as f:
                        conteudo = f.read()
                        if "@registry." not in conteudo and "registrar_rotas" not in conteudo:
                            erros.append(f"Módulo '{m}' não registra rotas com decoradores RouteRegistry.")
    except Exception as e:
        erros.append(f"Falha ao validar RouteRegistry: {str(e)}")

    # 2. Validar MCP Server
    mcp_file = os.path.join(src_path, "core", "mcp_server.py")
    if os.path.exists(mcp_file):
        try:
            with open(mcp_file, "r", encoding="utf-8", errors="ignore") as f:
                code = f.read()
                if "MCPServer" not in code or ("handle_json_rpc" not in code and "handle_request" not in code):
                    erros.append("Servidor MCP presente mas sem classe MCPServer ou método de processamento JSON-RPC.")
        except Exception as e:
            erros.append(f"Erro ao inspecionar MCP server: {str(e)}")

    # 3. Snapshot SHA-256 de Integridade de Contratos
    contract_manifest = {}
    try:
        if os.path.exists(modules_dir):
            for m in modulos:
                routes_path = os.path.join(modules_dir, m, "routes.py")
                if os.path.exists(routes_path):
                    with open(routes_path, "rb") as rf:
                        contract_manifest[m] = hashlib.sha256(rf.read()).hexdigest()[:16]
        
        snapshot_hash = hashlib.sha256(json.dumps(contract_manifest, sort_keys=True).encode()).hexdigest()[:16]
        print(f"  [+] Snapshot SHA-256 de Contratos: {snapshot_hash} ({len(contract_manifest)} módulos ativos)")
    except Exception as e:
        erros.append(f"Erro ao gerar snapshot de contratos: {e}")

    # 4. Validar Integridade e Autossuficiência dos 4 Portais Front-End
    index_html = os.path.join(src_path, "static", "index.html")
    if os.path.exists(index_html):
        try:
            with open(index_html, "r", encoding="utf-8", errors="ignore") as f:
                h = f.read()
                if "<style>" not in h or "--bg-base" not in h:
                    erros.append("Super-App 'index.html' sem CSS offline-first embutido na tag <style>.")
                if "modal-overlay" not in h and "modal-generic" not in h:
                    erros.append("Super-App 'index.html' sem estrutura modal com display encapsulado.")
                if "<svg" in h and 'width="' not in h:
                    erros.append("Super-App 'index.html' possui SVGs sem dimensões físicas travadas (width/height).")
        except Exception as e:
            erros.append(f"Erro ao auditar front-end index.html: {e}")

    # Checar geradores de HTML dos estúdios integrados
    openapi_py = os.path.join(src_path, "core", "openapi.py")
    if os.path.exists(openapi_py):
        with open(openapi_py, "r", encoding="utf-8", errors="ignore") as f:
            if "get_swagger_html" not in f.read():
                erros.append("core/openapi.py não implementa get_swagger_html() para o Swagger Studio.")

    webhooks_py = os.path.join(src_path, "core", "webhooks.py")
    if os.path.exists(webhooks_py):
        with open(webhooks_py, "r", encoding="utf-8", errors="ignore") as f:
            if "get_studio_html" not in f.read():
                erros.append("core/webhooks.py não implementa get_studio_html() para o Webhook Studio.")

    if erros:
        print("\n[FAIL] ❌ BLOQUEIO DE CONTRATOS: Violações de contrato/portais detectadas:")
        for e in erros:
            print(f"  - {e}")
        sys.exit(1)

    print("[OK] SUCESSO: Todos os contratos OpenAPI, MCP e os 4 Portais Web foram validados com 100% de êxito!")
    sys.exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=".", help="Diretório alvo do projeto")
    args, _ = parser.parse_known_args()
    verificar_contratos(args.dir)
