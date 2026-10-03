# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — MOTOR TOPOLÓGICO DE ARQUÉTIPOS VISUAIS & ENGENHARIA MOBILE
=============================================================================
Classifica a estrutura física da referência do Mobbin (Web Desktop vs Mobile/PWA),
extrai regras de ergonomia espacial (Touch Targets, Safe Areas, Elevação) e emite
as diretrizes arquiteturais para garantir identidade exclusiva e padrão enterprise.
"""

from typing import Any, Dict, List


class ArquétipoTopologico:
    # Arquétipos Web / Desktop
    RAIL_TWO_LEVEL = "rail_two_level"             # Consoles Cloud / DevTools / Monitoramento
    MASTER_DETAIL_INSPECTOR = "master_detail"     # ERP / CRM / Ferramentas de Gestão
    KANBAN_WORKSPACE = "kanban_workspace"         # Gestão Operacional / Projetos
    ANALYTICS_CANVAS = "analytics_canvas"         # BI / Relatórios / Painéis de Métricas

    # Arquétipos Mobile First / PWA
    MOBILE_TABBAR_SHEET = "mobile_tabbar_sheet"   # Apps Nativos com TabBar inferior e Bottom Sheets
    MOBILE_CARD_FEED = "mobile_card_feed"         # Feeds Verticais / Telemetria Móvel
    MOBILE_TRANSACTIONAL = "mobile_transactional" # Checkout / Fluxos de Aprovação em 1 mão


def classificar_arquetipo(tela: Dict[str, Any], plataforma: str = "web") -> Dict[str, Any]:
    """
    Classifica a anatomia do layout a partir dos metadados e tags do Mobbin,
    definindo o contrato ergonômico estrito para a geração da interface.
    """
    app_name = (tela.get("app_name") or "").lower()
    tags = [t.lower() for t in tela.get("tags", [])]
    screen_type = (tela.get("screen_type") or "").lower()
    is_mobile = plataforma.lower() in ["ios", "android", "mobile", "pwa"]

    if is_mobile:
        if any(k in app_name or k in tags for k in ["checkout", "payment", "crypto", "banking"]):
            arquetipo = ArquétipoTopologico.MOBILE_TRANSACTIONAL
            descricao = "Fluxo Transacional Móvel com Teclado Numérico, Bottom Actions e Biometria"
        elif any(k in app_name or k in tags for k in ["feed", "social", "delivery", "orders"]):
            arquetipo = ArquétipoTopologico.MOBILE_CARD_FEED
            descricao = "Feed Vertical com Cards de Alta Densidade e Pull-to-Refresh"
        else:
            arquetipo = ArquétipoTopologico.MOBILE_TABBAR_SHEET
            descricao = "App Corporativo PWA com Bottom TabBar Ergonômica e Gaveta de Detalhes"

        diretrizes = {
            "plataforma": "mobile_pwa",
            "arquetipo": arquetipo,
            "descricao": descricao,
            "ergonomia": {
                "touch_target_min": "48px",
                "safe_area_top": "env(safe-area-inset-top, 20px)",
                "safe_area_bottom": "env(safe-area-inset-bottom, 24px)",
                "nav_position": "bottom_fixed",
                "tabbar_height": "64px",
                "modal_pattern": "bottom_sheet_swipeable"
            },
            "densidade": {
                "data_display": "cards_verticais_com_badges",
                "table_allowed": False,
                "max_colunas_grid": 1
            }
        }
    else:
        if any(k in app_name or k in tags for k in ["supabase", "aws", "datadog", "grafana", "linear", "github"]):
            arquetipo = ArquétipoTopologico.RAIL_TWO_LEVEL
            descricao = "Console Técnico de Alta Densidade com Rail Nível 1 e Sidebar Nível 2"
        elif any(k in app_name or k in tags for k in ["crm", "erp", "salesforce", "hubspot", "notion"]):
            arquetipo = ArquétipoTopologico.MASTER_DETAIL_INSPECTOR
            descricao = "Master-Detail com Painel Lateral de Inspeção em Tempo Real"
        else:
            arquetipo = ArquétipoTopologico.ANALYTICS_CANVAS
            descricao = "Painel Analítico Multimétric com Gráficos e Tabelas de Auditoria"

        diretrizes = {
            "plataforma": "desktop_web",
            "arquetipo": arquetipo,
            "descricao": descricao,
            "ergonomia": {
                "touch_target_min": "32px",
                "safe_area_top": "0px",
                "safe_area_bottom": "0px",
                "nav_position": "left_sidebar_or_rail",
                "tabbar_height": "none",
                "modal_pattern": "dialog_centered"
            },
            "densidade": {
                "data_display": "tabela_multicoluna_com_sparklines",
                "table_allowed": True,
                "max_colunas_grid": 4
            }
        }

    return diretrizes
