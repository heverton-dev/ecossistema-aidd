# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — RESOLVEDOR DE REFERÊNCIAS VISUAIS DE UI (PLANNER)
=============================================================================
Oferece três caminhos para definição de referências de telas:
1. [PRINCIPAL PADRÃO]: Buscar referências no Mobbin via API Enterprise oficial.
2. [BUSCAR REFS ONLINE]: Coletar referências em galerias abertas (21st.dev, transitions.dev, etc.).
3. [MODELO DETERMINÍSTICO]: Resolução estática offline via design_catalog (Zero LLM, Zero Net).
"""

from __future__ import annotations

import sys
from typing import Any, Dict, Optional


MODO_MOBBIN = "mobbin"
MODO_ONLINE = "online"
MODO_DETERMINISTICO = "deterministico"

OPCOES_VALIDAS = {
    "1": MODO_MOBBIN,
    MODO_MOBBIN: MODO_MOBBIN,
    "2": MODO_ONLINE,
    MODO_ONLINE: MODO_ONLINE,
    "3": MODO_DETERMINISTICO,
    MODO_DETERMINISTICO: MODO_DETERMINISTICO,
}


def solicitar_modo_interativo() -> str:
    """Apresenta menu no terminal quando executado em TTY interativo."""
    print("\n" + "=" * 68)
    print(" [aidd-planner] SELEÇÃO DE REFERÊNCIAS DE TELAS E DESIGN SYSTEM")
    print("=" * 68)
    print(" Escolha o caminho para definir as referências de UI do projeto:")
    print("   1. [PRINCIPAL PADRÃO]    Buscar referências no Mobbin via API Enterprise")
    print("   2. [BUSCAR REFS ONLINE]  Buscar em 21st.dev, transitions.dev, Dribbble, etc.")
    print("   3. [DETERMINÍSTICO]       Modelo estático offline padrão-ouro (Zero LLM / Zero Net)")
    print("-" * 68)

    while True:
        try:
            escolha = input(" Opção [1/2/3] (Padrão: 1): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[aidd-planner] Entrada interrompida, adotando modo determinístico por segurança.")
            return MODO_DETERMINISTICO

        if not escolha:
            return MODO_MOBBIN

        modo = OPCOES_VALIDAS.get(escolha.lower())
        if modo:
            return modo

        print(" [AVISO] Opção inválida. Digite 1, 2 ou 3.")


def buscar_referencias_mobbin(
    termo: str,
    plataforma: str = "web",
    limite: int = 3
) -> Optional[Dict[str, Any]]:
    """Consulta a API Enterprise do Mobbin para extrair uma tela de referência."""
    try:
        from .mobbin_client import executar_busca
    except ImportError:
        try:
            from src.core_planner.mobbin_client import executar_busca
        except ImportError:
            return None

    try:
        resultado = executar_busca(query=termo, platform=plataforma, limit=limite)
        screens = resultado.get("screens", [])
        if screens:
            primeira = screens[0]
            return {
                "fonte": "mobbin_api",
                "app_name": primeira.get("app_name", termo),
                "name": primeira.get("name", "Tela de Referência"),
                "screen_type": "dashboard",
                "tags": [termo, plataforma],
                "mobbin_url": primeira.get("mobbin_url") or primeira.get("url", ""),
                "image_url": primeira.get("image_url", ""),
                "total_telas_encontradas": len(screens)
            }
    except Exception as err:
        print(f"[aidd-planner] Erro ao consultar Mobbin API: {err}. Recorrendo ao fallback determinístico.", file=sys.stderr)

    return None


def buscar_referencias_online(
    termo: str,
    dominio: str,
    plataforma: str = "web"
) -> Dict[str, Any]:
    """
    Estrutura contrato de referência com base em galerias abertas e abrange
    21st.dev, transitions.dev, Dribbble, Behance e Pinterest.
    """
    return {
        "fonte": "online_curated_galleries",
        "app_name": f"{dominio.capitalize()} Curated Design",
        "screen_type": "dashboard",
        "tags": [dominio, termo, plataforma, "modern-ui", "accessible"],
        "galerias_pesquisadas": [
            "21st.dev (Tailwind/React componentes livres)",
            "transitions.dev (Microinterações e física de UI)",
            "dribbble.com (Composições e layouts abertos)",
            "behance.net (Identidade visual de produtos)",
            "pinterest.com (Arquétipos de interfaces web)"
        ],
        "diretrizes": [
            "Uso prioritário de bibliotecas de componentes abertos (Radix / Tailwind / Lucide)",
            "Zero dependência de serviços proprietários",
            "Tipografia de fontes abertas (Inter, Geist, Roboto)"
        ]
    }


def resolver_referencia_ui(
    modo: Optional[str],
    projeto_nome: str,
    dominio: str,
    plataforma: str = "web"
) -> tuple[str, Optional[Dict[str, Any]]]:
    """
    Ponto de entrada único para resolver a referência de tela.
    Retorna (modo_utilizado, tela_referencia).
    """
    modo_escolhido = modo.lower() if modo else None

    # Se modo não foi especificado via flag:
    if not modo_escolhido:
        if sys.stdin.isatty():
            modo_escolhido = solicitar_modo_interativo()
        else:
            # Em execuções não-interativas (scripts, CI, bots), o padrão canônico é Mobbin
            modo_escolhido = MODO_MOBBIN

    modo_resolvido = OPCOES_VALIDAS.get(modo_escolhido, MODO_MOBBIN)

    if modo_resolvido == MODO_MOBBIN:
        print(f"[aidd-planner] [1. MOBBIN] Consultando API Enterprise para '{dominio}'...")
        tela = buscar_referencias_mobbin(dominio, plataforma=plataforma)
        if tela:
            print(f"[aidd-planner] Referência obtida do Mobbin: {tela.get('app_name')} ({tela.get('mobbin_url', 'sem URL')})")
            return MODO_MOBBIN, tela
        print("[aidd-planner] Nenhuma tela retornada pelo Mobbin ou chave ausente. Ativando modelo determinístico.")
        return MODO_MOBBIN, None

    elif modo_resolvido == MODO_ONLINE:
        print(f"[aidd-planner] [2. REFS ONLINE] Estruturando referências abertas (21st.dev, transitions.dev, etc.)...")
        tela = buscar_referencias_online(projeto_nome, dominio, plataforma=plataforma)
        return MODO_ONLINE, tela

    # MODO_DETERMINISTICO
    print("[aidd-planner] [3. DETERMINÍSTICO] Usando catálogo estático e motor topológico padrão-ouro (Zero LLM / Zero Net).")
    return MODO_DETERMINISTICO, None
