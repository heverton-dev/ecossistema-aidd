# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — CLIENTE E CLI UNIVERSAL DO MOBBIN ENTERPRISE
=============================================================================
Permite busca determinística de telas do Mobbin via API REST oficial
(POST /v1/screens/search) para consumo agnóstico por qualquer harness
(Claude, OpenCode, MiMo, Goose, Copilot, etc.) ou esteira de planejamento.

Delega canonicamente para tools/aidd-planner (ou implementa nativamente).
Consome MOBBIN_API_KEY e MOBBIN_API_URL centralizados no .env raiz.
"""

import sys
from typing import Any, Dict

try:
    from aidd_planner.core.mobbin_client import (
        obter_config,
        executar_busca,
        cmd_status,
        cmd_search,
        main,
    )
except ImportError:
    import argparse
    import json
    import os
    from pathlib import Path

    try:
        from dotenv import load_dotenv
        root_dir = Path(__file__).resolve().parents[4]
        load_dotenv(root_dir / ".env")
    except ImportError:
        pass

    try:
        import requests
    except ImportError:
        requests = None

    def obter_config() -> tuple[str, str]:
        api_key = os.getenv("MOBBIN_API_KEY", "").strip()
        api_url = os.getenv("MOBBIN_API_URL", "https://api.mobbin.com").strip().rstrip("/")
        return api_key, api_url

    def executar_busca(
        query: str,
        platform: str = "web",
        mode: str = "standard",
        limit: int = 10,
        image_quality: str = "optimized"
    ) -> Dict[str, Any]:
        if not requests:
            print("[ERRO] Biblioteca 'requests' não encontrada no ambiente Python.", file=sys.stderr)
            sys.exit(1)

        api_key, api_url = obter_config()
        if not api_key:
            print("[ERRO] MOBBIN_API_KEY não configurada no arquivo .env.", file=sys.stderr)
            sys.exit(1)

        url = f"{api_url}/v1/screens/search"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "ecossistema-aidd/1.0"
        }
        payload = {
            "query": query,
            "platform": platform,
            "mode": mode,
            "limit": limit,
            "image_quality": image_quality
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[ERRO] Falha na comunicação com Mobbin ({url}): {e}", file=sys.stderr)
            sys.exit(1)

    def cmd_status() -> int:
        api_key, api_url = obter_config()
        print("=" * 60)
        print(" ECOSSISTEMA AIDD — STATUS DO CLIENTE MOBBIN")
        print("=" * 60)
        print(f" URL Base: {api_url}")
        print(f" Chave Configurada: {'[SIM]' if api_key else '[NÃO - DEFINA NO .env]'}")
        return 0 if api_key else 1

    def cmd_search(args) -> int:
        res = executar_busca(
            query=args.query,
            platform=getattr(args, "plataforma", "web"),
            mode=getattr(args, "modo", "standard"),
            limit=getattr(args, "limite", 10)
        )
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0

    def main(argv=None):
        return 0

__all__ = [
    "obter_config",
    "executar_busca",
    "cmd_status",
    "cmd_search",
    "main",
]
