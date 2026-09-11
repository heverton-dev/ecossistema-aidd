# -*- coding: utf-8 -*-
"""Pacote formal das 8 fases do aidd-generator.

Substitui o hack de mutação manual de sys.path + spec_from_file_location por um
pacote Python estruturado com carregamento lazy (Apenas UMA fase em memória
por vez).

- As fases são membros reais do pacote (`phases.<script>`), importáveis via
  ``importlib.import_module('phases.02_analisador')`` — sem mutação de sys.path.
- Cada arquivo de fase faz import relativo (``.utils_modelo``) com fallback bare
  (``from utils_modelo import ...``) para preservar também a execução direta
  (``python scripts/phases/02_analisador.py``) documentada no projeto.
- Os micro-ambientes (pastas phase_NN_* com AGENTS.md) continuam sendo a fonte
  de contexto isolado para cada fase.
"""

import importlib
from pathlib import Path

PHASES_DIR = Path(__file__).parent


# =============================================================================
# REGISTRY DE FASES — mapeamento centralizado fase → (alias, script, micro-ambiente)
# =============================================================================

FASE_REGISTRY = {
    1: {'alias': 'pipeline_p1', 'script': '01_pesquisador.py', 'micro_env': 'phase_01_pesquisa'},
    2: {'alias': 'pipeline_p2', 'script': '02_analisador.py', 'micro_env': 'phase_02_analisador'},
    3: {'alias': 'pipeline_p3', 'script': '03_designer.py', 'micro_env': 'phase_03_designer'},
    4: {'alias': 'pipeline_p4', 'script': '04_decisor.py', 'micro_env': 'phase_04_planejador'},
    5: {'alias': 'pipeline_p5', 'script': '05_criador.py', 'micro_env': 'phase_05_criador'},
    6: {'alias': 'pipeline_p6', 'script': '06_documentador.py', 'micro_env': 'phase_06_documentador'},
    7: {'alias': 'pipeline_p7', 'script': '07_analisador.py', 'micro_env': 'phase_07_auto_critica'},
    8: {'alias': 'pipeline_p8', 'script': '08_implementador.py', 'micro_env': 'phase_08_implementador'},
}

# Alias de compatibilidade (mesmo objeto compartilhado com o pipeline).
_FASE_REGISTRY = FASE_REGISTRY

# Cache de módulos carregados (apenas 1 fase por vez em memória)
modulo_cache: dict = {}


def _nome_modulo_fase(numero_fase: int) -> str:
    """Retorna o nome canônico do módulo no pacote para uma fase (ex: phases.02_analisador)."""
    return f'phases.{FASE_REGISTRY[numero_fase]["script"][:-3]}'


def carregar_fase(numero_fase: int):
    """Carrega dinamicamente o módulo da fase indicada.

    Estratégia de economia de tokens:
    - Apenas UMA fase fica em memória por vez
    - Ao carregar uma nova fase, a anterior é descartada (del + gc)
    - O AGENTS.md do micro-ambiente é lido como contexto isolado
    - Evita manter todas as fases em memória simultaneamente (carregamento sob demanda)
    """
    if numero_fase not in FASE_REGISTRY:
        raise ValueError(f'Fase {numero_fase} não encontrada no registry')

    # Descartar fase anterior se existir (economia de memória/tokens)
    chaves_anteriores = [k for k in modulo_cache if k != numero_fase]
    for chave in chaves_anteriores:
        del modulo_cache[chave]

    # Se já está em cache, retorna direto
    if numero_fase in modulo_cache:
        return modulo_cache[numero_fase]

    # Carregar módulo da fase como membro real do pacote (lazy, sem sys.path)
    modulo = importlib.import_module(_nome_modulo_fase(numero_fase))
    modulo_cache[numero_fase] = modulo
    return modulo


def carregar_micro_ambiente(numero_fase: int) -> str:
    """Lê o AGENTS.md do micro-ambiente da fase como contexto isolado.

    Retorna o conteúdo do AGENTS.md ou string vazia se não existir.
    Este contexto é usado internamente pela fase para auto-orientação.
    """
    reg = FASE_REGISTRY.get(numero_fase)
    if not reg:
        return ''

    agents_path = PHASES_DIR / reg['micro_env'] / 'AGENTS.md'
    if agents_path.exists():
        return agents_path.read_text(encoding='utf-8')
    return ''


def descarregar_todas_fases():
    """Remove todos os módulos de fase da memória."""
    modulo_cache.clear()