#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PIPELINE COMPLETO — aidd-project-generator v2.2
Orquestra as Fases 1-7 (ou 1-8 com --implementar-codigo) ponta a ponta,
encadeando os dados reais que cada fase persiste em
<pasta>/.aidd/cache/data/ (não fabrica nem reaproveita dados de outra
execução).

Uso:
    python scripts/pipeline_completo.py "ideia do projeto" --pasta ../MEU-PROJETO
    python scripts/pipeline_completo.py "ideia do projeto" --pasta ../MEU-PROJETO --interativo
    python scripts/pipeline_completo.py "ideia do projeto" --pasta ../MEU-PROJETO --implementar-codigo

Ordem padrão (sem --implementar-codigo): 1→2→3→4→5→6→7
Ordem com --implementar-codigo:           1→2→3→4→5→8→6→7

--implementar-codigo roda a Fase 8 (implementação funcional real com
testes e loop de correção via LLM) logo após a Fase 5, ANTES de
Fase 6/7 — assim a documentação (Fase 6) reflete o código real e a
auto-crítica (Fase 7) audita o projeto funcional completo.

Sem fallback silencioso: se qualquer fase falhar (retornar None), o
pipeline para imediatamente e reporta exatamente qual fase e por quê —
nunca segue adiante com dado fabricado ou fase pulada.

Inovações v2.2:
- Fleet Discovery: auto-descoberta de agentes instalados no host
- Context-Purge Engine: subagentes efêmeros com descarte imediato de contexto
- Intent Router: detecção de intenção para /generate e linguagem natural
- Micro-ambientes: cada fase tem AGENTS.md com regras isoladas
- Carregamento dinâmico: apenas o micro-ambiente da fase em execução é
  carregado em memória (evita manter todas as fases simultaneamente)

Consolidação v2.4 (Item 2 — unificar-orquestradores-generator-e-ops):
- Este arquivo é o ÚNICO orquestrador canônico do pipeline. A orquestração
  genérica via Prefect (retries, checkpointing, persistência) que antes vivia
  em scripts/pipeline_prefect.py agora vive aqui, sem duplicidade: mesmo fluxo,
  mesmas fases, mesmo protocolo delegado. Use --orquestrador prefect para
  ativá-la.
- scripts/pipeline_prefect.py é apenas um shim de compatibilidade (deprecado)
  que reexporta os símbolos públicos a partir desta fonte única.
"""

import sys
import os
import json
import time
import hashlib
from types import SimpleNamespace
from pathlib import Path
from typing import Any

import click

# Escritor atômico: staging → fsync → os.replace
try:
    from escritor_atomico import escrever_json_atomico
except ImportError:
    import importlib.util
    _comp_dir = os.path.join(
        os.path.dirname(__file__), "..", "..", "componentes", "compartilhado", "src-core"
    )
    if os.path.isdir(_comp_dir) and _comp_dir not in sys.path:
        sys.path.insert(0, _comp_dir)
    from escritor_atomico import escrever_json_atomico

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Pré-voo LLM (verifica LLM_MODEL + credencial antes de rodar o pipeline)
# Imports absolutos via pacote: `phases`, `core` e `preflight_llm` resolvem
# porque este módulo sempre roda com scripts/ no sys.path (script main ou
# spec-load com scripts/ inserido nos testes). Zero mutação manual de sys.path.
from preflight_llm import verificar_llm_pronto  # noqa: E402
from phases.utils_delegacao import LLMNaoConfiguradoException
from phases.utils_fleet_discovery import resolver_fleet, fleet_status_para_log, persistir_fleet_status
from phases.utils_subagente_ephemero import ContextPurgeEngine
from core.repomix_runner import empacotar_repositorio, repomix_disponivel


# =============================================================================
# REGISTRY DE FASES — fonte canônica no pacote `phases` (carregamento lazy)
# =============================================================================
# O registry, o cache e os carregadores vivem em scripts/phases/__init__.py.
# Aqui são apenas re-exportados (mesmos objetos), preservando a API pública
# usada pelo pipeline e pelos testes (carregamento lazy, evict de 1 fase por
# vez, micro-ambiente isolado por AGENTS.md — sem mutação de sys.path).

from phases import (  # noqa: E402
    FASE_REGISTRY as _FASE_REGISTRY,
    modulo_cache as _modulo_cache,
    carregar_fase as _carregar_fase,
    carregar_micro_ambiente as _carregar_micro_ambiente,
    descarregar_todas_fases as _descarregar_todas_fases,
)


# =============================================================================
# ORÇAMENTO DE TOKENS POR FASE (Item 7 — 02-otimizacao-tokenomics-latencia)
# =============================================================================

_CONFIG_DIR = Path(__file__).resolve().parent.parent / 'config'
_TOKEN_BUDGETS_PATH = _CONFIG_DIR / 'token_budgets.json'


def _carregar_orcamento_fases() -> dict:
    """Carrega token_budgets.json. Retorna dict vazio se arquivo não existir."""
    if not _TOKEN_BUDGETS_PATH.exists():
        return {}
    try:
        dados = json.loads(_TOKEN_BUDGETS_PATH.read_text(encoding='utf-8'))
        return dados.get('fases', {})
    except (json.JSONDecodeError, OSError):
        return {}


def _registrar_e_verificar_orcamento(
    resultado_fase: dict, nome_fase: str, num_fase: int,
    orcamentos: dict, estado_path: Path
) -> None:
    """Registra tokens utilizados vs orçamento e emite alerta se desvio > 20%."""
    if not orcamentos:
        return
    chave = f'fase_{num_fase}'
    if chave not in orcamentos:
        return
    budget = orcamentos[chave]
    orcamento_tokens = budget.get('orcamento_tokens', 0)
    if orcamento_tokens <= 0:
        return

    # Extrair tokens consumidos da fase (se disponível)
    tokens_utilizados = 0
    if isinstance(resultado_fase, dict):
        tokens_utilizados = resultado_fase.get('tokens_consumidos', 0)
    elif isinstance(resultado_fase, str):
        # Índice JSON — tentar extrair de campo específico
        try:
            dados = json.loads(resultado_fase)
            tokens_utilizados = dados.get('tokens_consumidos', 0)
        except (json.JSONDecodeError, TypeError):
            pass

    if tokens_utilizados <= 0:
        return

    registro = {
        'fase': nome_fase,
        'num_fase': num_fase,
        'orcamento_tokens': orcamento_tokens,
        'tokens_utilizados': tokens_utilizados,
        'desvio_pct': round((tokens_utilizados / orcamento_tokens - 1) * 100, 1),
    }

    # Alerta se desvio > 20%
    limiar = 1.2
    if tokens_utilizados > orcamento_tokens * limiar:
        print(f"   ⚠️  ORÇAMENTO: Fase {num_fase} ({nome_fase}) usou {tokens_utilizados} tokens "
              f"(orcamento: {orcamento_tokens}, desvio: +{registro['desvio_pct']:.1f}%)")

    # Salvar no _pipeline_state.json
    estado = {}
    if estado_path.exists():
        try:
            estado = json.loads(estado_path.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, OSError):
            estado = {}
    if 'orcamento_fases' not in estado:
        estado['orcamento_fases'] = {}
    estado['orcamento_fases'][chave] = registro
    escrever_json_atomico(estado_path, estado)


# =============================================================================
# FALHA
# =============================================================================

def _falhar(resultado: dict, fase: str, t0: float) -> dict:
    resultado['status'] = 'FALHOU'
    resultado['fase_que_falhou'] = fase
    resultado['duracao_segundos'] = time.time() - t0
    _descarregar_todas_fases()
    return resultado


# =============================================================================
# ORQUESTRAÇÃO GENÉRICA OPCIONAL (Prefect) — fonte única consolidada
# =============================================================================
# A partir do Item 2 (unificar-orquestradores-generator-e-ops), a orquestração
# genérica via Prefect que vivia em scripts/pipeline_prefect.py passou a viver
# NESTE módulo — o único orquestrador canônico do pipeline — sem duplicidade.
# O Prefect entra como MOTOR GENÉRICO por cima da MESMA lógica de domínio das
# 8 fases e do MESMO protocolo delegado (utils_delegacao.py); nunca
# reimplementa fase nem decisão de negócio.
# scripts/pipeline_prefect.py é mantido apenas como shim de compatibilidade
# (deprecado oficialmente) que reexporta os símbolos públicos definidos daqui.

# --- Pré-voo de ambiente: uma instância limpa e determinística do Prefect -----
def resolver_prefect_home() -> str:
    """Resolve o PREFECT_HOME efetivo a partir de AIDD_PREFECT_HOME.

    Expõe o cálculo também ao shim scripts/pipeline_prefect.py, que recalcula
    `_PREFECT_HOME` no reload para refletir mudanças do ambiente em tempo de
    execução sem duplicar a lógica de resolução.
    """
    return os.environ.get(
        'AIDD_PREFECT_HOME',
        str((Path(__file__).resolve().parent.parent / '.aidd' / 'prefect').resolve()),
    )


_PREFECT_HOME = resolver_prefect_home()
os.environ.setdefault('PREFECT_HOME', _PREFECT_HOME)
# Telemetria desligada: evita corrida de banco (SQLite locked) em runs
# efêmeras e mantém a run auditável localmente sem exfiltração de metadados.
os.environ['PREFECT_TELEMETRY_ENABLED'] = 'false'
os.environ['PREFECT_SERVER_ENABLE_UI'] = 'false'
os.environ['PREFECT_API_BLOCK_ON_INIT_SEPARATELY'] = 'false'

# `task`/`flow`/`get_run_logger` são tipos Any em nível de módulo: quando o
# Prefect está instalado recebem o decorator real; quando não, um fallback
# identidade que mantém o módulo importável (diagnóstico via
# `disponibilidade_prefect()`). A tipagem precisa dos decorators do Prefect
# não é propagada para cá de propósito (degradação graciosa).
task: Any
flow: Any
get_run_logger: Any
_PREFECT_IMPORT_OK = False
_PREFECT_IMPORT_ERRO: Exception | None = None

try:
    from prefect import flow as _prefect_flow  # type: ignore[no-redef]
    from prefect import task as _prefect_task  # type: ignore[no-redef]
    from prefect.logging import get_run_logger as _prefect_logger  # type: ignore[no-redef]
    _PREFECT_IMPORT_OK = True
    task = _prefect_task
    flow = _prefect_flow
    get_run_logger = _prefect_logger
except Exception as _e:  # pragma: no cover - falha de import é diagnóstica
    _PREFECT_IMPORT_OK = False
    _PREFECT_IMPORT_ERRO = _e

    def _decorator_identidade(*_a, **_k):
        def _deco(fn):
            return fn
        return _deco

    task = _decorator_identidade
    flow = _decorator_identidade
    get_run_logger = lambda *_a, **_k: SimpleNamespace(  # noqa: E731
        info=lambda *x, **y: None,
        debug=lambda *x, **y: None,
        warning=lambda *x, **y: None,
        error=lambda *x, **y: None,
        exception=lambda *x, **y: None,
    )


# =============================================================================
# CONFIGURAÇÃO DE ORQUESTRAÇÃO GENÉRICA (a delegável ao Prefect)
# =============================================================================
#
# Número de retries e o atraso entre tentativas por perfil de fase. Fases de
# síntese/implementação (que dependem de ADE/LLM) têm mais tolerância a falha
# transitória; fases puramente mecânicas já são determinísticas e não precisam
# de retry agressivo.

_RETRIES = {
    'fase_1_pesquisador': {'retries': 2, 'retry_delay_seconds': 2.0},
    'fase_2_analisador': {'retries': 3, 'retry_delay_seconds': 3.0},
    'fase_3_designer': {'retries': 3, 'retry_delay_seconds': 3.0},
    'fase_4_planejador': {'retries': 1, 'retry_delay_seconds': 2.0},
    'fase_5_criador': {'retries': 2, 'retry_delay_seconds': 2.0},
    'fase_6_documentador': {'retries': 3, 'retry_delay_seconds': 3.0},
    'fase_7_auto_critica': {'retries': 2, 'retry_delay_seconds': 2.0},
    'fase_8_implementador': {'retries': 3, 'retry_delay_seconds': 5.0},
}


def _chave_checkpoint(ideia: str, fase: str) -> str:
    """Chave de cache deterministicamente vinculada a (ideia, fase).

    Permite que o Prefect pule fases já concluídas numa reexecução (resume):
    a mesma ideia + mesma fase produz a MESMA chave, então a task retorna o
    estado persistido e não é reexecutada. Preserva o determinismo do pipeline.
    """
    h = hashlib.sha256(f'{ideia.strip().lower()}'.encode('utf-8')).hexdigest()[:16]
    return f'{fase}:{h}'


def _cache_por_fase(fase: str):
    def _cache_key_fn(ctx, parametros):
        ideia = (parametros.get('ideia') or '') if isinstance(parametros, dict) else ''
        return _chave_checkpoint(str(ideia), fase)
    return _cache_key_fn


# =============================================================================
# WRAPPERS DE FASE (lógica de domínio preservada, retry/persistência delegada)
# =============================================================================
# Cada wrapper reutiliza a classe de domínio original (exatamente a mesma de
# executar_pipeline acima); só a ORQUESTRAÇÃO (retry/cache/persistência) é
# delegada ao decorator @task do Prefect.

@task(retries=_RETRIES['fase_1_pesquisador']['retries'],
      retry_delay_seconds=_RETRIES['fase_1_pesquisador']['retry_delay_seconds'],
      persist_result=True, cache_key_fn=_cache_por_fase('fase_1_pesquisador'))
def _task_fase_1(ideia: str, cache_dir: str):
    _carregar_micro_ambiente(1)
    p1 = _carregar_fase(1)
    return p1.PesquisadorFase1(Path(cache_dir)).executar(ideia)


@task(retries=_RETRIES['fase_2_analisador']['retries'],
      retry_delay_seconds=_RETRIES['fase_2_analisador']['retry_delay_seconds'],
      persist_result=True, cache_key_fn=_cache_por_fase('fase_2_analisador'))
def _task_fase_2(ideia: str, cache_dir: str, referencias: dict):
    _carregar_micro_ambiente(2)
    p2 = _carregar_fase(2)
    return p2.AnalisadorFase2(Path(cache_dir)).executar(ideia, referencias)


@task(retries=_RETRIES['fase_3_designer']['retries'],
      retry_delay_seconds=_RETRIES['fase_3_designer']['retry_delay_seconds'],
      persist_result=True, cache_key_fn=_cache_por_fase('fase_3_designer'))
def _task_fase_3(ideia: str, cache_dir: str, analise: dict):
    _carregar_micro_ambiente(3)
    p3 = _carregar_fase(3)
    return p3.DesignerFase3(Path(cache_dir)).executar(ideia, analise)


@task(retries=_RETRIES['fase_4_planejador']['retries'],
      retry_delay_seconds=_RETRIES['fase_4_planejador']['retry_delay_seconds'],
      persist_result=True, cache_key_fn=_cache_por_fase('fase_4_planejador'))
def _task_fase_4(ideia: str, cache_dir: str, design: dict, nao_interativo: bool):
    _carregar_micro_ambiente(4)
    p4 = _carregar_fase(4)
    return p4.DecisorFase4(Path(cache_dir)).executar(design, nao_interativo=nao_interativo)


@task(retries=_RETRIES['fase_5_criador']['retries'],
      retry_delay_seconds=_RETRIES['fase_5_criador']['retry_delay_seconds'],
      persist_result=True, cache_key_fn=_cache_por_fase('fase_5_criador'))
def _task_fase_5(ideia: str, pasta_projeto: str, config_fase4: dict):
    _carregar_micro_ambiente(5)
    p5 = _carregar_fase(5)
    return p5.CriadorProjetoFase5(Path(pasta_projeto)).executar(ideia, config_fase4)


@task(retries=_RETRIES['fase_8_implementador']['retries'],
      retry_delay_seconds=_RETRIES['fase_8_implementador']['retry_delay_seconds'],
      persist_result=True, cache_key_fn=_cache_por_fase('fase_8_implementador'))
def _task_fase_8(ideia: str, pasta_projeto: str, analise: dict, design: dict):
    _carregar_micro_ambiente(8)
    p8 = _carregar_fase(8)
    return p8.ImplementadorFase8(Path(pasta_projeto)).executar(ideia, analise, design)


@task(retries=_RETRIES['fase_6_documentador']['retries'],
      retry_delay_seconds=_RETRIES['fase_6_documentador']['retry_delay_seconds'],
      persist_result=True, cache_key_fn=_cache_por_fase('fase_6_documentador'))
def _task_fase_6(cache_dir: str, output_base: str, nome_projeto: str,
                 contexto_doc: dict, ideia: str):
    _carregar_micro_ambiente(6)
    p6 = _carregar_fase(6)
    return p6.DocumentadorFase6(
        pasta_cache=Path(cache_dir), output_base=Path(output_base)
    ).executar(nome_projeto, contexto_doc, titulo=ideia)


@task(retries=_RETRIES['fase_7_auto_critica']['retries'],
      retry_delay_seconds=_RETRIES['fase_7_auto_critica']['retry_delay_seconds'],
      persist_result=True, cache_key_fn=_cache_por_fase('fase_7_auto_critica'))
def _task_fase_7(ideia: str, pasta_projeto: str):
    _carregar_micro_ambiente(7)
    p7 = _carregar_fase(7)
    return p7.AnalisadorCriticoAutomatico(Path(pasta_projeto)).executar()


# =============================================================================
# FLOW PREFECT — orquestração genérica (retries, checkpoints, persistência)
# =============================================================================

@flow(name='aidd-generator-pipeline', version='2.3', log_prints=True)
def executar_pipeline_prefect(ideia: str, pasta_projeto: str,
                              nao_interativo: bool = True,
                              implementar_codigo: bool = False) -> dict:
    """Flow Prefect que orquestra as fases 1-8 com retries + checkpointing.

    Mantém o contrato de dados por arquivo JSON idêntico ao pipeline legado,
    preservando o protocolo delegado (ADE) e a lógica de domínio de cada fase.
    """
    logger = get_run_logger()
    proj_dir = Path(pasta_projeto)
    cache_dir = str((proj_dir / '.aidd' / 'cache').resolve())
    data_dir = proj_dir / '.aidd' / 'cache' / 'data'
    total_fases = 8 if implementar_codigo else 7

    resultado = {'ideia': ideia, 'pasta': str(proj_dir), 'fases_completas': {}}
    t0 = time.time()

    def _falhar(fase: str) -> dict:
        resultado['status'] = 'FALHOU'
        resultado['fase_que_falhou'] = fase
        resultado['duracao_segundos'] = time.time() - t0
        return resultado

    # --- FASE 1 ---
    logger.info('FASE 1/%s — Pesquisador', total_fases)
    idx1 = _task_fase_1(ideia, cache_dir)
    resultado['fases_completas']['fase_1'] = idx1 is not None
    if idx1 is None:
        return _falhar('fase_1_pesquisador')

    insights_path = data_dir / 'insights_phase1.json'
    referencias = json.loads(insights_path.read_text(encoding='utf-8')) if insights_path.exists() else {}

    # --- FASE 2 ---
    logger.info('FASE 2/%s — Analisador', total_fases)
    idx2 = _task_fase_2(ideia, cache_dir, referencias)
    resultado['fases_completas']['fase_2'] = idx2 is not None
    if idx2 is None:
        return _falhar('fase_2_analisador')
    analise = json.loads((data_dir / 'analise_phase2.json').read_text(encoding='utf-8'))

    # --- FASE 3 ---
    logger.info('FASE 3/%s — Designer', total_fases)
    idx3 = _task_fase_3(ideia, cache_dir, analise)
    resultado['fases_completas']['fase_3'] = idx3 is not None
    if idx3 is None:
        return _falhar('fase_3_designer')
    design = json.loads((data_dir / 'design_aidd_phase3.json').read_text(encoding='utf-8'))

    # --- FASE 4 ---
    logger.info('FASE 4/%s — Planejador', total_fases)
    idx4 = _task_fase_4(ideia, cache_dir, design, nao_interativo)
    resultado['fases_completas']['fase_4'] = idx4 is not None
    if idx4 is None:
        return _falhar('fase_4_planejador')
    config_fase4 = json.loads((data_dir / 'config_global_local_phase4.json').read_text(encoding='utf-8'))

    # --- FASE 5 ---
    logger.info('FASE 5/%s — Criador', total_fases)
    idx5 = _task_fase_5(ideia, str(proj_dir), config_fase4)
    resultado['fases_completas']['fase_5'] = idx5 is not None
    if idx5 is None:
        return _falhar('fase_5_criador')

    # --- FASE 8 (condicional, antes de 6/7 quando --implementar-codigo) ---
    if implementar_codigo:
        logger.info('FASE 8/%s — Implementador', total_fases)
        idx8 = _task_fase_8(ideia, str(proj_dir), analise, design)
        resultado['fases_completas']['fase_8'] = idx8 is not None and idx8.get('status') == 'COMPLETO'
        if not resultado['fases_completas']['fase_8']:
            return _falhar('fase_8_implementador')

    # --- FASE 6 ---
    logger.info('FASE 6/%s — Documentador', total_fases)
    contexto_doc = {**analise, **design}
    idx6 = _task_fase_6(cache_dir, str(proj_dir / 'output'),
                        proj_dir.name, contexto_doc, ideia)
    resultado['fases_completas']['fase_6'] = idx6 is not None and idx6.get('status') == 'COMPLETO'
    if not resultado['fases_completas']['fase_6']:
        return _falhar('fase_6_documentador')

    # --- FASE 7 ---
    logger.info('FASE 7/%s — Auto-crítica', total_fases)
    idx7 = _task_fase_7(ideia, str(proj_dir))
    resultado['fases_completas']['fase_7'] = idx7.get('status') == 'COMPLETO'
    resultado['score_final'] = idx7.get('score')

    resultado['status'] = 'COMPLETO'
    resultado['duracao_segundos'] = time.time() - t0
    return resultado


# =============================================================================
# DIAGNÓSTICO / GATE MECÂNICO
# =============================================================================

def disponibilidade_prefect() -> tuple:
    """Retorna (ok, mensagem) sobre a disponibilidade do motor Prefect.

    Usado pela CLI (`--orquestrador prefect`) para decidir se o motor é
    viável e pela suíte de testes para pular quando o env não estiver limpo.
    """
    if not _PREFECT_IMPORT_OK:
        return False, f'Prefect não importável: {_PREFECT_IMPORT_ERRO}'
    return True, f'Prefect disponível (PREFECT_HOME={_PREFECT_HOME})'


# =============================================================================
# PIPELINE PRINCIPAL
# =============================================================================

def executar_pipeline(ideia: str, pasta_projeto: Path, nao_interativo: bool = True,
                       implementar_codigo: bool = False) -> dict:
    """Executa as fases em sequência, real, sem mock, sem fallback silencioso.

    Ordem padrão (sem --implementar-codigo): 1→2→3→4→5→6→7
    Ordem com --implementar-codigo:           1→2→3→4→5→8→6→7

    Fase 8 roda ANTES de Fase 6/7 quando --implementar-codigo é usado,
    assim a documentação (Fase 6) reflete o código real implementado e
    a auto-crítica (Fase 7) audita o projeto funcional completo — não
    apenas a intenção de design.

    Carregamento dinâmico: cada fase é carregada sob demanda e descartada
    após execução (evita manter todas as fases simultaneamente em memória).
    """
    pasta_projeto = Path(pasta_projeto)
    cache_dir = pasta_projeto / '.aidd' / 'cache'
    data_dir = cache_dir / 'data'
    total_fases = 8 if implementar_codigo else 7

    # Orçamento de tokens por fase (Item 7)
    orcamentos = _carregar_orcamento_fases()
    pipeline_state_path = cache_dir / '_pipeline_state.json'

    resultado = {'ideia': ideia, 'pasta': str(pasta_projeto), 'fases_completas': {}}
    t0 = time.time()

    # Fleet Discovery: auto-detectar agentes instalados no host
    fleet = resolver_fleet()
    resultado['fleet'] = fleet.to_dict()
    print(f"\n🔍 Fleet Discovery:")
    print(fleet_status_para_log(fleet))
    persistir_fleet_status(fleet, pasta_cache=cache_dir)

    # Context-Purge Engine: inicializar para métricas de subagentes efêmeros
    purge_engine = ContextPurgeEngine(pasta_cache=cache_dir)

    # --- FASE 1: Pesquisador (carregamento dinâmico) ---
    print("\n" + "=" * 70)
    print(f"PIPELINE COMPLETO: FASE 1/{total_fases} — Pesquisador")
    print("=" * 70)
    ctx1 = _carregar_micro_ambiente(1)
    p1 = _carregar_fase(1)
    idx1 = p1.PesquisadorFase1(cache_dir).executar(ideia)
    resultado['fases_completas']['fase_1'] = idx1 is not None
    _registrar_e_verificar_orcamento(idx1 or {}, 'Pesquisador', 1, orcamentos, pipeline_state_path)
    if idx1 is None:
        return _falhar(resultado, 'fase_1_pesquisador', t0)

    insights_path = data_dir / 'insights_phase1.json'
    referencias = json.loads(insights_path.read_text(encoding='utf-8')) if insights_path.exists() else {}

    # --- FASE 2: Analisador (carregamento dinâmico) ---
    print("\n" + "=" * 70)
    print(f"PIPELINE COMPLETO: FASE 2/{total_fases} — Analisador")
    print("=" * 70)
    ctx2 = _carregar_micro_ambiente(2)
    p2 = _carregar_fase(2)
    idx2 = p2.AnalisadorFase2(cache_dir).executar(ideia, referencias)
    resultado['fases_completas']['fase_2'] = idx2 is not None
    _registrar_e_verificar_orcamento(idx2 or {}, 'Analisador', 2, orcamentos, pipeline_state_path)
    if idx2 is None:
        return _falhar(resultado, 'fase_2_analisador', t0)

    analise = json.loads((data_dir / 'analise_phase2.json').read_text(encoding='utf-8'))

    # --- FASE 3: Designer (carregamento dinâmico) ---
    print("\n" + "=" * 70)
    print(f"PIPELINE COMPLETO: FASE 3/{total_fases} — Designer")
    print("=" * 70)
    ctx3 = _carregar_micro_ambiente(3)
    p3 = _carregar_fase(3)
    idx3 = p3.DesignerFase3(cache_dir).executar(ideia, analise)
    resultado['fases_completas']['fase_3'] = idx3 is not None
    _registrar_e_verificar_orcamento(idx3 or {}, 'Designer', 3, orcamentos, pipeline_state_path)
    if idx3 is None:
        return _falhar(resultado, 'fase_3_designer', t0)

    design = json.loads((data_dir / 'design_aidd_phase3.json').read_text(encoding='utf-8'))

    # --- FASE 4: Planejador (carregamento dinâmico) ---
    print("\n" + "=" * 70)
    print(f"PIPELINE COMPLETO: FASE 4/{total_fases} — Planejador")
    print("=" * 70)
    ctx4 = _carregar_micro_ambiente(4)
    p4 = _carregar_fase(4)
    idx4 = p4.DecisorFase4(cache_dir).executar(design, nao_interativo=nao_interativo)
    resultado['fases_completas']['fase_4'] = idx4 is not None
    _registrar_e_verificar_orcamento(idx4 or {}, 'Planejador', 4, orcamentos, pipeline_state_path)
    if idx4 is None:
        return _falhar(resultado, 'fase_4_planejador', t0)

    config_fase4 = json.loads((data_dir / 'config_global_local_phase4.json').read_text(encoding='utf-8'))

    # --- FASE 5: Criador (carregamento dinâmico) ---
    print("\n" + "=" * 70)
    print(f"PIPELINE COMPLETO: FASE 5/{total_fases} — Criador")
    print("=" * 70)
    ctx5 = _carregar_micro_ambiente(5)
    p5 = _carregar_fase(5)
    idx5 = p5.CriadorProjetoFase5(pasta_projeto).executar(ideia, config_fase4)
    resultado['fases_completas']['fase_5'] = idx5 is not None
    _registrar_e_verificar_orcamento(idx5 or {}, 'Criador', 5, orcamentos, pipeline_state_path)
    if idx5 is None:
        return _falhar(resultado, 'fase_5_criador', t0)

    # --- FASE 8: Implementador (condicional, carregamento dinâmico) ---
    # Fase 8 roda ANTES de Fase 6/7 quando --implementar-codigo é usado,
    # para que documentação e auto-crícia reflitam o código real.
    if implementar_codigo:
        print("\n" + "=" * 70)
        print(f"PIPELINE COMPLETO: FASE 8/{total_fases} — Implementador com Verificação")
        print("=" * 70)
        ctx8 = _carregar_micro_ambiente(8)
        p8 = _carregar_fase(8)
        idx8 = p8.ImplementadorFase8(pasta_projeto).executar(ideia, analise, design)
        resultado['fases_completas']['fase_8'] = idx8 is not None and idx8.get('status') == 'COMPLETO'
        _registrar_e_verificar_orcamento(idx8 or {}, 'Implementador', 8, orcamentos, pipeline_state_path)
        if not resultado['fases_completas']['fase_8']:
            return _falhar(resultado, 'fase_8_implementador', t0)

    # --- FASE 6: Documentador (carregamento dinâmico) ---
    print("\n" + "=" * 70)
    print(f"PIPELINE COMPLETO: FASE 6/{total_fases} — Documentador")
    print("=" * 70)
    ctx6 = _carregar_micro_ambiente(6)
    p6 = _carregar_fase(6)
    contexto_doc = {**analise, **design}
    idx6 = p6.DocumentadorFase6(
        pasta_cache=cache_dir, output_base=pasta_projeto / 'output'
    ).executar(pasta_projeto.name, contexto_doc, titulo=ideia)
    resultado['fases_completas']['fase_6'] = idx6 is not None and idx6.get('status') == 'COMPLETO'
    _registrar_e_verificar_orcamento(idx6 or {}, 'Documentador', 6, orcamentos, pipeline_state_path)
    if not resultado['fases_completas']['fase_6']:
        return _falhar(resultado, 'fase_6_documentador', t0)

    # --- FASE 7: Auto-crítica (carregamento dinâmico) ---
    print("\n" + "=" * 70)
    print(f"PIPELINE COMPLETO: FASE 7/{total_fases} — Auto-crítica")
    print("=" * 70)
    ctx7 = _carregar_micro_ambiente(7)
    p7 = _carregar_fase(7)
    idx7 = p7.AnalisadorCriticoAutomatico(pasta_projeto).executar()
    resultado['fases_completas']['fase_7'] = idx7.get('status') == 'COMPLETO'
    _registrar_e_verificar_orcamento(idx7, 'Auto-critica', 7, orcamentos, pipeline_state_path)
    resultado['score_final'] = idx7.get('score')

    resultado['status'] = 'COMPLETO'
    resultado['duracao_segundos'] = time.time() - t0

    # Persistir métricas do Context-Purge Engine
    resultado['context_purge'] = purge_engine.metricas.to_dict()
    purge_engine.persistir_metricas()

    # NIH #22: Empacotamento canônico do repositório via Repomix para LLMs
    saida_contexto = cache_dir / 'contexto_repo.xml'
    pkg_repo = empacotar_repositorio(
        pasta_projeto,
        saida_arquivo=saida_contexto,
        formato='xml',
        remove_comments=True,
        remove_empty_lines=True,
        no_file_summary=True
    )
    resultado['contexto_repo'] = {
        'status': pkg_repo.get('status'),
        'tokens_estimados': pkg_repo.get('tokens_estimados', 0),
        'ferramenta': pkg_repo.get('ferramenta'),
        'arquivo': str(saida_contexto) if saida_contexto.exists() else None
    }

    # Descartar todas as fases da memória ao final
    _descarregar_todas_fases()

    return resultado


@click.command(
    context_settings={'help_option_names': ['-h', '--help']},
    help='Pipeline completo aidd-project-generator (Fases 1-7, ou 1-8 com --implementar-codigo)',
)
@click.argument('ideia')
@click.option('--pasta', '--output', 'pasta', required=True, help='Pasta onde o projeto será criado')
@click.option('--interativo', is_flag=True, default=False,
              help='Usar modal interativo (input()) na Fase 4 em vez da heurística automática')
@click.option('--implementar-codigo', is_flag=True, default=False,
              help='Rodar também a Fase 8 (implementa código funcional real a partir do design, com testes e loop de correção)')
@click.option('--orquestrador', type=click.Choice(['legado', 'prefect']), default='legado',
              help='Motor de orquestração genérica (retries/checkpoints/estado). '
                   'prefect: delega a parte genérica ao Prefect preservando o protocolo delegado. '
                   'legado: orquestração sequencial custom (comportamento padrão).')
def cli(ideia, pasta, interativo, implementar_codigo, orquestrador):
    # --- Pré-voo: verificar LLM antes de gastar tempo com Fase 1 ---
    ok, msg = verificar_llm_pronto()
    if not ok:
        print("\n" + "=" * 70)
        print("❌ PREFLIGHT FALHOU — " + msg)
        print("=" * 70 + "\n")
        sys.exit(1)

    print(f"✓ {msg}")

    # Rede de segurança: mesmo com o pré-voo passando (checa só presença de
    # env vars), uma chave presente mas inválida só falha na chamada real —
    # captura aqui pra nunca vazar o stack trace cru do litellm.
    try:
        if orquestrador == 'prefect':
            # Orquestração genérica via Prefect: retries automáticos por fase,
            # checkpointing por (ideia, fase) e estado persistido em SQLite.
            # O protocolo delegado (utils_delegacao) permanece intacto.
            # (Fonte única: desde o Item 2 — unificar-orquestradores-generator-e-ops,
            # a orquestração Prefect vive NESTE módulo.)
            prefect_ok, prefect_msg = disponibilidade_prefect()
            if not prefect_ok:
                print(f"\n❌ ORQUESTRADOR PREFECT INDISPONÍVEL — {prefect_msg}")
                print("   Confirme a instalação com: pip install prefect")
                sys.exit(1)
            print(f"✓ {prefect_msg}")
            resultado = executar_pipeline_prefect(
                ideia, str(Path(pasta)),
                nao_interativo=not interativo,
                implementar_codigo=implementar_codigo
            )
        else:
            resultado = executar_pipeline(
                ideia, Path(pasta), nao_interativo=not interativo,
                implementar_codigo=implementar_codigo
            )
    except LLMNaoConfiguradoException as e:
        print(f"\n❌ {e.mensagem_usuario}")
        sys.exit(1)

    print("\n" + "=" * 70)
    if resultado['status'] == 'COMPLETO':
        print(f"✅ PIPELINE COMPLETO — score final: {resultado.get('score_final')}/100")
        # Fleet info
        fleet_info = resultado.get('fleet', {})
        print(f"   Fleet: {fleet_info.get('modo', '?')} ({fleet_info.get('total_detectados', 0)} agente(s))")
        # Context-Purge metrics
        purge_info = resultado.get('context_purge', {})
        if purge_info:
            print(f"   Context-Purge: {purge_info.get('total_subagentes_criados', 0)} subagentes, "
                  f"{purge_info.get('total_tokens_consumidos', 0)} tokens, "
                  f"{purge_info.get('taxa_sucesso', 0)}% sucesso")
    else:
        print(f"❌ PIPELINE FALHOU na {resultado['fase_que_falhou']}")
    print(f"   Duração: {resultado['duracao_segundos']:.1f}s")
    print("=" * 70 + "\n")

    sys.exit(0 if resultado['status'] == 'COMPLETO' else 1)


def main():
    cli()


if __name__ == '__main__':
    main()
