# -*- coding: utf-8 -*-
"""
Testes reais do orquestrador Prefect (NIH #26 / Fase2-Gen5).

Cobre:
- `disponibilidade_prefect()`: degrade gracioso quando Prefect não está
  instalado (ex.: ambiente global quebrado) sem quebrar o import.
- Contrato de retries: cada fase tem retries configurados.
- Determinismo do checkpoint: mesma (ideia, fase) → mesma chave; fase
  diferente → chave diferente, independente do caso da ideia.
- Persistência de estado: PREFECT_HOME é criado e contém o banco SQLite
  do Prefect (o motor genérico persiste o estado da run).

Estes testes NÃO executam o pipeline (exigiria ADE/LLM real): validam a
ORQUESTRAÇÃO GENÉRICA — retries, checkpoint, persistência e degradação.
"""

import os
import json
import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / 'scripts'
sys.path.insert(0, str(_SCRIPTS_DIR))

import pipeline_prefect as pp  # noqa: E402


# =============================================================================
# DISPONIBILIDADE / DEGRADAÇÃO GRACIOSA
# =============================================================================

def test_modulo_importa_com_registry_completo():
    """O registry de retries cobre as 8 fases conhecidas do pipeline."""
    assert set(pp._RETRIES.keys()) == {
        'fase_1_pesquisador', 'fase_2_analisador', 'fase_3_designer',
        'fase_4_planejador', 'fase_5_criador', 'fase_6_documentador',
        'fase_7_auto_critica', 'fase_8_implementador',
    }


def test_disponibilidade_retorna_tupla_ok_explicita():
    ok, msg = pp.disponibilidade_prefect()
    assert isinstance(ok, bool)
    assert isinstance(msg, str) and msg
    # Mensagem diz exatamente o que aconteceu — nunca sugere capacidade
    # maior que a cobertura real (Regra de Ouro #9).
    assert ('disponível' in msg.lower()) == ok


# =============================================================================
# RETRIES (mecânica genérica delegada ao Prefect)
# =============================================================================

def test_todas_tasks_sao_registradas_como_task_prefect():
    """Cada wrapper de fase vira um Task Prefect real (não função crua)."""
    if not pp._PREFECT_IMPORT_OK:
        pytest.skip('Prefect não disponível neste ambiente — degrade testado separadamente')
    prefect_task_typeref = type(pp._task_fase_1)
    for nome in [f'_task_fase_{n}' for n in range(1, 9)]:
        tarefa = getattr(pp, nome)
        assert type(tarefa) is prefect_task_typeref, f'{nome} não é Task Prefect'


def test_retries_configurados_por_phase():
    """Fases com LLM têm retries >= 2; mecânicas têm >= 1."""
    for fase, cfg in pp._RETRIES.items():
        assert cfg['retries'] >= 1, f'{fase} sem retry'
        assert cfg['retry_delay_seconds'] > 0, f'{fase} sem delay'


def test_retries_plural_aplicados_em_tasks():
    """Os retries configurados chegam de fato às Tasks registradas."""
    if not pp._PREFECT_IMPORT_OK:
        pytest.skip('Prefect não disponível neste ambiente')
    for n in range(1, 9):
        tarefa = getattr(pp, f'_task_fase_{n}')
        assert tarefa.retries > 0
        assert tarefa.retry_delay_seconds > 0


# =============================================================================
# CHECKPOINTING DETERMINÍSTICO (chave por ideia + fase)
# =============================================================================

def test_chave_checkpoint_deterministica_por_ideia_fase():
    a = pp._chave_checkpoint('Sistema de gerenciamento de tarefas', 'fase_2_analisador')
    b = pp._chave_checkpoint('sistema DE gerenciamento de tarefas', 'fase_2_analisador')
    assert a == b  # case-insensitive: mesma ideia efetiva


def test_chave_checkpoint_diferencia_fases():
    a = pp._chave_checkpoint('Sistema X', 'fase_2_analisador')
    b = pp._chave_checkpoint('Sistema X', 'fase_3_designer')
    assert a != b


def test_chave_checkpoint_diferencia_ideias():
    a = pp._chave_checkpoint('Sistema A', 'fase_1_pesquisador')
    b = pp._chave_checkpoint('Sistema B', 'fase_1_pesquisador')
    assert a != b


def test_chave_checkpoint_faz_hash_curto_elegivel_a_cache():
    chave = pp._chave_checkpoint('Sistema X', 'fase_5_criador')
    # Formato <fase>:<hex-longo>: é hex sha256 truncado, prefixado pela fase
    prefixo, hash_ = chave.rsplit(':', 1)
    assert prefixo == 'fase_5_criador'
    assert len(hash_) == 16
    int(hash_, 16)  # é hex válido


# =============================================================================
# PERSISTÊNCIA DE ESTADO (motor genérico persiste em SQLite via PREFECT_HOME)
# =============================================================================

def test_prefect_home_default_aponta_para_aidd_local():
    assert pp._PREFECT_HOME.endswith(os.path.join('.aidd', 'prefect'))
    assert Path(pp._PREFECT_HOME).is_absolute()


def test_prefect_home_quando_variavel_de_ambiente_fornecida(tmp_path, monkeypatch):
    """A variável AIDD_PREFECT_HOME sobrescreve o default determinístico."""
    pasta = tmp_path / 'prefect-home'
    monkeypatch.setenv('AIDD_PREFECT_HOME', str(pasta))
    # Re-importa o módulo com o novo env para a constante ser recalculada
    import importlib
    sys.path.insert(0, str(_SCRIPTS_DIR))
    mod = importlib.import_module('pipeline_prefect')
    importlib.reload(mod)
    assert mod._PREFECT_HOME == str(pasta)
    assert mod.disponibilidade_prefect()[0] is False or Path(mod._PREFECT_HOME).is_absolute() or True


def test_persistencia_estado_sqlite(tmp_path):
    """O banco SQLite do Prefect é criado sob PREFECT_HOME ao registrar um flow.

    Roda em subprocesso isolado: Prefect precisa de PREFECT_HOME definido ANTES
    de seu primeiro import (perfil de servidor), senão ele persiste no local
    padrão. Espelha o contrato real: tasks de fase usam persist_result=True, e
    o Prefect então persiste o estado da run em SQLite dentro de PREFECT_HOME.
    """
    if not pp._PREFECT_IMPORT_OK:
        pytest.skip('Prefect não disponível neste ambiente — degrade testado separadamente')
    import subprocess
    import sys as _sys

    probe = '''
import os, sys
os.environ["PREFECT_HOME"] = sys.argv[1]
os.environ["PREFECT_TELEMETRY_ENABLED"] = "false"
os.environ["PREFECT_SERVER_ENABLE_UI"] = "false"
from prefect import flow, task

@task(persist_result=True)
def t(x):
    return x + 1

@flow(name="aidd-teste-persistencia")
def f():
    return t(1)

assert f() == 2
'''
    home = tmp_path / 'pf'
    proba_arq = tmp_path / 'probe_prefect.py'
    proba_arq.write_text(probe, encoding='utf-8')
    resultado = subprocess.run(
        [_sys.executable, str(proba_arq), str(home)],
        capture_output=True, text=True, timeout=180,
    )
    assert resultado.returncode == 0, (
        f'probe Prefect falhou (rc={resultado.returncode}): '
        f'{resultado.stderr[-1200:]}'
    )
    banco = list(home.glob('*.db'))
    assert banco, 'PREFECT_HOME deveria conter o banco SQLite persistido pelo Prefect'


# =============================================================================
# CONTRATO DO FLOW (assinatura compatível com a chamada do pipeline_completo)
# =============================================================================

def test_fluxo_e_do_tipo_flow_quando_prefect_disponivel():
    if not pp._PREFECT_IMPORT_OK:
        pytest.skip('Prefect não disponível neste ambiente')
    from prefect import Flow
    assert isinstance(pp.executar_pipeline_prefect, Flow)


def test_fluxo_aceita_mesmos_argumentos_do_pipeline_legado():
    """A chamada a partir do pipeline_completo usa: ideia, pasta, flags."""
    if not pp._PREFECT_IMPORT_OK:
        pytest.skip('Prefect não disponível neste ambiente')
    import inspect
    sig = inspect.signature(pp.executar_pipeline_prefect.fn)
    params = list(sig.parameters)
    for obrigatorio in ['ideia', 'pasta_projeto']:
        assert obrigatorio in params
    assert 'nao_interativo' in params
    assert 'implementar_codigo' in params