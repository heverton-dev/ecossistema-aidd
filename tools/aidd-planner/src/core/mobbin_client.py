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

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from dotenv import load_dotenv
    # aidd_planner/core/mobbin_client.py -> raiz do ecossistema
    root_dir = Path(__file__).resolve().parents[4]
    load_dotenv(root_dir / ".env")
except ImportError:
    pass

try:
    import requests
except ImportError:
    requests = None


def obter_config() -> tuple[str, str]:
    """Retorna (api_key, api_url) a partir do ambiente."""
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
    """Executa POST /v1/screens/search com a chave Enterprise."""
    if not requests:
        print("[ERRO] Biblioteca 'requests' não encontrada no ambiente Python.", file=sys.stderr)
        sys.exit(1)

    api_key, api_url = obter_config()
    if not api_key:
        print("[ERRO] MOBBIN_API_KEY não configurada no arquivo .env.", file=sys.stderr)
        print("Adicione sua chave Enterprise em .env na raiz antes de executar.", file=sys.stderr)
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
        if response.status_code == 401:
            print("[ERRO] Chave de API do Mobbin inválida ou não autorizada (401).", file=sys.stderr)
            sys.exit(1)
        if response.status_code == 403:
            print("[ERRO] Acesso negado pelo Mobbin (403). Verifique o plano Enterprise.", file=sys.stderr)
            sys.exit(1)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"[ERRO] Falha na comunicação com Mobbin ({url}): {e}", file=sys.stderr)
        sys.exit(1)


def cmd_status() -> int:
    """Verifica se a chave e o endpoint estão declarados e prontos."""
    api_key, api_url = obter_config()
    print("=" * 60)
    print(" ECOSSISTEMA AIDD — STATUS DO CLIENTE MOBBIN (PLANNER)")
    print("=" * 60)
    print(f" URL Base: {api_url}")
    print(f" Chave Configurada: {'[SIM]' if api_key else '[NÃO - DEFINA NO .env]'}")
    if not api_key:
        print("\nPara ativar, preencha MOBBIN_API_KEY no arquivo .env.")
        return 1

    mascarada = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "***"
    print(f" Chave Ativa: {mascarada}")
    print(" Endpoint REST: POST /v1/screens/search")
    print(" Conexão pronta para qualquer harness.")
    print("-" * 60)
    return 0


def cmd_search(args) -> int:
    """Executa busca de telas via CLI."""
    plataforma = getattr(args, "plataforma", "web") or "web"
    modo = getattr(args, "modo", "standard") or "standard"
    limite = getattr(args, "limite", 10) or 10

    res = executar_busca(
        query=args.query,
        platform=plataforma,
        mode=modo,
        limit=limite
    )

    if getattr(args, "json", False) or getattr(args, "as_json", False):
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        screens = res.get("screens", [])
        print(f"\nResultados encontrados para '{args.query}' ({plataforma}): {len(screens)}")
        for idx, screen in enumerate(screens, 1):
            app_name = screen.get("app_name", "Desconhecido")
            screen_name = screen.get("name", "Sem nome")
            screen_url = screen.get("mobbin_url") or screen.get("url", "")
            img_url = screen.get("image_url", "")
            print(f" [{idx}] App: {app_name} | Tela: {screen_name}")
            if screen_url:
                print(f"     Mobbin: {screen_url}")
            if img_url:
                print(f"     Imagem: {img_url}")
    return 0


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog="python ecossistema.py planner mobbin",
        description="Cliente determinístico e agnóstico do Mobbin para o Ecossistema AIDD (Planner)"
    )
    subparsers = parser.add_subparsers(dest="subcmd")

    subparsers.add_parser("status", help="Verifica integridade das credenciais no .env")

    search_parser = subparsers.add_parser("search", help="Busca telas de UI por linguagem natural")
    search_parser.add_argument("query", help="Termo de pesquisa (ex: 'saas dashboard', 'checkout with stripe')")
    search_parser.add_argument("--plataforma", choices=["web", "ios"], default="web", help="Plataforma alvo (padrão: web)")
    search_parser.add_argument("--modo", choices=["fast", "standard", "deep"], default="standard", help="Modo de busca")
    search_parser.add_argument("--limite", type=int, default=10, help="Quantidade máxima de telas (1-100)")
    search_parser.add_argument("--json", action="store_true", help="Saída em JSON puro para pipelines")

    args = parser.parse_args(argv)

    if args.subcmd == "status" or not args.subcmd:
        return cmd_status()
    elif args.subcmd == "search":
        return cmd_search(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
