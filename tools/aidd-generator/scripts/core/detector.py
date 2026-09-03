# -*- coding: utf-8 -*-
"""
Detector de ferramentas instaladas no host.

Detecta silenciosamente agentes/harness (claude, codex, agy, cursor, ollama)
e a presenca do ORCA ADE no sistema.

Zero dependencia externa — usa apenas shutil.which() e os.environ.
"""

import os
import shutil
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# =============================================================================
# CONSTANTES — Ferramentas conhecidas e seus comandos de deteccao
# =============================================================================

FERRAMENTAS_CONHECIDAS: Dict[str, Dict] = {
    'claude': {
        'comandos': ['claude'],
        'descricao': 'Claude Code (Anthropic)',
        'especialidades': ['arquitetura', 'analise', 'design', 'documentacao', 'codigo'],
        'prioridade': 1,
    },
    'codex': {
        'comandos': ['codex'],
        'descricao': 'Codex (OpenAI)',
        'especialidades': ['codigo', 'database', 'testes', 'refatoracao'],
        'prioridade': 2,
    },
    'agy': {
        'comandos': ['agy', 'antigravity'],
        'descricao': 'Antigravity (agy)',
        'especialidades': ['arquitetura', 'codigo', 'design', 'testes'],
        'prioridade': 2,
    },
    'cursor': {
        'comandos': ['cursor'],
        'descricao': 'Cursor',
        'especialidades': ['codigo', 'design', 'frontend'],
        'prioridade': 3,
    },
    'ollama': {
        'comandos': ['ollama'],
        'descricao': 'Ollama (local)',
        'especialidades': ['codigo', 'analise'],
        'prioridade': 4,
    },
}

# Sinais ambientais que indicam presenca do ORCA ADE
ORCA_AMBIENTE_SINAIS = [
    'ORCA_WORKSPACE',
    'ORCA_WORKTREE_ID',
    'ORCA_FLEET_ID',
    'ORCA_ADE',
]


# =============================================================================
# DATA CLASS — Resultado de uma unica deteccao
# =============================================================================

@dataclass
class FerramentaDetectada:
    """Uma ferramenta detectada no host."""
    nome: str
    comando: str
    caminho: str
    descricao: str
    especialidades: List[str] = field(default_factory=list)
    prioridade: int = 99

    def to_dict(self) -> Dict:
        return {
            'nome': self.nome,
            'comando': self.comando,
            'caminho': self.caminho,
            'descricao': self.descricao,
            'especialidades': self.especialidades,
            'prioridade': self.prioridade,
        }


@dataclass
class DetectorResultado:
    """Resultado completo da deteccao do host."""
    ferramentas: List[FerramentaDetectada] = field(default_factory=list)
    orca_presente: bool = False
    orca_sinais: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'ferramentas': [f.to_dict() for f in self.ferramentas],
            'total_ferramentas': len(self.ferramentas),
            'orca_presente': self.orca_presente,
            'orca_sinais': self.orca_sinais,
        }


# =============================================================================
# FUNCOES DE DETECCAO
# =============================================================================

def _encontrar_executavel(comando: str) -> Optional[str]:
    """Encontra caminho completo de um executavel no PATH. Silencioso."""
    caminho = shutil.which(comando)
    return str(caminho) if caminho else None


def detectar_ferramentas() -> List[FerramentaDetectada]:
    """
    Detecta ferramentas instaladas no host de forma silenciosa.

    Para cada ferramenta conhecida, testa se algum de seus comandos
    esta disponivel no PATH via shutil.which().

    Retorna lista ordenada por prioridade (menor = melhor).
    """
    detectadas: List[FerramentaDetectada] = []

    for nome, config in FERRAMENTAS_CONHECIDAS.items():
        for comando in config['comandos']:
            caminho = _encontrar_executavel(comando)
            if caminho:
                detectadas.append(FerramentaDetectada(
                    nome=nome,
                    comando=comando,
                    caminho=caminho,
                    descricao=config['descricao'],
                    especialidades=config['especialidades'],
                    prioridade=config['prioridade'],
                ))
                break  # achou um comando, nao precisa testar aliases

    detectadas.sort(key=lambda f: f.prioridade)
    return detectadas


def detectar_orca_ade() -> bool:
    """
    Detecta a presenca do ORCA ADE no sistema.

    Verifica variaveis de ambiente associadas ao ORCA.
    Retorna True se pelo menos um sinal for encontrado.
    """
    return any(os.environ.get(sinal) for sinal in ORCA_AMBIENTE_SINAIS)


def obter_sinais_orca() -> List[str]:
    """Retorna lista de sinais ORCA encontrados no ambiente."""
    return [s for s in ORCA_AMBIENTE_SINAIS if os.environ.get(s)]


def executar_deteccao_completa() -> DetectorResultado:
    """
    Executa deteccao completa do host: ferramentas + ORCA ADE.

    Retorna DetectorResultado com tudo que foi encontrado.
    """
    return DetectorResultado(
        ferramentas=detectar_ferramentas(),
        orca_presente=detectar_orca_ade(),
        orca_sinais=obter_sinais_orca(),
    )
