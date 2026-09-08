#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PIPELINE PREFECT — Orquestração genérica da pipeline de 8 fases via Prefect
aidd-project-generator v2.3 (NIH #26 / Fase2-Gen5)

Este módulo integra o Prefect como MOTOR GENÉRICO de orquestração da pipeline
de fases do aidd-generator. A lógica de domínio de cada fase e o PROTOCOLO
DELEGADO (utils_delegacao.py) NÃO são reimplementados aqui — são preservados
como o diferencial custom do ecossistema. O que o Prefect entrega é a parte
genérica que antes era mantida à mão:

- Retries automáticos por fase (antes: laço manual só no modo headless do LLM).
- Checkpointing/resume: tasks concluídas são cacheadas por (ideia + fase); numa
  reexecução após falha, fases já completas são puladas via cache_key_fn.
- Estado persistido: o Prefect persiste o resultado de cada task e o estado da
  run em banco SQLite local (PREFECT_HOME), permitindo auditoria e retomada.

O contrato de encadeamento é o MESMO do pipeline_completo.py: cada fase persiste
suas saídas em <pasta>/.aidd/cache/data/<nome>.json e a fase seguinte lê esses
arquivos reais — nenhum dado é fabricado nem passado apenas em memória.

Uso (via CLI do pipeline principal):
    python scripts/pipeline_completo.py "ideia" --pasta ../PROJ --orquestrador prefect
"""

import os
import sys
import json
import time
import hashlib
from types import SimpleNamespace
from pathlib import Path
from typing import Any

# --- Pré-voo de ambiente: uma instância limpa e determinística do Prefect -----
_PREFECT_HOME = os.environ.get(
    'AIDD_PREFECT_HOME',
    str((Path(__file__).resolve().parent.parent / '.aidd' / 'prefect').resolve()),
)
os.environ.setdefault('PREFECT_HOME', _PREFECT_HOME)
# Telemetria desligada: evita corrida de banco (SQLite locked) em runs efêmeras
# e mantém a run auditável localmente sem exfiltração de metadados.
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
# pipeline_completo.py); só a ORQUESTRAÇÃO (retry/cache/persistência) é
# delegada ao decorator @task do Prefect.

@task(retries=_RETRIES['fase_1_pesquisador']['retries'],
      retry_delay_seconds=_RETRIES['fase_1_pesquisador']['retry_delay_seconds'],
      persist_result=True, cache_key_fn=_cache_por_fase('fase_1_pesquisador'))
def _task_fase_1(ideia: str, cache_dir: str):
    from pipeline_completo import _carregar_fase, _carregar_micro_ambiente
    _carregar_micro_ambiente(1)
    p1 = _carregar_fase(1)
    return p1.PesquisadorFase1(Path(cache_dir)).executar(ideia)


@task(retries=_RETRIES['fase_2_analisador']['retries'],
      retry_delay_seconds=_RETRIES['fase_2_analisador']['retry_delay_seconds'],
      persist_result=True, cache_key_fn=_cache_por_fase('fase_2_analisador'))
def _task_fase_2(ideia: str, cache_dir: str, referencias: dict):
    from pipeline_completo import _carregar_fase, _carregar_micro_ambiente
    _carregar_micro_ambiente(2)
    p2 = _carregar_fase(2)
    return p2.AnalisadorFase2(Path(cache_dir)).executar(ideia, referencias)


@task(retries=_RETRIES['fase_3_designer']['retries'],
      retry_delay_seconds=_RETRIES['fase_3_designer']['retry_delay_seconds'],
      persist_result=True, cache_key_fn=_cache_por_fase('fase_3_designer'))
def _task_fase_3(ideia: str, cache_dir: str, analise: dict):
    from pipeline_completo import _carregar_fase, _carregar_micro_ambiente
    _carregar_micro_ambiente(3)
    p3 = _carregar_fase(3)
    return p3.DesignerFase3(Path(cache_dir)).executar(ideia, analise)


@task(retries=_RETRIES['fase_4_planejador']['retries'],
      retry_delay_seconds=_RETRIES['fase_4_planejador']['retry_delay_seconds'],
      persist_result=True, cache_key_fn=_cache_por_fase('fase_4_planejador'))
def _task_fase_4(ideia: str, cache_dir: str, design: dict, nao_interativo: bool):
    from pipeline_completo import _carregar_fase, _carregar_micro_ambiente
    _carregar_micro_ambiente(4)
    p4 = _carregar_fase(4)
    return p4.DecisorFase4(Path(cache_dir)).executar(design, nao_interativo=nao_interativo)


@task(retries=_RETRIES['fase_5_criador']['retries'],
      retry_delay_seconds=_RETRIES['fase_5_criador']['retry_delay_seconds'],
      persist_result=True, cache_key_fn=_cache_por_fase('fase_5_criador'))
def _task_fase_5(ideia: str, pasta_projeto: str, config_fase4: dict):
    from pipeline_completo import _carregar_fase, _carregar_micro_ambiente
    _carregar_micro_ambiente(5)
    p5 = _carregar_fase(5)
    return p5.CriadorProjetoFase5(Path(pasta_projeto)).executar(ideia, config_fase4)


@task(retries=_RETRIES['fase_8_implementador']['retries'],
      retry_delay_seconds=_RETRIES['fase_8_implementador']['retry_delay_seconds'],
      persist_result=True, cache_key_fn=_cache_por_fase('fase_8_implementador'))
def _task_fase_8(ideia: str, pasta_projeto: str, analise: dict, design: dict):
    from pipeline_completo import _carregar_fase, _carregar_micro_ambiente
    _carregar_micro_ambiente(8)
    p8 = _carregar_fase(8)
    return p8.ImplementadorFase8(Path(pasta_projeto)).executar(ideia, analise, design)


@task(retries=_RETRIES['fase_6_documentador']['retries'],
      retry_delay_seconds=_RETRIES['fase_6_documentador']['retry_delay_seconds'],
      persist_result=True, cache_key_fn=_cache_por_fase('fase_6_documentador'))
def _task_fase_6(cache_dir: str, output_base: str, nome_projeto: str,
                 contexto_doc: dict, ideia: str):
    from pipeline_completo import _carregar_fase, _carregar_micro_ambiente
    _carregar_micro_ambiente(6)
    p6 = _carregar_fase(6)
    return p6.DocumentadorFase6(
        pasta_cache=Path(cache_dir), output_base=Path(output_base)
    ).executar(nome_projeto, contexto_doc, titulo=ideia)


@task(retries=_RETRIES['fase_7_auto_critica']['retries'],
      retry_delay_seconds=_RETRIES['fase_7_auto_critica']['retry_delay_seconds'],
      persist_result=True, cache_key_fn=_cache_por_fase('fase_7_auto_critica'))
def _task_fase_7(ideia: str, pasta_projeto: str):
    from pipeline_completo import _carregar_fase, _carregar_micro_ambiente
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

    Usado pelo pipeline principal para decidir se o --orquestrador prefect é
    viável e pela suíte de testes para pular quando o env não estiver limpo.
    """
    if not _PREFECT_IMPORT_OK:
        return False, f'Prefect não importável: {_PREFECT_IMPORT_ERRO}'
    return True, f'Prefect disponível (PREFECT_HOME={_PREFECT_HOME})'


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Executa pipeline via Prefect')
    parser.add_argument('ideia', help='Ideia do projeto')
    parser.add_argument('--pasta', required=True)
    parser.add_argument('--interativo', action='store_true')
    parser.add_argument('--implementar-codigo', action='store_true')
    args = parser.parse_args()
    ok, msg = disponibilidade_prefect()
    if not ok:
        sys.exit(f'❌ {msg}')
    res = executar_pipeline_prefect(
        args.ideia, args.pasta,
        nao_interativo=not args.interativo,
        implementar_codigo=args.implementar_codigo,
    )
    print(json.dumps(res, indent=2, ensure_ascii=False, default=str))
    sys.exit(0 if res.get('status') == 'COMPLETO' else 1)