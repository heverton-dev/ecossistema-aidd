#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes automatizados da aplicação Web Local
tests/test_web_app.py — aidd-project-generator
"""

import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from web.config_manager import (
    mascarar_chave,
    ler_env_dict,
    identificar_provedor_por_modelo,
    obter_configuracao,
    salvar_configuracao,
    testar_chave_llm as executar_teste_chave_llm,
    PROVEDORES_SUPORTADOS
)
from web.status_parser import (
    obter_sequencia_fases,
    extrair_gates_de_index,
    analisar_status_pasta_projeto
)
from web.pipeline_runner import PipelineRunner
from web.app import app, sanitizar_nome_pasta


# =============================================================================
# 1. TESTES: CONFIG MANAGER
# =============================================================================

def test_mascarar_chave():
    assert mascarar_chave("") == ""
    assert mascarar_chave(None) == ""
    assert mascarar_chave("12345") == "••••••••"
    assert mascarar_chave("12345678") == "••••••••"
    assert mascarar_chave("gsk_1234567890abcdef") == "gsk_••••••••cdef"


def test_ler_env_dict(tmp_path):
    env_file = tmp_path / ".env"
    assert ler_env_dict(env_file) == {}

    env_file.write_text(
        "# Comentário\n"
        "LLM_MODEL=groq/llama-3.3-70b-versatile\n"
        "GROQ_API_KEY=\"gsk_test123\"\n"
        "TIMEOUT=120\n",
        encoding='utf-8'
    )
    resultado = ler_env_dict(env_file)
    assert resultado['LLM_MODEL'] == 'groq/llama-3.3-70b-versatile'
    assert resultado['GROQ_API_KEY'] == 'gsk_test123'
    assert resultado['TIMEOUT'] == '120'


def test_identificar_provedor_por_modelo():
    assert identificar_provedor_por_modelo("groq/llama-3.3-70b-versatile")['id'] == 'groq'
    assert identificar_provedor_por_modelo("nvidia_nim/meta/llama-3.3-70b-instruct")['id'] == 'nvidia_nim'
    assert identificar_provedor_por_modelo("openrouter/meta-llama/llama-3.3-70b-instruct:free")['id'] == 'openrouter'
    assert identificar_provedor_por_modelo("together_ai/meta-llama/Llama-3.3-70B-Instruct-Turbo")['id'] == 'together_ai'
    assert identificar_provedor_por_modelo("openai/gpt-4o-mini")['id'] == 'openai_compativel'
    assert identificar_provedor_por_modelo("modelo_invalido_sem_prefixo") is None
    assert identificar_provedor_por_modelo("") is None


def test_obter_configuracao_sem_chave(tmp_path, monkeypatch):
    monkeypatch.delenv('CLAUDECODE', raising=False)
    monkeypatch.delenv('LLM_MODEL', raising=False)
    monkeypatch.delenv('GROQ_API_KEY', raising=False)

    env_vazio = tmp_path / ".env"
    cfg = obter_configuracao(env_vazio)
    assert cfg['esta_configurado'] is False
    assert cfg['tem_chave'] is False
    assert len(cfg['provedores_disponiveis']) == 5


def test_obter_configuracao_com_chave(tmp_path, monkeypatch):
    monkeypatch.delenv('CLAUDECODE', raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "LLM_MODEL=groq/llama-3.3-70b-versatile\n"
        "GROQ_API_KEY=gsk_1234567890abcdef\n",
        encoding='utf-8'
    )
    cfg = obter_configuracao(env_file)
    assert cfg['esta_configurado'] is True
    assert cfg['tem_chave'] is True
    assert cfg['provedor_ativo'] == 'groq'
    assert "gsk_" in cfg['chave_mascarada']


def test_salvar_configuracao_sucesso(tmp_path):
    env_file = tmp_path / ".env"
    sucesso, msg = salvar_configuracao(
        provedor_id='nvidia_nim',
        chave='nvapi-teste1234567890',
        modelo='nvidia_nim/meta/llama-3.3-70b-instruct',
        timeout_segundos=90,
        caminho_env=env_file
    )
    assert sucesso is True
    assert env_file.exists()
    conteudo = env_file.read_text(encoding='utf-8')
    assert "LLM_MODEL=nvidia_nim/meta/llama-3.3-70b-instruct" in conteudo
    assert "NVIDIA_NIM_API_KEY=nvapi-teste1234567890" in conteudo
    assert "LLM_TIMEOUT_SEGUNDOS=90" in conteudo


def test_salvar_configuracao_provedor_invalido(tmp_path):
    env_file = tmp_path / ".env"
    sucesso, msg = salvar_configuracao(
        provedor_id='provedor_nao_existente',
        chave='key123',
        caminho_env=env_file
    )
    assert sucesso is False
    assert "não é suportado" in msg


def test_salvar_configuracao_chave_vazia(tmp_path):
    env_file = tmp_path / ".env"
    sucesso, msg = salvar_configuracao(
        provedor_id='groq',
        chave='',
        caminho_env=env_file
    )
    assert sucesso is False
    assert "obrigatória" in msg


def test_testar_chave_llm_sucesso():
    with patch('litellm.completion') as mock_comp:
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock(message=MagicMock(content="OK"))]
        mock_resp.usage = MagicMock(total_tokens=5)
        mock_comp.return_value = mock_resp

        sucesso, msg, detalhes = executar_teste_chave_llm(
            provedor_id='groq',
            chave='gsk_validkey123456'
        )
        assert sucesso is True
        assert "validada com sucesso" in msg
        assert detalhes['tokens'] == 5


def test_testar_chave_llm_erro_autenticacao():
    with patch('litellm.completion', side_effect=Exception("AuthenticationError: 401 Unauthorized Invalid API Key")):
        sucesso, msg, detalhes = executar_teste_chave_llm(
            provedor_id='groq',
            chave='gsk_invalidkey'
        )
        assert sucesso is False
        assert "recusada pelo provedor" in msg


# =============================================================================
# 2. TESTES: STATUS PARSER
# =============================================================================

def test_obter_sequencia_fases():
    fases_padrao = obter_sequencia_fases(implementar_codigo=False)
    assert len(fases_padrao) == 7
    assert all(f['numero'] != 8 for f in fases_padrao)

    fases_com_codigo = obter_sequencia_fases(implementar_codigo=True)
    assert len(fases_com_codigo) == 8
    # Verifica que fase 8 existe e está antes da 6 e 7
    numeros = [f['numero'] for f in fases_com_codigo]
    assert numeros == [1, 2, 3, 4, 5, 8, 6, 7]


def test_extrair_gates_de_index():
    dados = {
        'gates': [
            {'id': 'G1', 'descricao': 'Gate de teste', 'passou': True},
            {'id': 'G2', 'descricao': 'Gate falho', 'passou': False}
        ]
    }
    gates = extrair_gates_de_index(dados)
    assert len(gates) == 2
    assert gates[0]['passou'] is True
    assert gates[1]['passou'] is False


def test_analisar_status_pasta_projeto_completo(tmp_path):
    pasta_projeto = tmp_path / "meu-projeto"
    cache_dir = pasta_projeto / ".aidd" / "cache"
    cache_dir.mkdir(parents=True)

    # Simular index das fases
    (cache_dir / "_phase_01_index.json").write_text(json.dumps({
        'fase_id': 'phase_01_research',
        'status': 'COMPLETO',
        'timestamps': {'duracao_segundos': 1.5},
        'tokens': {'consumidos': 0}
    }), encoding='utf-8')

    (cache_dir / "_phase_02_index.json").write_text(json.dumps({
        'fase_id': 'phase_02_analysis',
        'status': 'COMPLETO',
        'timestamps': {'duracao_segundos': 2.0},
        'tokens': {'consumidos': 1500}
    }), encoding='utf-8')

    (cache_dir / "_phase_07_index.json").write_text(json.dumps({
        'fase_id': 'phase_07_auto_critique',
        'status': 'COMPLETO',
        'score': 95,
        'pontos_fortes': ['Excelente arquitetura'],
        'pontos_fracos': []
    }), encoding='utf-8')

    status = analisar_status_pasta_projeto(pasta_projeto, implementar_codigo=False)
    assert status['pasta_existe'] is True
    assert status['fases_concluidas'] == 3  # fases 1, 2 e 7
    assert status['tokens_totais_consumidos'] == 1500
    assert status['score_final'] == 95


def test_analisar_status_pasta_projeto_com_fase_8(tmp_path):
    pasta_projeto = tmp_path / "projeto-funcional"
    cache_dir = pasta_projeto / ".aidd" / "cache"
    cache_dir.mkdir(parents=True)

    (cache_dir / "_phase_08_index.json").write_text(json.dumps({
        'fase_id': 'phase_08_implementacao',
        'status': 'COMPLETO',
        'resultado_pytest': {
            'coletados': 10,
            'passaram': 10,
            'falharam': 0,
            'duracao_segundos': 1.2
        },
        'timestamps': {'duracao_segundos': 5.0},
        'tokens': {'consumidos': 3000}
    }), encoding='utf-8')

    status = analisar_status_pasta_projeto(pasta_projeto, implementar_codigo=True)
    assert status['total_fases'] == 8
    assert status['resultado_testes'] is not None
    assert status['resultado_testes']['todos_passaram'] is True
    assert status['resultado_testes']['passaram'] == 10


# =============================================================================
# 3. TESTES: PIPELINE RUNNER
# =============================================================================

def test_pipeline_runner_validacao():
    runner = PipelineRunner()
    res = runner.iniciar_pipeline("", "../pasta")
    assert res['sucesso'] is False
    assert "informe a ideia" in res['mensagem']


def test_pipeline_runner_deteccao_erro_llm():
    runner = PipelineRunner()
    runner.logs.append("[10:00:00] litellm.exceptions.BadRequestError: Provider List: groq requires GROQ_API_KEY")
    runner._processar_falha()
    assert runner.precisa_configuracao is True
    assert "Você ainda não configurou uma chave de IA" in runner.erro_amigavel


def test_pipeline_runner_deteccao_erro_permissao():
    runner = PipelineRunner()
    runner.logs.append("[10:00:00] PermissionError: [Errno 13] Permission denied")
    runner._processar_falha()
    assert runner.precisa_configuracao is False
    assert "Permissão negada" in runner.erro_amigavel


def test_pipeline_runner_cancelar_sem_execucao():
    runner = PipelineRunner()
    res = runner.cancelar_pipeline()
    assert res['sucesso'] is False


# =============================================================================
# 4. TESTES: FLASK API ENDPOINTS
# =============================================================================

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def test_endpoint_index(client):
    res = client.get('/')
    assert res.status_code == 200
    assert b"AIDD Generator" in res.data


def test_endpoint_config_get(client):
    res = client.get('/api/config')
    assert res.status_code == 200
    data = res.get_json()
    assert data['sucesso'] is True
    assert 'esta_configurado' in data['config']


def test_endpoint_config_post(client, tmp_path):
    env_temp = tmp_path / ".env"
    with patch('web.app.salvar_configuracao', return_value=(True, "Salvo com sucesso!")):
        res = client.post('/api/config', json={
            'provedor_id': 'groq',
            'chave': 'gsk_123456789'
        })
        assert res.status_code == 200
        assert res.get_json()['sucesso'] is True


def test_endpoint_suggest_folder(client):
    res = client.get('/api/suggest-folder?ideia=API de Tarefas com Flask')
    assert res.status_code == 200
    data = res.get_json()
    assert data['sucesso'] is True
    assert 'projeto-' in data['nome_pasta']


def test_endpoint_pipeline_start_bloqueado_sem_chave(client):
    with patch('web.app.obter_configuracao', return_value={'esta_configurado': False}):
        res = client.post('/api/pipeline/start', json={
            'ideia': 'Meu projeto teste',
            'pasta_projeto': '../teste'
        })
        assert res.status_code == 400
        data = res.get_json()
        assert data['sucesso'] is False
        assert data['bloqueado_por_configuracao'] is True


def test_endpoint_pipeline_start_sucesso_quando_configurado(client):
    with patch('web.app.obter_configuracao', return_value={'esta_configurado': True}):
        with patch('web.app.runner_global.iniciar_pipeline', return_value={'sucesso': True, 'pasta_projeto': '...' }):
            res = client.post('/api/pipeline/start', json={
                'ideia': 'Meu projeto teste',
                'pasta_projeto': '../teste'
            })
            assert res.status_code == 200
            assert res.get_json()['sucesso'] is True


def test_endpoint_pipeline_status(client):
    res = client.get('/api/pipeline/status')
    assert res.status_code == 200
    assert 'status' in res.get_json()


def test_endpoint_open_folder_pasta_inexistente(client):
    res = client.post('/api/open-folder', json={'caminho': '/caminho/completamente/inexistente/12345'})
    assert res.status_code == 404
    assert res.get_json()['sucesso'] is False


def test_sanitizar_nome_pasta():
    assert sanitizar_nome_pasta("") == "novo-projeto-aidd"
    assert sanitizar_nome_pasta("API de Gestão Financeira com IA") == "projeto-api-de-gestao-financeira"
    assert sanitizar_nome_pasta("Projeto Já Com Prefixo") == "projeto-ja-com-prefixo"


# =============================================================================
# 5. TESTES: ROTAS DE MONITORAMENTO (projeto/status e workspace/status)
# =============================================================================

def test_endpoint_projeto_status_pasta_real(client, tmp_path):
    """/api/projeto/status com pasta real contendo .aidd/cache retorna status."""
    pasta_projeto = tmp_path / "projeto-monitorado"
    cache_dir = pasta_projeto / ".aidd" / "cache"
    cache_dir.mkdir(parents=True)
    (cache_dir / "_phase_01_index.json").write_text(json.dumps({
        'fase_id': 'phase_01_research',
        'status': 'COMPLETO',
        'timestamps': {'duracao_segundos': 1.0},
        'tokens': {'consumidos': 0}
    }), encoding='utf-8')

    res = client.get(f'/api/projeto/status?pasta={pasta_projeto}')
    assert res.status_code == 200
    data = res.get_json()
    assert data['sucesso'] is True
    assert data['status']['pasta_existe'] is True
    assert data['status']['fases_concluidas'] >= 1


def test_endpoint_projeto_status_pasta_inexistente(client):
    """/api/projeto/status com pasta inexistente retorna 404 honesto."""
    res = client.get('/api/projeto/status?pasta=C:/caminho/inexistente/xyz')
    assert res.status_code == 404
    data = res.get_json()
    assert data['sucesso'] is False
    assert 'não encontrada' in data['mensagem'].lower()


def test_endpoint_projeto_status_sem_pasta(client):
    """/api/projeto/status sem pasta e sem runner ativo retorna 400."""
    with patch('web.app.runner_global.obter_status', return_value={'pasta_projeto': ''}):
        res = client.get('/api/projeto/status')
        assert res.status_code == 400
        data = res.get_json()
        assert data['sucesso'] is False


def test_endpoint_workspace_status(client):
    """/api/workspace/status lê o PLANO-EXECUCAO-ESTRUTURADO.json real e retorna progresso."""
    res = client.get('/api/workspace/status')
    assert res.status_code == 200
    data = res.get_json()
    assert data['sucesso'] is True
    ws = data['workspace']
    assert 'total_etapas' in ws
    assert 'etapas_completas' in ws
    assert 'progresso_percentual' in ws
    assert isinstance(ws['etapas'], list)


def test_endpoint_workspace_status_sem_plano(client, tmp_path):
    """/api/workspace/status sem PLANO-EXECUCAO-ESTRUTURADO.json retorna 404."""
    with patch('web.app.ROOT_DIR', tmp_path):
        res = client.get('/api/workspace/status')
        assert res.status_code == 404
        data = res.get_json()
        assert data['sucesso'] is False
