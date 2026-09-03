#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UTILS: Auto-Descoberta de Frota & Fallback Universal
aidd-project-generator v2.1

Detecta automaticamente quais agentes/harness estão instalados no host
e roteia por especialidade quando múltiplos estão disponíveis.

Ciclo:
1. Auto-descoberta: which/where para claude, codex, agy, opencode, etc.
2. Se múltiplos: roteia por especialidade (arquiteto→Claude, db→Codex, etc.)
3. Se apenas 1: modo "Agente Único Isolado" (todos workers no mesmo, em worktrees separadas)
4. Configurável via .env: ORCA_DEFAULT_HARNESS para forçar um único agente

Fallback em cascata:
  Delegado → Headless → Erro honesto (nunca silencioso)
"""

import sys
import os
import shutil
import json
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CONSTANTES — Agentes conhecidos e suas especialidades
# =============================================================================

AGENTES_CONHECIDOS = {
    'claude': {
        'comandos': ['claude'],
        'especialidades': ['arquitetura', 'analise', 'design', 'documentacao', 'codigo'],
        'prioridade': 1,
        'descricao': 'Claude Code (Anthropic)',
    },
    'codex': {
        'comandos': ['codex'],
        'especialidades': ['codigo', 'database', 'testes', 'refatoracao'],
        'prioridade': 2,
        'descricao': 'Codex (OpenAI)',
    },
    'opencode': {
        'comandos': ['opencode'],
        'especialidades': ['codigo', 'analise'],
        'prioridade': 3,
        'descricao': 'OpenCode',
    },
    'antigravity': {
        'comandos': ['agy', 'antigravity'],
        'especialidades': ['arquitetura', 'codigo', 'design', 'testes'],
        'prioridade': 2,
        'descricao': 'Antigravity (agy)',
    },
    'cursor': {
        'comandos': ['cursor'],
        'especialidades': ['codigo', 'design', 'frontend'],
        'prioridade': 3,
        'descricao': 'Cursor',
    },
    'gemini': {
        'comandos': ['gemini'],
        'especialidades': ['analise', 'codigo', 'documentacao'],
        'prioridade': 3,
        'descricao': 'Google Gemini CLI',
    },
    'mimocode': {
        'comandos': ['mimocode', 'mimo'],
        'especialidades': ['arquitetura', 'codigo', 'analise', 'design'],
        'prioridade': 2,
        'descricao': 'MimoCode Engine',
    },
    'ollama': {
        'comandos': ['ollama'],
        'especialidades': ['codigo', 'analise'],
        'prioridade': 4,
        'descricao': 'Ollama (local)',
    },
}

# Mapeamento de especialidade → agente preferido
ROTEAMENTO_ESPECIALIDADE = {
    'arquitetura': 'claude',
    'analise': 'claude',
    'design': 'claude',
    'documentacao': 'claude',
    'database': 'codex',
    'testes': 'codex',
    'refatoracao': 'codex',
    'codigo': 'claude',       # fallback: qualquer um serve
    'frontend': 'cursor',
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class AgenteDetectado:
    """Representa um agente/harness detectado no host."""
    nome: str
    comando: str
    caminho: str  # Path completo do executável
    especialidades: List[str]
    prioridade: int
    descricao: str
    ativo: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            'nome': self.nome,
            'comando': self.comando,
            'caminho': self.caminho,
            'especialidades': self.especialidades,
            'prioridade': self.prioridade,
            'descricao': self.descricao,
            'ativo': self.ativo,
        }


@dataclass
class FleetStatus:
    """Status completo da frota de agentes detectados."""
    agentes_detectados: List[AgenteDetectado] = field(default_factory=list)
    agente_default: Optional[str] = None
    modo: str = 'desconhecido'  # 'multi-agente', 'agente-unico', 'nenhum'
    override_config: Optional[str] = None  # ORCA_DEFAULT_HARNESS
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'agentes_detectados': [a.to_dict() for a in self.agentes_detectados],
            'total_detectados': len(self.agentes_detectados),
            'agente_default': self.agente_default,
            'modo': self.modo,
            'override_config': self.override_config,
            'timestamp': self.timestamp,
        }


# =============================================================================
# AUTO-DESCOBERTA
# =============================================================================

def _encontrar_executavel(comando: str) -> Optional[str]:
    """Encontra o caminho completo de um executável no PATH."""
    caminho = shutil.which(comando)
    return str(caminho) if caminho else None


def detectar_agentes_instalados() -> List[AgenteDetectado]:
    """
    Detecta automaticamente quais agentes/harness estão instalados no host.

    Usa shutil.which() para verificar se cada comando está no PATH.
    Retorna lista de agentes detectados (pode ser vazia).
    """
    agentes = []

    for nome, config in AGENTES_CONHECIDOS.items():
        for comando in config['comandos']:
            caminho = _encontrar_executavel(comando)
            if caminho:
                agente = AgenteDetectado(
                    nome=nome,
                    comando=comando,
                    caminho=caminho,
                    especialidades=config['especialidades'],
                    prioridade=config['prioridade'],
                    descricao=config['descricao'],
                )
                agentes.append(agente)
                break  # Encontrou um comando para este agente, não precisa testar os outros

    # Ordenar por prioridade (menor = melhor)
    agentes.sort(key=lambda a: a.prioridade)
    return agentes


def detectar_via_ambiente() -> List[str]:
    """
    Detecta agentes via variáveis de ambiente (complementar ao which/where).

    Útil quando o executável está no PATH mas queremos confirmar que está
    ativo (não apenas instalado).
    """
    detectados = []

    # Claude Code
    if os.environ.get('CLAUDECODE') == '1':
        detectados.append('claude')

    # MimoCode
    if os.environ.get('MIMOCODE') or os.environ.get('MIMO_SESSION') or os.environ.get('MIMO_WORKSPACE'):
        detectados.append('mimocode')

    # OpenCode
    if os.environ.get('OPENCODE') or os.environ.get('OPENCODE_SESSION'):
        detectados.append('opencode')

    # Antigravity / Gemini
    if os.environ.get('ANTIGRAVITY_CLI') or os.environ.get('AGY_SESSION'):
        detectados.append('antigravity')

    # ORCA
    if os.environ.get('ORCA_WORKSPACE'):
        detectados.append('orca')

    # AIDD_HARNESS_NAME (override explícito)
    harness_name = os.environ.get('AIDD_HARNESS_NAME')
    if harness_name:
        detectados.append(harness_name.lower())

    return list(set(detectados))


# =============================================================================
# ROTEAMENTO POR ESPECIALIDADE
# =============================================================================

def rotear_por_especialidade(
    especialidade: str,
    agentes_disponiveis: List[AgenteDetectado],
) -> Optional[AgenteDetectado]:
    """
    Escolhe o melhor agente para uma dada especialidade.

    Estratégia:
    1. Procura agente que tenha a especialidade E menor prioridade
    2. Se nenhum, usa o agente default (menor prioridade geral)
    3. Se nenhum agente disponível, retorna None
    """
    if not agentes_disponiveis:
        return None

    # 1. Procurar por especialidade específica
    agente_preferido = ROTEAMENTO_ESPECIALIDADE.get(especialidade)
    if agente_preferido:
        for agente in agentes_disponiveis:
            if agente.nome == agente_preferido:
                return agente

    # 2. Procurar qualquer agente que tenha a especialidade
    for agente in agentes_disponiveis:
        if especialidade in agente.especialidades:
            return agente

    # 3. Fallback: agente de maior prioridade (menor número)
    return agentes_disponiveis[0]


def resolver_fleet(
    override_harness: Optional[str] = None,
) -> FleetStatus:
    """
    Resolve o status completo da frota de agentes.

    Args:
        override_harness: Força um único agente (ORCA_DEFAULT_HARNESS)

    Returns:
        FleetStatus com agentes detectados, modo operacional e default
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    # Override via .env ou argumento
    override = override_harness or os.environ.get('ORCA_DEFAULT_HARNESS')

    # Auto-descoberta
    agentes = detectar_agentes_instalados()
    agentes_ambiente = detectar_via_ambiente()

    # Se override está configurado, filtrar apenas esse agente
    if override:
        override_lower = override.lower()
        agente_override = None
        for agente in agentes:
            if agente.nome == override_lower or agente.comando == override_lower:
                agente_override = agentes
                break

        if agente_override:
            # Encontrou o agente forçado — modo agente único
            return FleetStatus(
                agentes_detectados=[a for a in agentes if a.nome == override_lower or a.comando == override_lower],
                agente_default=override_lower,
                modo='agente-unico',
                override_config=override,
                timestamp=timestamp,
            )
        else:
            # Override aponta para agente não encontrado — honesto sobre isso
            return FleetStatus(
                agentes_detectados=[],
                agente_default=None,
                modo='nenhum',
                override_config=override,
                timestamp=timestamp,
            )

    # Sem override — auto-descoberta
    if len(agentes) >= 2:
        return FleetStatus(
            agentes_detectados=agentes,
            agente_default=agentes[0].nome,
            modo='multi-agente',
            timestamp=timestamp,
        )
    elif len(agentes) == 1:
        return FleetStatus(
            agentes_detectados=agentes,
            agente_default=agentes[0].nome,
            modo='agente-unico',
            timestamp=timestamp,
        )
    else:
        return FleetStatus(
            agentes_detectados=[],
            agente_default=None,
            modo='nenhum',
            timestamp=timestamp,
        )


# =============================================================================
# INTERFACE UNIFICADA — Integrar com utils_delegacao.py
# =============================================================================

def obter_modelo_para_fleet(fleet: FleetStatus, fase: str) -> Optional[str]:
    """
    Retorna o modelo apropriado para uma dada fase, baseado na frota.

    Em modo multi-agente: roteia por especialidade da fase.
    Em modo agente-unico: usa o único agente para tudo.
    Em modo nenhum: retorna None (vai para headless).
    """
    if fleet.modo == 'nenhum':
        return None

    # Mapeamento fase → especialidade
    fase_especialidade = {
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

    especialidade = fase_especialidade.get(fase, 'codigo')

    if fleet.modo == 'multi-agente':
        agente = rotear_por_especialidade(especialidade, fleet.agentes_detectados)
        return agente.nome if agente else fleet.agente_default
    else:
        return fleet.agente_default


def fleet_status_para_log(fleet: FleetStatus) -> str:
    """Retorna string legível do status da frota para logs."""
    linhas = [
        f"Frota: {fleet.modo}",
        f"Agentes detectados: {len(fleet.agentes_detectados)}",
    ]
    for agente in fleet.agentes_detectados:
        linhas.append(f"  - {agente.descricao} ({agente.comando}): {', '.join(agente.especialidades)}")

    if fleet.override_config:
        linhas.append(f"Override: {fleet.override_config}")

    linhas.append(f"Default: {fleet.agente_default or 'nenhum'}")
    return "\n".join(linhas)


def persistir_fleet_status(fleet: FleetStatus, pasta_cache: Optional[Path] = None):
    """Persiste o status da frota em disco para rastreabilidade."""
    pasta = pasta_cache or Path('.aidd/cache')
    pasta_data = pasta / 'data'
    pasta_data.mkdir(parents=True, exist_ok=True)

    caminho = pasta_data / '_fleet_status.json'
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(fleet.to_dict(), f, indent=2, ensure_ascii=False)

    return caminho


# =============================================================================
# TESTE RÁPIDO
# =============================================================================

if __name__ == '__main__':
    print("=== Fleet Discovery — Auto-Descoberta de Frota ===\n")

    # 1. Detectar agentes instalados
    print("1. Agentes instalados no host:")
    agentes = detectar_agentes_instalados()
    if agentes:
        for a in agentes:
            print(f"   ✓ {a.descricao} ({a.comando}) — {a.caminho}")
            print(f"     Especialidades: {', '.join(a.especialidades)}")
    else:
        print("   ⚠️ Nenhum agente detectado no PATH")

    # 2. Detectar via ambiente
    print("\n2. Agentes detectados via ambiente:")
    amb = detectar_via_ambiente()
    print(f"   {amb if amb else 'Nenhum'}")

    # 3. Resolver frota (sem override)
    print("\n3. Status da frota (auto):")
    fleet = resolver_fleet()
    print(fleet_status_para_log(fleet))

    # 4. Resolver frota (com override)
    print("\n4. Status da frota (override=claude):")
    fleet_override = resolver_fleet(override_harness='claude')
    print(fleet_status_para_log(fleet_override))

    # 5. Roteamento por especialidade
    if agentes:
        print("\n5. Roteamento por especialidade:")
        for esp in ['arquitetura', 'database', 'codigo', 'documentacao']:
            agente = rotear_por_especialidade(esp, agentes)
            print(f"   {esp} → {agente.descricao if agente else 'nenhum'}")

    print("\n✓ Fleet Discovery OK")
