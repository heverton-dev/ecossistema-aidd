# -*- coding: utf-8 -*-
"""
ORCA Fleet — Gerador dinamico de inventario e fallback em cascata.

Gera '.orca/01_orca_inventory.json' com as ferramentas reais do host.
Aplica fallback em cascata: se o usuario tiver apenas 1 agente, todos
os workers operam nele em worktrees separadas sem falhar.

Override via variavel de ambiente ORCA_DEFAULT_HARNESS.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .detector import (
    DetectorResultado,
    FerramentaDetectada,
    executar_deteccao_completa,
)


# =============================================================================
# CONSTANTES
# =============================================================================

ORCA_INVENTORY_PATH = Path('.orca') / '01_orca_inventory.json'

# Mapeamento de especialidade → ferramenta preferida
ROTEAMENTO_ESPECIALIDADE = {
    'arquitetura': 'claude',
    'analise': 'claude',
    'design': 'claude',
    'documentacao': 'claude',
    'database': 'codex',
    'testes': 'codex',
    'refatoracao': 'codex',
    'codigo': 'claude',
    'frontend': 'cursor',
}

# Mapeamento fase → especialidade
FASE_ESPECIALIDADE = {
    'phase_01': 'analise',
    'phase_02': 'analise',
    'phase_03': 'design',
    'phase_04': 'arquitetura',
    'phase_05': 'codigo',
    'phase_06': 'documentacao',
    'phase_07': 'analise',
    'phase_08': 'codigo',
    'phase_08_schema': 'database',
    'phase_08_teste': 'testes',
}


# =============================================================================
# DATA CLASS — Status da frota ORCA
# =============================================================================

class OrcaFleetStatus:
    """Status resolvido da frota ORCA."""

    def __init__(
        self,
        ferramentas: List[FerramentaDetectada],
        modo: str,
        ferramenta_default: Optional[str] = None,
        override_config: Optional[str] = None,
        orca_presente: bool = False,
    ):
        self.ferramentas = ferramentas
        self.modo = modo  # 'multi-agente', 'agente-unico', 'nenhum'
        self.ferramenta_default = ferramenta_default
        self.override_config = override_config
        self.orca_presente = orca_presente

    def to_dict(self) -> Dict:
        return {
            'ferramentas': [f.to_dict() for f in self.ferramentas],
            'total': len(self.ferramentas),
            'modo': self.modo,
            'ferramenta_default': self.ferramenta_default,
            'override_config': self.override_config,
            'orca_presente': self.orca_presente,
        }


# =============================================================================
# RESOLUCAO DA FROTA
# =============================================================================

def resolver_frota(
    resultado_deteccao: Optional[DetectorResultado] = None,
    override_harness: Optional[str] = None,
) -> OrcaFleetStatus:
    """
    Resolve o status da frota com fallback em cascata.

    Logica:
    1. Se ORCA_DEFAULT_HARNESS definido → filtra so essa ferramenta
    2. Se multiplas ferramentas → modo multi-agente, roteia por especialidade
    3. Se apenas 1 → modo agente-unico (todos workers nela, worktrees separadas)
    4. Se nenhuma → modo nenhum (erro honesto, nunca silencioso)

    Args:
        resultado_deteccao: Resultado de detector.executar_deteccao_completa().
                           Se None, executa deteccao automaticamente.
        override_harness: Forca uma ferramenta (ORCA_DEFAULT_HARNESS).

    Returns:
        OrcaFleetStatus com modo operacional e ferramentas.
    """
    if resultado_deteccao is None:
        resultado_deteccao = executar_deteccao_completa()

    override = override_harness or os.environ.get('ORCA_DEFAULT_HARNESS')
    ferramentas = resultado_deteccao.ferramentas

    # Override explicito
    if override:
        override_lower = override.lower()
        filtradas = [
            f for f in ferramentas
            if f.nome == override_lower or f.comando == override_lower
        ]
        if filtradas:
            return OrcaFleetStatus(
                ferramentas=filtradas,
                modo='agente-unico',
                ferramenta_default=override_lower,
                override_config=override,
                orca_presente=resultado_deteccao.orca_presente,
            )
        else:
            # Override aponta para ferramenta nao encontrada
            return OrcaFleetStatus(
                ferramentas=[],
                modo='nenhum',
                ferramenta_default=None,
                override_config=override,
                orca_presente=resultado_deteccao.orca_presente,
            )

    # Auto-deteccao (sem override)
    if len(ferramentas) >= 2:
        return OrcaFleetStatus(
            ferramentas=ferramentas,
            modo='multi-agente',
            ferramenta_default=ferramentas[0].nome,
            orca_presente=resultado_deteccao.orca_presente,
        )
    elif len(ferramentas) == 1:
        return OrcaFleetStatus(
            ferramentas=ferramentas,
            modo='agente-unico',
            ferramenta_default=ferramentas[0].nome,
            orca_presente=resultado_deteccao.orca_presente,
        )
    else:
        return OrcaFleetStatus(
            ferramentas=[],
            modo='nenhum',
            ferramenta_default=None,
            orca_presente=resultado_deteccao.orca_presente,
        )


# =============================================================================
# ROTEAMENTO POR ESPECIALIDADE
# =============================================================================

def rotear_por_especialidade(
    especialidade: str,
    ferramentas: List[FerramentaDetectada],
) -> Optional[FerramentaDetectada]:
    """
    Escolhe a melhor ferramenta para uma especialidade.

    1. Procura ferramenta preferida pelo mapeamento global
    2. Se nao, qualquer uma que tenha a especialidade
    3. Fallback: primeira da lista (menor prioridade)
    """
    if not ferramentas:
        return None

    preferida = ROTEAMENTO_ESPECIALIDADE.get(especialidade)
    if preferida:
        for f in ferramentas:
            if f.nome == preferida:
                return f

    for f in ferramentas:
        if especialidade in f.especialidades:
            return f

    return ferramentas[0]


def resolver_para_fase(
    fase: str,
    fleet: OrcaFleetStatus,
) -> Optional[str]:
    """
    Retorna o nome da ferramenta para uma fase do pipeline.

    Em modo multi-agente: roteia por especialidade.
    Em modo agente-unico: usa a ferramenta default.
    Em modo nenhum: retorna None.
    """
    if fleet.modo == 'nenhum':
        return None

    especialidade = FASE_ESPECIALIDADE.get(fase, 'codigo')

    if fleet.modo == 'multi-agente':
        ferramenta = rotear_por_especialidade(especialidade, fleet.ferramentas)
        return ferramenta.nome if ferramenta else fleet.ferramenta_default

    return fleet.ferramenta_default


# =============================================================================
# GERACAO DO INVENTARIO JSON
# =============================================================================

def gerar_inventory(
    fleet: OrcaFleetStatus,
    destino: Optional[Path] = None,
) -> Path:
    """
    Gera o arquivo '.orca/01_orca_inventory.json' com as ferramentas reais.

    Args:
        fleet: OrcaFleetStatus resolvido.
        destino: Caminho customizado. Default: .orca/01_orca_inventory.json

    Returns:
        Path do arquivo gerado.
    """
    caminho = destino or ORCA_INVENTORY_PATH
    caminho.parent.mkdir(parents=True, exist_ok=True)

    inventory = {
        'metadata': {
            'versao': '1.0',
            'gerado_em': datetime.now(timezone.utc).isoformat(),
            'gerador': 'orca_fleet.py',
            'descricao': 'Inventario automatico de ferramentas do host para ORCA ADE',
        },
        'frota': fleet.to_dict(),
        'roteamento': {
            esp: pref for esp, pref in ROTEAMENTO_ESPECIALIDADE.items()
        },
        'fases': {
            fase: resolver_para_fase(fase, fleet)
            for fase in FASE_ESPECIALIDADE
        },
    }

    caminho.write_text(
        json.dumps(inventory, indent=2, ensure_ascii=False),
        encoding='utf-8',
    )
    return caminho


# =============================================================================
# INTERFACE PRINCIPAL — Uso direto
# =============================================================================

def inicializar_frota(
    override_harness: Optional[str] = None,
    gerar_json: bool = True,
    destino_json: Optional[Path] = None,
) -> OrcaFleetStatus:
    """
    Ponto de entrada principal: detecta, resolve e opcionalmente gera JSON.

    Args:
        override_harness: Forca uma ferramenta (ORCA_DEFAULT_HARNESS).
        gerar_json: Se True, gera o arquivo de inventario.
        destino_json: Caminho customizado para o JSON.

    Returns:
        OrcaFleetStatus com a frota resolvida.
    """
    resultado = executar_deteccao_completa()
    fleet = resolver_frota(resultado, override_harness=override_harness)

    if gerar_json:
        gerar_inventory(fleet, destino=destino_json)

    return fleet
