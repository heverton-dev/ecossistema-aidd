# -*- coding: utf-8 -*-
"""
Fixtures compartilhadas para os testes das 6 fases AIDD (Correção 5/5).

Os scripts de fase vivem em scripts/phases/ e têm nomes que começam com
dígito (02_analisador.py, ...), o que impede `import` normal. Este conftest
expõe `load_phase_module()` (via importlib) e fixtures de dados reais.
"""

import sys
import json
import importlib.util
from pathlib import Path

import pytest

PHASES_DIR = Path(__file__).resolve().parent.parent / 'scripts' / 'phases'
sys.path.insert(0, str(PHASES_DIR))


def load_phase_module(alias: str, filename: str):
    """Carrega um script de fase por caminho, com alias válido para import."""
    path = PHASES_DIR / filename
    spec = importlib.util.spec_from_file_location(alias, path)
    if spec is None or spec.loader is None:
        raise ImportError(f'Não foi possível carregar {path}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# =============================================================================
# MÓDULOS DAS FASES (carregados uma vez por sessão)
# =============================================================================

@pytest.fixture(scope='session')
def pesquisador_01():
    return load_phase_module('pesquisador_01', '01_pesquisador.py')


@pytest.fixture(scope='session')
def analisador_02():
    return load_phase_module('analisador_02', '02_analisador.py')


@pytest.fixture(scope='session')
def designer_03():
    return load_phase_module('designer_03', '03_designer.py')


@pytest.fixture(scope='session')
def decisor_04():
    return load_phase_module('decisor_04', '04_decisor.py')


@pytest.fixture(scope='session')
def criador_05():
    return load_phase_module('criador_05', '05_criador.py')


@pytest.fixture(scope='session')
def documentador_06():
    return load_phase_module('documentador_06', '06_documentador.py')


@pytest.fixture(scope='session')
def analisador_07():
    return load_phase_module('analisador_07', '07_analisador.py')


@pytest.fixture(scope='session')
def implementador_08():
    return load_phase_module('implementador_08', '08_implementador.py')


# =============================================================================
# DADOS REAIS (entrada válida que passa nos gates)
# =============================================================================

@pytest.fixture
def analise_valida():
    """Análise que passa em todos os gates A1-A4 da Phase 2."""
    return {
        'objetivo': 'Sistema automatizado de processamento de vídeos YouTube com documentação tripartite em PT-BR',
        'publico_alvo': 'Educadores e criadores de conteúdo',
        'constraints': [
            'Zero download de binários',
            'Máxima economia de tokens',
            'Brasil first',
        ],
        'stack_recomendado': {
            'linguagem': 'Python 3.10+',
            'framework': 'FastAPI',
            'banco': 'SQLite',
            'libs_principais': ['requests', 'pydantic'],
        },
        'arquitetura': 'Pipeline em 5 camadas AIDD com gates mecânicos e persistência estruturada em JSON',
        'referencias_utilizadas': ['referencia-1', 'referencia-2'],
    }


@pytest.fixture
def design_valido():
    """Design que passa em todos os gates D1-D3 da Phase 3."""
    return {
        'design': {
            'camadas': [
                {'numero': i, 'nome': f'Camada {i}', 'responsabilidade': 'resp', 'artefatos': ['a.py']}
                for i in range(1, 6)
            ],
            'scripts': [
                {
                    'camada': 2,
                    'nome': 'coleta.py',
                    'responsabilidade': 'Coletar dados sem LLM',
                    'pseudocodigo': '1. Conectar API\n2. Buscar dados',
                    'determinismo_percentual': 100,
                    'teste': 'assert dados.len > 0',
                }
            ],
            'tokens': {
                'fases': [{'fase': 'Phase 1', 'tokens_consumidos': 0, 'justificativa': 'GitHub API pura'}],
                'total_tokens': 60000,
                'percentual_determinismo': 88,
            },
            'ferramentas': [
                {'nome': 'skill-x', 'tipo': 'Skill', 'proposito': 'x', 'escopo': 'GLOBAL', 'justificativa': 'x'}
            ],
            'gates': [
                {'gate_id': 'G0', 'descricao': 'Validar entrada', 'checklist': ['a'], 'criterio_sucesso': 'x', 'retorno': 'exit 0'}
            ],
        }
    }


# =============================================================================
# DADOS DE PROJETO PARA A PHASE 7 (índices JSON reais em disco)
# =============================================================================

def _escrever_index_phase(cache_dir: Path, num: int, **overrides):
    """Escreve um _phase_NN_index.json com valores default saudáveis."""
    index = {
        'fase_id': f'phase_{num:02d}',
        'versao': '2.1',
        'status': 'COMPLETO',
        'tokens': {
            'consumidos': 0,
            'percentual_determinismo': 100,
        },
        'gates_executados': [
            {'gate_id': f'G{num}_1', 'descricao': 'gate 1', 'status': 'PASSOU', 'detalhes': 'ok'},
            {'gate_id': f'G{num}_2', 'descricao': 'gate 2', 'status': 'PASSOU', 'detalhes': 'ok'},
            {'gate_id': f'G{num}_3', 'descricao': 'gate 3', 'status': 'PASSOU', 'detalhes': 'ok'},
        ],
        'resume_info': {'proxima_fase': 'x', 'pode_prosseguir': True, 'requer_intervencao_manual': False},
    }
    if num == 6:
        index['processamento'] = {'documentos_gerados': 3, 'formatos': ['html', 'md', 'pdf']}
    if num == 1:
        index['validacoes'] = {'passou': 5, 'total_checks': 5, 'falhou': 0}

    index.update(overrides)
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / f'_phase_{num:02d}_index.json').write_text(
        json.dumps(index, ensure_ascii=False), encoding='utf-8'
    )
    return index


@pytest.fixture
def projeto_bom(tmp_path):
    """Projeto saudável: 6 phases COMPLETO, gates passando, docs em 3 formatos."""
    for i in range(1, 7):
        _escrever_index_phase(tmp_path / '.aidd' / 'cache', i)
    return tmp_path


@pytest.fixture
def projeto_ruim(tmp_path):
    """Projeto com falhas: phases incompletas, gates falhando, sem documentação."""
    cache = tmp_path / '.aidd' / 'cache'
    _escrever_index_phase(
        cache, 1,
        tokens={'consumidos': 5000, 'percentual_determinismo': 100},
        validacoes={'passou': 1, 'total_checks': 3, 'falhou': 2},
    )
    _escrever_index_phase(
        cache, 2,
        status='FALHOU',
        tokens={'consumidos': 8000, 'percentual_determinismo': 0},
        gates_executados=[
            {'gate_id': 'A1_schema_valido', 'descricao': 'Validar output segue schema', 'status': 'FALHOU', 'detalhes': 'Schema inválido'},
        ],
        resume_info={'proxima_fase': 'x', 'pode_prosseguir': False, 'requer_intervencao_manual': True},
    )
    _escrever_index_phase(
        cache, 3,
        tokens={'consumidos': 30000, 'percentual_determinismo': 30},
    )
    return tmp_path


@pytest.fixture
def projeto_vazio(tmp_path):
    """Projeto sem nenhum índice de fase (cache vazio, como projeto recém-criado)."""
    (tmp_path / '.aidd' / 'cache').mkdir(parents=True)
    return tmp_path


@pytest.fixture
def projeto_bom_com_fase8(tmp_path):
    """Projeto saudável COM fase 8 (pipeline --implementar-codigo): 7 phases completas + phase 8."""
    cache = tmp_path / '.aidd' / 'cache'
    for i in range(1, 7):
        _escrever_index_phase(cache, i)
    # Phase 7 (auto-crítica) — não é escrita por _escrever_index_phase default
    _escrever_index_phase(cache, 7)
    # Phase 8 (implementador) — 4 gates (I1-I4), tokens LLM reais
    _escrever_index_phase(
        cache, 8,
        fase_id='phase_08_implementacao',
        tokens={'consumidos': 7616, 'medicao': 'real', 'percentual_determinismo': 0},
        processamento={
            'scripts_implementados': 5,
            'tentativas_totais': 5,
            'scripts_com_falha_apos_tentativas': 0,
            'testes_passaram': 37,
            'testes_falharam': 0,
            'testes_erros': 0,
            'testes_total': 37,
        },
        gates_executados=[
            {'gate_id': 'I1_scripts_implementados', 'descricao': 'Todos scripts implementados', 'status': 'PASSOU', 'detalhes': '5/5'},
            {'gate_id': 'I2_testes_coletam', 'descricao': 'pytest coleta sem erro', 'status': 'PASSOU', 'detalhes': 'Coleta OK'},
            {'gate_id': 'I3_testes_passam', 'descricao': '100% testes passam', 'status': 'PASSOU', 'detalhes': '37/37'},
            {'gate_id': 'I4_cli_executa', 'descricao': 'CLI smoke-test', 'status': 'PASSOU', 'detalhes': 'exit code 0'},
            {'gate_id': 'I5_teste_integracao', 'descricao': 'Teste de integração entre scripts', 'status': 'PASSOU', 'detalhes': '1/1 teste(s) de integração passando'},
        ],
    )
    return tmp_path