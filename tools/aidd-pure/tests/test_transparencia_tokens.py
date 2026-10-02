# -*- coding: utf-8 -*-
import sys
from pathlib import Path

_PHASES_DIR = Path(__file__).resolve().parent.parent / 'scripts' / 'phases'
if str(_PHASES_DIR) not in sys.path:
    sys.path.insert(0, str(_PHASES_DIR))

def test_designer_contaminacao_mista_resulta_em_autodeclarado(tmp_path, monkeypatch):
    import importlib
    designer_mod = importlib.import_module('03_designer')
    chamadas = 0
    def fake_solicitar(prompt, contexto, fase, modelo=None, timeout_delegacao=30):
        nonlocal chamadas
        chamadas += 1
        origem = 'medido_api' if chamadas == 1 else 'autodeclarado'
        return {
            'conteudo': '{"camadas": [{"nome": "c1", "numero": 1, "responsabilidade": "r", "artefatos": ["a.py"]}], "scripts": [{"nome": "s1.py", "camada": 1, "objetivo": "obj", "pseudocodigo": "p", "determinismo_percentual": 90, "ferramentas": []}], "percentual_determinismo": 90, "total_tokens": 100, "ferramentas": [{"nome": "f", "justificativa": "j", "alternativa_rejeitada": "a"}], "gates": [{"nome": "G1", "comando_verificacao": "exit 0", "criterio_sucesso": "ok", "tipo": "mecanico"}]}',
            'tokens_consumidos': 100,
            'origem_medicao': origem,
            'modelo_usado': 'teste',
            'timestamp_resposta': '2026-09-05T12:00:00Z',
        }
    monkeypatch.setattr(designer_mod, 'solicitar_llm', fake_solicitar)
    designer = designer_mod.DesignerFase3(tmp_path / 'cache')
    res = designer._executar_subagentes_com_llm('ideia')
    assert res is not None
    assert designer._origem_medicao_totais == 'autodeclarado'
    assert designer._tokens_totais == 500
    gates, _ = designer_mod.ValidadorGatesPhase3.executar_todos(designer._consolidar_design(res))
    index = designer._gerar_index(designer._consolidar_design(res), gates, 1.0)
    assert index['tokens']['origem_medicao'] == 'autodeclarado'
    assert 'real' not in index['tokens']['medicao'].lower()
    assert 'litellm' not in index['tokens']['medicao'].lower()

def test_designer_todas_medido_api_resulta_em_medido_api(tmp_path, monkeypatch):
    import importlib
    designer_mod = importlib.import_module('03_designer')
    def fake_solicitar(prompt, contexto, fase, modelo=None, timeout_delegacao=30):
        return {
            'conteudo': '{"camadas": [{"nome": "c1", "numero": 1, "responsabilidade": "r", "artefatos": ["a.py"]}], "scripts": [{"nome": "s1.py", "camada": 1, "objetivo": "obj", "pseudocodigo": "p", "determinismo_percentual": 90, "ferramentas": []}], "percentual_determinismo": 90, "total_tokens": 100, "ferramentas": [{"nome": "f", "justificativa": "j", "alternativa_rejeitada": "a"}], "gates": [{"nome": "G1", "comando_verificacao": "exit 0", "criterio_sucesso": "ok", "tipo": "mecanico"}]}',
            'tokens_consumidos': 150,
            'origem_medicao': 'medido_api',
            'modelo_usado': 'litellm/gpt-4',
            'timestamp_resposta': '2026-09-05T12:00:00Z',
        }
    monkeypatch.setattr(designer_mod, 'solicitar_llm', fake_solicitar)
    designer = designer_mod.DesignerFase3(tmp_path / 'cache')
    res = designer._executar_subagentes_com_llm('ideia')
    assert res is not None
    assert designer._origem_medicao_totais == 'medido_api'
    assert designer._tokens_totais == 750
    gates, _ = designer_mod.ValidadorGatesPhase3.executar_todos(designer._consolidar_design(res))
    index = designer._gerar_index(designer._consolidar_design(res), gates, 1.0)
    assert index['tokens']['origem_medicao'] == 'medido_api'
    assert 'medido_api' in index['tokens']['medicao']

def test_implementador_contaminacao_mista_resulta_em_autodeclarado(tmp_path):
    import importlib
    imp_mod = importlib.import_module('08_implementador')
    imp = imp_mod.ImplementadorFase8(tmp_path)
    imp._origens_medicao = ['medido_api', 'autodeclarado']
    imp._tokens_totais = 800
    index = imp._gerar_index(scripts_implementados=[], resultado_pytest=None, gates=[], tempo_execucao=1.0)
    assert index['tokens']['origem_medicao'] == 'autodeclarado'
    assert 'real' not in index['tokens']['medicao'].lower()

def test_implementador_todas_medido_api_resulta_em_medido_api(tmp_path):
    import importlib
    imp_mod = importlib.import_module('08_implementador')
    imp = imp_mod.ImplementadorFase8(tmp_path)
    imp._origens_medicao = ['medido_api', 'medido_api', 'medido_api']
    imp._tokens_totais = 1200
    index = imp._gerar_index(scripts_implementados=[], resultado_pytest=None, gates=[], tempo_execucao=1.0)
    assert index['tokens']['origem_medicao'] == 'medido_api'
    assert 'medido_api' in index['tokens']['medicao']
