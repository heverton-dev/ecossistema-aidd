# -*- coding: utf-8 -*-
"""
Testes de Máquina de Estados Formal e Retomada Inteligente (--resume)
Item: maquina-estados-pipeline-generator-e-resume

Cobre integralmente o Definition of Done:
1. Estado estruturado versionado .aidd/cache/_pipeline_state.json gravado atomicamente.
2. Flag --resume que pula fases com status COMPLETO e artefatos válidos.
3. Validação de entradas de cache com jsonschema na fronteira de leitura de cada fase.
4. Tratamento de JSON corrompido com _falhar estruturado e orientativo.
"""

import json
import os
import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from core.pipeline_state import (
    PipelineStateManager,
    ler_cache_com_validacao,
    PipelineCorrompidoError,
)
from phases.schemas.registry import (
    validar_pipeline_state,
    validar_cache,
    SchemaValidationError,
)
import pipeline_completo


# =============================================================================
# 1. ESTADO ESTRUTURADO VERSIONADO E GRAVAÇÃO ATÔMICA
# =============================================================================

def test_estado_estruturado_versionado_inicializacao(tmp_path):
    """1.1: Valida criação atômica e conformidade com schema 1.0 de _pipeline_state.json."""
    mgr = PipelineStateManager(tmp_path, ideia="App Finanças Pessoais", total_fases=7)
    estado = mgr.inicializar(resume=False)

    estado_file = tmp_path / ".aidd" / "cache" / "_pipeline_state.json"
    assert estado_file.exists()

    # Validação estrita via JSON Schema Draft 2020-12
    dados = json.loads(estado_file.read_text(encoding="utf-8"))
    validar_pipeline_state(dados)

    assert dados["schema_version"] == "1.0"
    assert dados["ideia"] == "App Finanças Pessoais"
    assert dados["status_global"] == "EM_ANDAMENTO"
    assert dados["total_fases"] == 7
    assert isinstance(dados["fases"], dict)


def test_transicoes_da_maquina_de_estados(tmp_path):
    """1.2: Valida transições de estado (EM_ANDAMENTO, COMPLETO, FALHOU) e persistência atômica."""
    mgr = PipelineStateManager(tmp_path, ideia="App Tarefas", total_fases=7)
    mgr.inicializar(resume=False)

    # Iniciar Fase 1
    mgr.registrar_fase_iniciada("fase_1_pesquisador", "Pesquisador", 1)
    estado = json.loads(mgr.estado_path.read_text(encoding="utf-8"))
    assert estado["fases"]["fase_1_pesquisador"]["status"] == "EM_ANDAMENTO"
    assert estado["fase_atual"] == "fase_1_pesquisador"

    # Concluir Fase 1
    mgr.registrar_fase_concluida(
        "fase_1_pesquisador",
        artefatos=["_phase_01_index.json", "data/insights_phase1.json"],
        tokens_consumidos=150,
    )
    estado = json.loads(mgr.estado_path.read_text(encoding="utf-8"))
    assert estado["fases"]["fase_1_pesquisador"]["status"] == "COMPLETO"
    assert estado["fases_completas"]["fase_1_pesquisador"] is True
    assert estado["fases"]["fase_1_pesquisador"]["tokens_consumidos"] == 150

    # Falhar Fase 2
    mgr.registrar_fase_falhou("fase_2_analisador", erro="Falha ao analisar requisitos", detalhe="Timeout de rede")
    estado = json.loads(mgr.estado_path.read_text(encoding="utf-8"))
    assert estado["status_global"] == "FALHOU"
    assert estado["fase_que_falhou"] == "fase_2_analisador"
    assert estado["erro"] == "Falha ao analisar requisitos"
    assert estado["detalhe"] == "Timeout de rede"
    assert estado["fases"]["fase_2_analisador"]["status"] == "FALHOU"


# =============================================================================
# 2. RETOMADA INTELIGENTE (--resume)
# =============================================================================

def test_resume_pula_fases_completas_com_artefatos_validos(tmp_path, monkeypatch):
    """2.1: --resume pula fases já concluídas sem executar lógica interna nem gastar tokens."""
    cache_dir = tmp_path / ".aidd" / "cache"
    data_dir = cache_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Criar artefatos íntegros das fases 1 e 2
    (cache_dir / "_phase_01_index.json").write_text('{"status": "COMPLETO", "tokens": {"consumidos": 0}}', encoding="utf-8")
    (data_dir / "insights_phase1.json").write_text('{"total_insights": 1, "insights": []}', encoding="utf-8")

    analise_valida = {
        "objetivo": "Construir sistema de faturamento",
        "publico_alvo": "Pequenas empresas",
        "constraints": ["LGPD", "Alta disponibilidade"],
        "stack_recomendado": {"backend": "Python/FastAPI", "db": "PostgreSQL"},
    }
    (cache_dir / "_phase_02_index.json").write_text('{"status": "COMPLETO", "tokens": {"consumidos": 100}}', encoding="utf-8")
    (data_dir / "analise_phase2.json").write_text(json.dumps(analise_valida), encoding="utf-8")

    # Pré-criar _pipeline_state.json com Fases 1 e 2 completas
    mgr = PipelineStateManager(tmp_path, ideia="Sistema Faturamento", total_fases=7)
    mgr.inicializar(resume=False)
    mgr.registrar_fase_concluida("fase_1_pesquisador", ["_phase_01_index.json", "data/insights_phase1.json"], tokens_consumidos=0)
    mgr.registrar_fase_concluida("fase_2_analisador", ["_phase_02_index.json", "data/analise_phase2.json"], tokens_consumidos=100)

    # Rastrear se fases foram chamadas
    chamadas = {"fase_1": False, "fase_2": False, "fase_3": False}

    class FakePesquisador:
        def __init__(self, *args, **kwargs): pass
        def executar(self, *args, **kwargs):
            chamadas["fase_1"] = True
            return {"status": "COMPLETO"}

    class FakeAnalisador:
        def __init__(self, *args, **kwargs): pass
        def executar(self, *args, **kwargs):
            chamadas["fase_2"] = True
            return {"status": "COMPLETO"}

    class FakeDesigner:
        def __init__(self, *args, **kwargs): pass
        def executar(self, *args, **kwargs):
            chamadas["fase_3"] = True
            # Simular falha intencional na fase 3 para parar o pipeline
            return None

    def fake_carregar_fase(num):
        if num == 1:
            from types import SimpleNamespace
            return SimpleNamespace(PesquisadorFase1=FakePesquisador)
        if num == 2:
            from types import SimpleNamespace
            return SimpleNamespace(AnalisadorFase2=FakeAnalisador)
        if num == 3:
            from types import SimpleNamespace
            return SimpleNamespace(DesignerFase3=FakeDesigner)
        raise NotImplementedError()

    monkeypatch.setattr(pipeline_completo, "_carregar_fase", fake_carregar_fase)
    monkeypatch.setattr(pipeline_completo, "_carregar_micro_ambiente", lambda num: None)
    monkeypatch.setattr(pipeline_completo, "resolver_fleet", lambda: type("Fleet", (), {"to_dict": lambda s: {}})())
    monkeypatch.setattr(pipeline_completo, "persistir_fleet_status", lambda *args, **kwargs: None)
    monkeypatch.setattr(pipeline_completo, "fleet_status_para_log", lambda *args: "")

    resultado = pipeline_completo.executar_pipeline(
        ideia="Sistema Faturamento",
        pasta_projeto=tmp_path,
        nao_interativo=True,
        resume=True,
    )

    # Fases 1 e 2 foram puladas sem executar
    assert chamadas["fase_1"] is False
    assert chamadas["fase_2"] is False
    # Fase 3 foi executada
    assert chamadas["fase_3"] is True

    assert resultado["fases_completas"]["fase_1"] is True
    assert resultado["fases_completas"]["fase_2"] is True
    assert resultado["status"] == "FALHOU"
    assert resultado["fase_que_falhou"] == "fase_3_designer"


def test_resume_nao_pula_se_artefato_estiver_faltando(tmp_path):
    """2.2: Se o status no estado for COMPLETO mas o arquivo não existir, não pode pular."""
    mgr = PipelineStateManager(tmp_path, ideia="Teste", total_fases=7)
    mgr.inicializar(resume=False)
    mgr.registrar_fase_concluida("fase_1_pesquisador", ["_phase_01_index.json", "data/insights_phase1.json"])

    # Artefato não foi criado no disco
    pode_retomar, motivo = mgr.pode_retomar_fase(
        "fase_1_pesquisador",
        ["_phase_01_index.json", "data/insights_phase1.json"],
        schema_tipo="cache_insights_phase1",
    )
    assert pode_retomar is False
    assert "não existe no disco" in motivo


# =============================================================================
# 3. VALIDAÇÃO JSON SCHEMA NA FRONTEIRA INTER-FASES
# =============================================================================

def test_fronteira_leitura_detecta_violacao_schema(tmp_path):
    """3.1: Artefato sem campos obrigatórios falha na validação jsonschema com mensagem explicativa."""
    arquivo_invalido = tmp_path / "analise_phase2.json"
    # Falta 'stack_recomendado' e 'constraints'
    arquivo_invalido.write_text(
        json.dumps({"objetivo": "App Financeiro", "publico_alvo": "Investidores"}),
        encoding="utf-8",
    )

    ok, dados, erro = ler_cache_com_validacao(
        arquivo_invalido,
        schema_tipo="cache_analise_phase2",
        fase_origem="fase_2_analisador",
        fase_destino="fase_3_designer",
    )

    assert ok is False
    assert dados is None
    assert "violou o contrato do schema 'cache_analise_phase2'" in erro
    assert "Reexecute a fase_2_analisador" in erro


def test_pipeline_interrompe_quando_cache_viola_schema(tmp_path, monkeypatch):
    """3.2: Pipeline para e registra falha estruturada quando cache viola schema na fronteira."""
    cache_dir = tmp_path / ".aidd" / "cache"
    data_dir = cache_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    class FakePesquisadorInvalido:
        def __init__(self, *args, **kwargs): pass
        def executar(self, *args, **kwargs):
            # Salva insights com schema violado (total_insights como string)
            (data_dir / "insights_phase1.json").write_text('{"total_insights": "invalido"}', encoding="utf-8")
            (cache_dir / "_phase_01_index.json").write_text('{"status": "COMPLETO"}', encoding="utf-8")
            return {"status": "COMPLETO", "tokens": {"consumidos": 0}}

    from types import SimpleNamespace
    monkeypatch.setattr(pipeline_completo, "_carregar_fase", lambda num: SimpleNamespace(PesquisadorFase1=FakePesquisadorInvalido))
    monkeypatch.setattr(pipeline_completo, "_carregar_micro_ambiente", lambda num: None)
    monkeypatch.setattr(pipeline_completo, "resolver_fleet", lambda: type("Fleet", (), {"to_dict": lambda s: {}})())
    monkeypatch.setattr(pipeline_completo, "persistir_fleet_status", lambda *args, **kwargs: None)
    monkeypatch.setattr(pipeline_completo, "fleet_status_para_log", lambda *args: "")

    resultado = pipeline_completo.executar_pipeline(
        ideia="Teste Schema",
        pasta_projeto=tmp_path,
        nao_interativo=True,
        resume=False,
    )

    assert resultado["status"] == "FALHOU"
    assert resultado["fase_que_falhou"] == "fase_1_pesquisador"
    assert "violou o contrato do schema 'cache_insights_phase1'" in resultado["erro"]


# =============================================================================
# 4. TRATAMENTO DE JSON CORROMPIDO COM _FALHAR ESTRUTURADO E ORIENTATIVO
# =============================================================================

def test_ler_cache_com_json_corrompido(tmp_path):
    """4.1: ler_cache_com_validacao identifica JSON corrompido e gera instrução orientativa."""
    arquivo_corrompido = tmp_path / "insights_phase1.json"
    # JSON truncado
    arquivo_corrompido.write_text('{"total_insights": 10, "insights": [', encoding="utf-8")

    ok, dados, erro = ler_cache_com_validacao(
        arquivo_corrompido,
        schema_tipo="cache_insights_phase1",
        fase_origem="fase_1_pesquisador",
        fase_destino="fase_2_analisador",
    )

    assert ok is False
    assert dados is None
    assert "JSON corrompido no artefato de cache 'insights_phase1.json'" in erro
    assert "JSONDecodeError" in erro
    assert "Remova o arquivo" in erro


def test_pipeline_trata_pipeline_state_corrompido_ao_retomar(tmp_path, monkeypatch):
    """4.2: Se _pipeline_state.json estiver corrompido na inicialização com --resume, encerra com erro orientativo."""
    cache_dir = tmp_path / ".aidd" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    state_file = cache_dir / "_pipeline_state.json"
    state_file.write_text('{"schema_version": "1.0", "status_global": ', encoding="utf-8")  # Truncado

    monkeypatch.setattr(pipeline_completo, "verificar_llm_pronto", lambda: (True, "ok"))

    resultado = pipeline_completo.executar_pipeline(
        ideia="App Teste",
        pasta_projeto=tmp_path,
        nao_interativo=True,
        resume=True,
    )

    assert resultado["status"] == "FALHOU"
    assert resultado["fase_que_falhou"] == "inicializacao"
    assert "está corrompido" in resultado["erro"]
    assert "Remova o arquivo corrompido ou execute o pipeline sem a flag --resume" in resultado["erro"]
