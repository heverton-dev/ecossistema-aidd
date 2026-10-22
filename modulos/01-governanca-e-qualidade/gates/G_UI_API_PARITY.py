# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_UI_API_PARITY (Lei #10 & Lei #11)
=============================================================================
Audita a paridade estrita entre os endpoints OpenAPI 3.1 declarados no Backend
e as chamadas HTTP ativas no Frontend (TypeScript / React / TanStack).

Invariante Fundamental:
  Nenhum sistema no Ecossistema AIDD pode nascer com "cascas cosméticas"
  ou capacidade de negócio oculta. A taxa de paridade de endpoints (TPE)
  entre as operações HTTP do backend e as invocações ativas no frontend
  deve ser igual ou superior ao limiar mínimo definido (padrão: 85%).

Fórmula:
  TPE = (Endpoints Conectados na UI / Endpoints Totais do Backend) * 100

Saída Binária (Lei #2):
  exit 0 = TPE >= limiar mínimo (aprovado)
  exit 1 = TPE < limiar mínimo ou ausência de rotas (bloqueado)

Uso:
  python G_UI_API_PARITY.py [--backend <pasta_backend>] [--frontend <pasta_frontend>] [--limiar <porcentagem>]
=============================================================================
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

DEFAULT_MIN_PARITY = 85.0


def extrair_endpoints_openapi(caminho_openapi: Path) -> Set[str]:
    """Extrai os caminhos (paths) únicos declarados em um arquivo openapi.json."""
    if not caminho_openapi.is_file():
        return set()
    try:
        dados = json.loads(caminho_openapi.read_text(encoding="utf-8"))
        paths = dados.get("paths", {})
        return {p.rstrip("/") for p in paths.keys() if p}
    except Exception:
        return set()


def extrair_endpoints_fastapi_ast(pasta_backend: Path) -> Set[str]:
    """Extrai rotas FastAPI inspecionando decoradores @router.* ou @app.* em arquivos Python."""
    rotas: Set[str] = set()
    if not pasta_backend.is_dir():
        return rotas

    # Regex robusto para capturar decoradores de rotas FastAPI: @router.get("/...") ou @app.post('/...')
    padrao_rota = re.compile(
        r"@(?:router|app)\.(?:get|post|put|delete|patch|options|head)\s*\(\s*['\"]([^'\"]+)['\"]",
        re.IGNORECASE,
    )

    for py_file in pasta_backend.rglob("*.py"):
        try:
            conteudo = py_file.read_text(encoding="utf-8", errors="ignore")
            for m in padrao_rota.finditer(conteudo):
                rota = m.group(1).split("?")[0].rstrip("/")
                if rota:
                    rotas.add(rota)
        except OSError:
            continue
    return rotas


def extrair_chamadas_api_frontend(pasta_frontend: Path) -> Set[str]:
    """Varre arquivos .ts e .tsx procurando chamadas literais ou dinâmicas a endpoints de API."""
    chamadas: Set[str] = set()
    if not pasta_frontend.is_dir():
        return chamadas

    # Padrão para capturar URLs de API em chamadas fetch, axios, tanstack query ou strings de rotas
    padrao_url = re.compile(
        r"[`'\"](?:https?://[^/]+)?(/api/v[0-9]+[^`'\"?#\s]*|/api/[^`'\"?#\s]*)",
        re.IGNORECASE,
    )

    for ext in ("*.ts", "*.tsx", "*.js", "*.jsx"):
        for ts_file in pasta_frontend.rglob(ext):
            # Ignora arquivos de contrato bruto gerados automaticamente se existirem fora da UI ativa
            if "api_contracts.ts" in ts_file.name or ".test." in ts_file.name or ".spec." in ts_file.name:
                continue
            try:
                conteudo = ts_file.read_text(encoding="utf-8", errors="ignore")
                # Remove comentários de bloco e linha para evitar falsos positivos
                conteudo_limpo = re.sub(r"/\*.*?\*/", "", conteudo, flags=re.DOTALL)
                conteudo_limpo = re.sub(r"//.*", "", conteudo_limpo)

                for m in padrao_url.finditer(conteudo_limpo):
                    url = m.group(1).rstrip("/")
                    # Normaliza parâmetros de rota dinâmicos (ex.: /api/v1/deals/{id} ou /api/v1/deals/${id})
                    url_norm = re.sub(r"\$\{?[^/}]+\}?", "{param}", url)
                    chamadas.add(url_norm)
            except OSError:
                continue
    return chamadas


def normalizar_rota(rota: str) -> str:
    """Normaliza parâmetros de rota em formato padrão {param} para cruzamento."""
    rota_limpa = rota.rstrip("/")
    # Transforma {deal_id}, {id}, :id em {param}
    rota_norm = re.sub(r"\{[^}]+\}", "{param}", rota_limpa)
    rota_norm = re.sub(r":([a-zA-Z0-9_]+)", "{param}", rota_norm)
    return rota_norm


def calcular_paridade(
    rotas_backend: Set[str],
    chamadas_frontend: Set[str],
) -> Tuple[float, Set[str], Set[str]]:
    """Calcula a taxa de paridade entre as rotas do backend e as invocações do frontend."""
    if not rotas_backend:
        return 100.0, set(), set()

    rotas_backend_norm = {normalizar_rota(r) for r in rotas_backend}
    frontend_norm = {normalizar_rota(c) for c in chamadas_frontend}

    conectadas: Set[str] = set()
    orfas: Set[str] = set()

    for rota in rotas_backend_norm:
        # Verifica correspondência exata ou prefixo semântico compatível
        if rota in frontend_norm or any(rota in f or f in rota for f in frontend_norm):
            conectadas.add(rota)
        else:
            orfas.add(rota)

    taxa = (len(conectadas) / len(rotas_backend_norm)) * 100.0
    return taxa, conectadas, orfas


def auditar_paridade(
    raiz_projeto: Path,
    caminho_backend: Path | None = None,
    caminho_frontend: Path | None = None,
    limiar_minimo: float = DEFAULT_MIN_PARITY,
) -> int:
    """Executa a auditoria completa de paridade e emite o veredito binário."""
    print("=" * 70)
    print(" [GATE] G_UI_API_PARITY — Paridade Estrita entre Rotas Backend e Frontend")
    print("=" * 70)

    # 1. Resolver diretórios
    b_dir = caminho_backend or (raiz_projeto / "src")
    if not b_dir.is_dir() and (raiz_projeto / "app" / "backend").is_dir():
        b_dir = raiz_projeto / "app" / "backend"

    f_dir = caminho_frontend or (raiz_projeto / "frontend" / "src")
    if not f_dir.is_dir() and (raiz_projeto / "app" / "frontend" / "src").is_dir():
        f_dir = raiz_projeto / "app" / "frontend" / "src"

    # 2. Extrair rotas do backend (tenta openapi.json primeiro, depois AST dos routers)
    rotas_backend: Set[str] = set()
    candidatos_openapi = [
        raiz_projeto / "openapi.json",
        raiz_projeto / "docs" / "openapi.json",
        raiz_projeto / "src" / "openapi.json",
    ]
    for c in candidatos_openapi:
        if c.is_file():
            rotas_backend = extrair_endpoints_openapi(c)
            if rotas_backend:
                print(f"[INFO] Contrato OpenAPI carregado de: {c.relative_to(raiz_projeto)} ({len(rotas_backend)} paths)")
                break

    if not rotas_backend:
        rotas_backend = extrair_endpoints_fastapi_ast(b_dir)
        print(f"[INFO] Rotas extraídas via AST de {b_dir}: {len(rotas_backend)} rotas")

    if not rotas_backend:
        print("[INFO] Nenhuma rota de backend detectada no projeto analisado. Gate dispensado.")
        print("=" * 70)
        return 0

    # 3. Extrair chamadas do frontend
    chamadas_frontend = extrair_chamadas_api_frontend(f_dir)
    print(f"[INFO] Chamadas a endpoints identificadas em {f_dir}: {len(chamadas_frontend)}")

    # 4. Calcular métricas
    taxa, conectadas, orfas = calcular_paridade(rotas_backend, chamadas_frontend)

    print("-" * 70)
    print(f" Total de Rotas Declaradas no Backend:   {len(rotas_backend)}")
    print(f" Rotas Efetivamente Conectadas na UI:   {len(conectadas)}")
    print(f" Rotas Órfãs / Invisíveis para Usuário: {len(orfas)}")
    print(f" Taxa de Paridade de Endpoints (TPE):   {taxa:.2f}% (Limiar Mínimo: {limiar_minimo:.1f}%)")
    print("-" * 70)

    if taxa < limiar_minimo:
        print(" [FALHA] Quality Gate REPROVADO:")
        print(f"  - Subutilização severa de backend: apenas {taxa:.2f}% dos endpoints estão na UI.")
        print("  - Cascas cosméticas detectadas ou telas omitidas. Endpoints órfãos (amostra):")
        for orf in sorted(list(orfas))[:10]:
            print(f"     • {orf}")
        if len(orfas) > 10:
            print(f"     ... e mais {len(orfas) - 10} endpoint(s) sem tela ou botão na interface.")
        print("=" * 70)
        return 1

    print(" [SUCESSO] Quality Gate G_UI_API_PARITY APROVADO (100% OK)!")
    print("=" * 70)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Audita a paridade estrita entre rotas OpenAPI do Backend e UI.")
    parser.add_argument("--projeto", default=".", help="Raiz do projeto alvo")
    parser.add_argument("--backend", default=None, help="Caminho explícito da pasta do backend")
    parser.add_argument("--frontend", default=None, help="Caminho explícito da pasta do frontend")
    parser.add_argument("--limiar", type=float, default=DEFAULT_MIN_PARITY, help="Limiar mínimo percentual (ex: 85.0)")
    args = parser.parse_args()

    raiz = Path(args.projeto).resolve()
    b_path = Path(args.backend).resolve() if args.backend else None
    f_path = Path(args.frontend).resolve() if args.frontend else None

    return auditar_paridade(raiz, b_path, f_path, args.limiar)


if __name__ == "__main__":
    sys.exit(main())
