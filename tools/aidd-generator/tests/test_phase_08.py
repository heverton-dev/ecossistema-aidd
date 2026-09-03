# -*- coding: utf-8 -*-
"""
Testes reais da Phase 8 (Implementador com Verificação).

Cobre: gates I1-I4, ImplementadorFase8 (escrita real de arquivos, parsing
real de saída de pytest via subprocess mockado, loop de correção real com
2+ tentativas) e main(). O LLM é mockado (protocolo delegado), mas a
lógica de verificação/correção é exercitada de verdade.
"""

import json
import sys
from pathlib import Path

import pytest


# =============================================================================
# HELPERS
# =============================================================================

def resposta_llm(conteudo_dict, tokens=100):
    return {
        'conteudo': json.dumps(conteudo_dict, ensure_ascii=False),
        'tokens_consumidos': tokens,
        'modelo_usado': 'teste',
        'timestamp_resposta': '2026-08-30T00:00:00Z',
    }


IMPL_VALIDA = {
    'codigo': 'def somar(a, b):\n    return a + b\n',
    'teste': 'from pacote.somar import somar\n\ndef test_somar():\n    assert somar(2, 3) == 5\n',
    'caminho_relativo': 'pacote/somar.py',
    'caminho_teste': 'test_somar.py',
}

DESIGN_COM_1_SCRIPT = {
    'design': {
        'scripts': [
            {'nome': 'somar.py', 'responsabilidade': 'somar dois numeros', 'pseudocodigo': '1. retornar a+b'}
        ]
    }
}

ANALISE_COM_STACK = {
    'stack_recomendado': {'linguagem': 'Python 3.11+', 'framework': 'None', 'banco': 'None'}
}


class PytestFake:
    """Simula subprocess.CompletedProcess para as chamadas de pytest real."""
    def __init__(self, passaram=1, falharam=0, returncode=0, extra_saida=''):
        saida = f"{passaram} passed" if falharam == 0 else f"{passaram} passed, {falharam} failed"
        self.stdout = f"{extra_saida}\n{saida}\n" if extra_saida else f"{saida}\n"
        self.stderr = ''
        self.returncode = returncode


# =============================================================================
# GATE (estrutura base)
# =============================================================================

def test_gate_to_dict(implementador_08):
    gate = implementador_08.Gate('I1', 'descricao', True, 'detalhes')
    assert gate.to_dict() == {
        'gate_id': 'I1', 'descricao': 'descricao', 'status': 'PASSOU', 'detalhes': 'detalhes'
    }
    assert implementador_08.Gate('I1', 'd', False, 'x').to_dict()['status'] == 'FALHOU'


# =============================================================================
# GATES I1-I4
# =============================================================================

def test_gate_i1_scripts_implementados(implementador_08, tmp_path):
    (tmp_path / 'src' / 'pacote').mkdir(parents=True)
    (tmp_path / 'src' / 'pacote' / 'somar.py').write_text('x', encoding='utf-8')

    scripts = [{'caminho_relativo': 'pacote/somar.py'}]
    gate = implementador_08.ValidadorGatesPhase8._gate_i1_scripts_implementados(tmp_path, scripts)
    assert gate.passou is True
    assert '1/1' in gate.detalhes

    scripts_faltando = [{'caminho_relativo': 'pacote/somar.py'}, {'caminho_relativo': 'pacote/nao_existe.py'}]
    gate_falhou = implementador_08.ValidadorGatesPhase8._gate_i1_scripts_implementados(tmp_path, scripts_faltando)
    assert gate_falhou.passou is False
    assert '1/2' in gate_falhou.detalhes


def test_gate_i1_lista_vazia_falha(implementador_08, tmp_path):
    gate = implementador_08.ValidadorGatesPhase8._gate_i1_scripts_implementados(tmp_path, [])
    assert gate.passou is False


def test_gate_i2_testes_coletam(implementador_08):
    gate_ok = implementador_08.ValidadorGatesPhase8._gate_i2_testes_coletam({'erro_coleta': False})
    assert gate_ok.passou is True

    gate_falhou = implementador_08.ValidadorGatesPhase8._gate_i2_testes_coletam({'erro_coleta': True})
    assert gate_falhou.passou is False

    gate_sem_resultado = implementador_08.ValidadorGatesPhase8._gate_i2_testes_coletam(None)
    assert gate_sem_resultado.passou is False


def test_gate_i3_testes_passam(implementador_08):
    gate_ok = implementador_08.ValidadorGatesPhase8._gate_i3_testes_passam({'passaram': 5, 'total': 5})
    assert gate_ok.passou is True

    gate_parcial = implementador_08.ValidadorGatesPhase8._gate_i3_testes_passam({'passaram': 3, 'total': 5})
    assert gate_parcial.passou is False
    assert '3/5' in gate_parcial.detalhes

    gate_zero = implementador_08.ValidadorGatesPhase8._gate_i3_testes_passam({'passaram': 0, 'total': 0})
    assert gate_zero.passou is False


def test_gate_i4_sem_cli_nao_bloqueia(implementador_08, tmp_path):
    gate = implementador_08.ValidadorGatesPhase8._gate_i4_cli_executa(tmp_path)
    assert gate.passou is True
    assert 'não aplicável' in gate.detalhes


def test_gate_i4_cli_falha_retorna_gate_falho(implementador_08, tmp_path):
    (tmp_path / 'main.py').write_text('import sys\nsys.exit(1)\n', encoding='utf-8')
    gate = implementador_08.ValidadorGatesPhase8._gate_i4_cli_executa(tmp_path)
    assert gate.passou is False


def test_gate_i4_excecao_ao_rodar_retorna_gate_falho(implementador_08, tmp_path, monkeypatch):
    (tmp_path / 'main.py').write_text('x', encoding='utf-8')
    monkeypatch.setattr(
        implementador_08.subprocess, 'run',
        lambda *a, **kw: (_ for _ in ()).throw(TimeoutError("travou"))
    )
    gate = implementador_08.ValidadorGatesPhase8._gate_i4_cli_executa(tmp_path)
    assert gate.passou is False
    assert 'Erro ao rodar' in gate.detalhes


def test_gate_i3_sem_resultado_pytest(implementador_08):
    gate = implementador_08.ValidadorGatesPhase8._gate_i3_testes_passam(None)
    assert gate.passou is False


def test_executar_todos_gates(implementador_08, tmp_path):
    (tmp_path / 'src' / 'pacote').mkdir(parents=True)
    (tmp_path / 'src' / 'pacote' / 'somar.py').write_text('x', encoding='utf-8')
    scripts = [{'caminho_relativo': 'pacote/somar.py'}]
    resultado_pytest = {'erro_coleta': False, 'passaram': 1, 'total': 1}
    resultado_integracao = {'erro_coleta': False, 'passaram': 1, 'total': 1, 'falharam': 0, 'erros': 0}

    gates, todos_passaram = implementador_08.ValidadorGatesPhase8.executar_todos(
        tmp_path, scripts, resultado_pytest, resultado_integracao=resultado_integracao, teste_integracao_gerado=True
    )
    assert len(gates) == 5
    assert todos_passaram is True


def test_gate_i5_teste_integracao_sucesso(implementador_08):
    resultado = {'erro_coleta': False, 'passaram': 2, 'falharam': 0, 'erros': 0, 'total': 2}
    gate = implementador_08.ValidadorGatesPhase8._gate_i5_teste_integracao(resultado, teste_gerado=True)
    assert gate.passou is True
    assert '2/2 teste(s) de integração passando' in gate.detalhes


def test_gate_i5_teste_integracao_falha(implementador_08):
    resultado = {'erro_coleta': False, 'passaram': 1, 'falharam': 1, 'erros': 0, 'total': 2}
    gate = implementador_08.ValidadorGatesPhase8._gate_i5_teste_integracao(resultado, teste_gerado=True)
    assert gate.passou is False
    assert '1 falha(s)' in gate.detalhes


def test_gate_i5_teste_integracao_nao_gerado(implementador_08):
    gate = implementador_08.ValidadorGatesPhase8._gate_i5_teste_integracao(None, teste_gerado=False)
    assert gate.passou is False
    assert 'não gerado ou não executado' in gate.detalhes


def test_gate_i5_teste_integracao_erro_coleta(implementador_08):
    resultado = {'erro_coleta': True, 'passaram': 0, 'falharam': 0, 'erros': 1, 'total': 0}
    gate = implementador_08.ValidadorGatesPhase8._gate_i5_teste_integracao(resultado, teste_gerado=True)
    assert gate.passou is False
    assert 'Erro de coleta' in gate.detalhes


# =============================================================================
# ESCRITA REAL DE ARQUIVOS
# =============================================================================

def test_escrever_implementacao(implementador_08, tmp_path):
    imp = implementador_08.ImplementadorFase8(tmp_path)
    imp._escrever_implementacao(IMPL_VALIDA)

    codigo_path = tmp_path / 'src' / 'pacote' / 'somar.py'
    teste_path = tmp_path / 'tests' / 'test_somar.py'
    init_path = tmp_path / 'src' / 'pacote' / '__init__.py'

    assert codigo_path.read_text(encoding='utf-8') == IMPL_VALIDA['codigo']
    assert teste_path.read_text(encoding='utf-8') == IMPL_VALIDA['teste']
    assert init_path.exists()


def test_escrever_implementacao_nao_sobrescreve_init_existente(implementador_08, tmp_path):
    pacote_dir = tmp_path / 'src' / 'pacote'
    pacote_dir.mkdir(parents=True)
    (pacote_dir / '__init__.py').write_text('# conteudo real', encoding='utf-8')

    imp = implementador_08.ImplementadorFase8(tmp_path)
    imp._escrever_implementacao(IMPL_VALIDA)

    assert (pacote_dir / '__init__.py').read_text(encoding='utf-8') == '# conteudo real'


# =============================================================================
# EXECUÇÃO REAL DE PYTEST (subprocess mockado)
# =============================================================================

def test_rodar_pytest_parseia_sucesso(implementador_08, tmp_path, monkeypatch):
    monkeypatch.setattr(implementador_08.subprocess, 'run', lambda *a, **kw: PytestFake(passaram=3, falharam=0))
    imp = implementador_08.ImplementadorFase8(tmp_path)
    resultado = imp._rodar_pytest(None)
    assert resultado['passaram'] == 3
    assert resultado['falharam'] == 0
    assert resultado['total'] == 3
    assert resultado['erro_coleta'] is False


def test_rodar_pytest_detecta_erro_coleta(implementador_08, tmp_path, monkeypatch):
    monkeypatch.setattr(
        implementador_08.subprocess, 'run',
        lambda *a, **kw: PytestFake(passaram=0, falharam=0, extra_saida='ModuleNotFoundError: No module named x\nERROR collecting tests/test_x.py')
    )
    imp = implementador_08.ImplementadorFase8(tmp_path)
    resultado = imp._rodar_pytest(None)
    assert resultado['erro_coleta'] is True


def test_rodar_pytest_excecao_retorna_falha_honesta(implementador_08, tmp_path, monkeypatch):
    def levanta(*a, **kw):
        raise TimeoutError("pytest travou")
    monkeypatch.setattr(implementador_08.subprocess, 'run', levanta)
    imp = implementador_08.ImplementadorFase8(tmp_path)
    resultado = imp._rodar_pytest(None)
    assert resultado['erro_coleta'] is True
    assert resultado['total'] == 0


# =============================================================================
# LOOP DE VERIFICAÇÃO E CORREÇÃO REAL
# =============================================================================

def test_implementar_script_sucesso_primeira_tentativa(implementador_08, tmp_path, monkeypatch):
    monkeypatch.setattr(implementador_08, 'solicitar_llm', lambda **kw: resposta_llm(IMPL_VALIDA))
    monkeypatch.setattr(implementador_08.subprocess, 'run', lambda *a, **kw: PytestFake(passaram=1, falharam=0))

    imp = implementador_08.ImplementadorFase8(tmp_path)
    resultado = imp._implementar_script_com_verificacao('ideia', {}, DESIGN_COM_1_SCRIPT['design']['scripts'][0])

    assert resultado['tentativas'] == 1
    assert not resultado.get('falhou_apos_tentativas')
    assert (tmp_path / 'src' / 'pacote' / 'somar.py').exists()


def test_implementar_script_corrige_na_segunda_tentativa(implementador_08, tmp_path, monkeypatch):
    """Achado real que motivou este teste: nunca marcar sucesso sem RODAR
    e ver passar. Simula 1ª implementação com bug (teste falha de verdade),
    LLM recebe o erro real e retorna versão corrigida na 2ª chamada."""
    chamadas_llm = []

    def fake_solicitar_llm(prompt, contexto, fase, modelo=None, timeout_delegacao=30):
        chamadas_llm.append(fase)
        if fase == 'phase_08':
            return resposta_llm(dict(IMPL_VALIDA, codigo='def somar(a, b):\n    return a - b\n'))  # bug proposital
        return resposta_llm(IMPL_VALIDA)  # correção

    # Sprint 06: 3 resultados — falha, sucesso (fix), sucesso (micro-task verification)
    resultados_pytest = iter([PytestFake(passaram=0, falharam=1), PytestFake(passaram=1, falharam=0), PytestFake(passaram=1, falharam=0)])
    monkeypatch.setattr(implementador_08, 'solicitar_llm', fake_solicitar_llm)
    monkeypatch.setattr(implementador_08.subprocess, 'run', lambda *a, **kw: next(resultados_pytest))

    imp = implementador_08.ImplementadorFase8(tmp_path)
    resultado = imp._implementar_script_com_verificacao('ideia', {}, DESIGN_COM_1_SCRIPT['design']['scripts'][0])

    assert resultado['tentativas'] == 2
    assert not resultado.get('falhou_apos_tentativas')
    assert 'phase_08_fix' in chamadas_llm


def test_implementar_script_esgota_tentativas(implementador_08, tmp_path, monkeypatch):
    monkeypatch.setattr(implementador_08, 'solicitar_llm', lambda **kw: resposta_llm(IMPL_VALIDA))
    monkeypatch.setattr(implementador_08.subprocess, 'run', lambda *a, **kw: PytestFake(passaram=0, falharam=1))

    imp = implementador_08.ImplementadorFase8(tmp_path)
    resultado = imp._implementar_script_com_verificacao('ideia', {}, DESIGN_COM_1_SCRIPT['design']['scripts'][0])

    assert resultado['tentativas'] == implementador_08.MAX_TENTATIVAS_POR_SCRIPT
    assert resultado['falhou_apos_tentativas'] is True


def test_implementar_script_correcao_nao_responde(implementador_08, tmp_path, monkeypatch):
    """Se a chamada de CORREÇÃO (não a inicial) não responder, para ali
    mesmo — não trava esperando indefinidamente."""
    def fake_solicitar_llm(prompt, contexto, fase, modelo=None, timeout_delegacao=30):
        return None if fase == 'phase_08_fix' else resposta_llm(IMPL_VALIDA)

    monkeypatch.setattr(implementador_08, 'solicitar_llm', fake_solicitar_llm)
    monkeypatch.setattr(implementador_08.subprocess, 'run', lambda *a, **kw: PytestFake(passaram=0, falharam=1))

    imp = implementador_08.ImplementadorFase8(tmp_path)
    resultado = imp._implementar_script_com_verificacao('ideia', {}, DESIGN_COM_1_SCRIPT['design']['scripts'][0])

    assert resultado['falhou_apos_tentativas'] is True
    assert resultado['tentativas'] == 1


def test_implementar_script_correcao_json_invalido(implementador_08, tmp_path, monkeypatch):
    def fake_solicitar_llm(prompt, contexto, fase, modelo=None, timeout_delegacao=30):
        if fase == 'phase_08_fix':
            return {'conteudo': 'nao é json', 'tokens_consumidos': 5, 'modelo_usado': 'x', 'timestamp_resposta': 'x'}
        return resposta_llm(IMPL_VALIDA)

    monkeypatch.setattr(implementador_08, 'solicitar_llm', fake_solicitar_llm)
    monkeypatch.setattr(implementador_08.subprocess, 'run', lambda *a, **kw: PytestFake(passaram=0, falharam=1))

    imp = implementador_08.ImplementadorFase8(tmp_path)
    resultado = imp._implementar_script_com_verificacao('ideia', {}, DESIGN_COM_1_SCRIPT['design']['scripts'][0])

    assert resultado['falhou_apos_tentativas'] is True
    assert resultado['tentativas'] == 1


def test_implementar_script_llm_nao_responde(implementador_08, tmp_path, monkeypatch):
    monkeypatch.setattr(implementador_08, 'solicitar_llm', lambda **kw: None)
    imp = implementador_08.ImplementadorFase8(tmp_path)
    resultado = imp._implementar_script_com_verificacao('ideia', {}, DESIGN_COM_1_SCRIPT['design']['scripts'][0])
    assert resultado is None


def test_implementar_script_json_invalido(implementador_08, tmp_path, monkeypatch):
    monkeypatch.setattr(
        implementador_08, 'solicitar_llm',
        lambda **kw: {'conteudo': 'nao é json', 'tokens_consumidos': 10, 'modelo_usado': 'x', 'timestamp_resposta': 'x'}
    )
    imp = implementador_08.ImplementadorFase8(tmp_path)
    resultado = imp._implementar_script_com_verificacao('ideia', {}, DESIGN_COM_1_SCRIPT['design']['scripts'][0])
    assert resultado is None


# =============================================================================
# EXECUTAR() — FLUXO COMPLETO
# =============================================================================

def test_executar_sem_scripts_no_design_retorna_none(implementador_08, tmp_path):
    imp = implementador_08.ImplementadorFase8(tmp_path)
    resultado = imp.executar('ideia', ANALISE_COM_STACK, {'design': {'scripts': []}})
    assert resultado is None


def test_executar_sucesso_completo(implementador_08, tmp_path, monkeypatch):
    monkeypatch.setattr(implementador_08, 'solicitar_llm', lambda **kw: resposta_llm(IMPL_VALIDA, tokens=100))
    monkeypatch.setattr(implementador_08.subprocess, 'run', lambda *a, **kw: PytestFake(passaram=1, falharam=0))

    imp = implementador_08.ImplementadorFase8(tmp_path)
    index = imp.executar('ideia', ANALISE_COM_STACK, DESIGN_COM_1_SCRIPT)

    assert index is not None
    assert index['status'] == 'COMPLETO'
    assert index['tokens']['consumidos'] == 200  # 100 (script) + 100 (teste integracao)
    assert index['processamento']['teste_integracao_gerado'] is True
    assert index['processamento']['teste_integracao_passou'] is True
    assert (tmp_path / '.aidd' / 'cache' / '_phase_08_index.json').exists()
    assert (tmp_path / 'tests' / 'test_integracao.py').exists()


def test_executar_llm_nunca_responde(implementador_08, tmp_path, monkeypatch):
    monkeypatch.setattr(implementador_08, 'solicitar_llm', lambda **kw: None)
    imp = implementador_08.ImplementadorFase8(tmp_path)
    resultado = imp.executar('ideia', ANALISE_COM_STACK, DESIGN_COM_1_SCRIPT)
    assert resultado is None


def test_executar_gates_falham_quando_pytest_nao_passa(implementador_08, tmp_path, monkeypatch):
    monkeypatch.setattr(implementador_08, 'solicitar_llm', lambda **kw: resposta_llm(IMPL_VALIDA))
    monkeypatch.setattr(implementador_08.subprocess, 'run', lambda *a, **kw: PytestFake(passaram=0, falharam=1))

    imp = implementador_08.ImplementadorFase8(tmp_path)
    resultado = imp.executar('ideia', ANALISE_COM_STACK, DESIGN_COM_1_SCRIPT)
    assert resultado is None


def test_executar_com_falha_no_teste_integracao_reprova_gate_i5(implementador_08, tmp_path, monkeypatch):
    """Se os testes unitários passarem mas o teste de integração falhar,
    o Gate I5 reprova e a fase reporta FALHOU honestamente."""
    def fake_pytest(cmd, **kw):
        # Se estiver rodando o teste de integração
        if any('test_integracao' in arg for arg in cmd):
            return PytestFake(passaram=0, falharam=1)
        return PytestFake(passaram=1, falharam=0)

    monkeypatch.setattr(implementador_08, 'solicitar_llm', lambda **kw: resposta_llm(IMPL_VALIDA))
    monkeypatch.setattr(implementador_08.subprocess, 'run', fake_pytest)

    imp = implementador_08.ImplementadorFase8(tmp_path)
    resultado = imp.executar('ideia', ANALISE_COM_STACK, DESIGN_COM_1_SCRIPT)
    assert resultado is None

    # Verifica que o index foi escrito reportando status FALHOU e Gate I5 FALHOU
    index_path = tmp_path / '.aidd' / 'cache' / '_phase_08_index.json'
    assert index_path.exists()
    dados_index = json.loads(index_path.read_text(encoding='utf-8'))
    assert dados_index['status'] == 'FALHOU'
    gate_i5 = next(g for g in dados_index['gates_executados'] if g['gate_id'] == 'I5_teste_integracao')
    assert gate_i5['status'] == 'FALHOU'


def test_gerar_e_escrever_teste_integracao_sucesso(implementador_08, tmp_path, monkeypatch):
    impl_integracao = {
        'teste': 'from pacote.somar import somar\ndef test_int():\n    assert somar(1, 2) == 3\n',
        'caminho_teste': 'test_integracao.py'
    }
    monkeypatch.setattr(implementador_08, 'solicitar_llm', lambda **kw: resposta_llm(impl_integracao, tokens=150))
    monkeypatch.setattr(implementador_08.subprocess, 'run', lambda *a, **kw: PytestFake(passaram=1, falharam=0))

    imp = implementador_08.ImplementadorFase8(tmp_path)
    gerou, res = imp._gerar_e_escrever_teste_integracao(
        'ideia', {}, [{'caminho_relativo': 'pacote/somar.py', 'codigo': 'def somar(a, b): return a + b'}]
    )
    assert gerou is True
    assert res is not None
    assert res['passaram'] == 1
    assert (tmp_path / 'tests' / 'test_integracao.py').exists()


def test_gerar_e_escrever_teste_integracao_llm_falha(implementador_08, tmp_path, monkeypatch):
    monkeypatch.setattr(implementador_08, 'solicitar_llm', lambda **kw: None)
    imp = implementador_08.ImplementadorFase8(tmp_path)
    gerou, res = imp._gerar_e_escrever_teste_integracao('ideia', {}, [])
    assert gerou is False
    assert res is None


def test_gerar_e_escrever_teste_integracao_json_invalido(implementador_08, tmp_path, monkeypatch):
    monkeypatch.setattr(implementador_08, 'solicitar_llm', lambda **kw: {'conteudo': 'resposta invalida'})
    imp = implementador_08.ImplementadorFase8(tmp_path)
    gerou, res = imp._gerar_e_escrever_teste_integracao('ideia', {}, [])
    assert gerou is False
    assert res is None


# =============================================================================
# MAIN (CLI)
# =============================================================================

def test_main_sucesso(tmp_path, implementador_08, monkeypatch):
    monkeypatch.setattr(
        sys, 'argv',
        ['08_implementador.py', str(tmp_path), '--ideia', 'minha ideia']
    )
    monkeypatch.setattr(
        implementador_08.ImplementadorFase8, 'executar',
        lambda self, ideia, analise, design: {'status': 'COMPLETO'}
    )
    with pytest.raises(SystemExit) as exc:
        implementador_08.main()
    assert exc.value.code == 0


def test_main_falha(tmp_path, implementador_08, monkeypatch):
    monkeypatch.setattr(
        sys, 'argv',
        ['08_implementador.py', str(tmp_path), '--ideia', 'minha ideia']
    )
    monkeypatch.setattr(
        implementador_08.ImplementadorFase8, 'executar',
        lambda self, ideia, analise, design: None
    )
    with pytest.raises(SystemExit) as exc:
        implementador_08.main()
    assert exc.value.code == 1


# =============================================================================
# SCHEMA COMPARTILHADO & UTF-8 (COORDENAÇÃO MULTI-SCRIPT)
# =============================================================================

def test_precisa_schema_compartilhado_com_sqlite(implementador_08, tmp_path):
    imp = implementador_08.ImplementadorFase8(tmp_path)
    stack_sqlite = {'banco': 'SQLite 3'}
    assert imp._precisa_schema_compartilhado(stack_sqlite, []) is True

    stack_sem_banco = {'banco': 'None', 'linguagem': 'Python'}
    scripts_com_habito = [{'nome': 'adicionar_habito.py', 'responsabilidade': 'salva habito', 'pseudocodigo': 'INSERT INTO habitos'}]
    assert imp._precisa_schema_compartilhado(stack_sem_banco, scripts_com_habito) is True

    scripts_puros = [{'nome': 'somar.py', 'responsabilidade': 'soma 2 nums', 'pseudocodigo': 'return a+b'}]
    assert imp._precisa_schema_compartilhado(stack_sem_banco, scripts_puros) is False


def test_gerar_schema_compartilhado_sucesso(implementador_08, tmp_path, monkeypatch):
    schema_sql = "CREATE TABLE IF NOT EXISTS habitos (id INTEGER PRIMARY KEY, nome TEXT);\nCREATE TABLE IF NOT EXISTS checkins (id INTEGER PRIMARY KEY, habito_id INTEGER, data DATE);"
    monkeypatch.setattr(
        implementador_08, 'solicitar_llm',
        lambda **kw: resposta_llm({'schema_sql': schema_sql, 'tabelas': ['habitos', 'checkins']}, tokens=150)
    )

    imp = implementador_08.ImplementadorFase8(tmp_path)
    resultado = imp._gerar_schema_compartilhado('Rastreador de Hábitos', {'banco': 'SQLite'}, [{'nome': 'marcar_checkin.py'}])

    assert resultado == schema_sql
    assert imp._tokens_totais == 150


def test_executar_com_schema_compartilhado_injetado_e_persistido(implementador_08, tmp_path, monkeypatch):
    schema_sql = "CREATE TABLE IF NOT EXISTS habitos (id INTEGER PRIMARY KEY, nome TEXT);"
    prompts_enviados = []

    def fake_solicitar_llm(prompt, contexto, fase, modelo=None, timeout_delegacao=30):
        prompts_enviados.append((fase, prompt))
        if fase == 'phase_08_schema':
            return resposta_llm({'schema_sql': schema_sql, 'tabelas': ['habitos']}, tokens=120)
        return resposta_llm(IMPL_VALIDA, tokens=80)

    monkeypatch.setattr(implementador_08, 'solicitar_llm', fake_solicitar_llm)
    monkeypatch.setattr(implementador_08.subprocess, 'run', lambda *a, **kw: PytestFake(passaram=1, falharam=0))

    stack_habitos = {'stack_recomendado': {'banco': 'SQLite 3'}}
    design_habitos = {'design': {'scripts': [{'nome': 'adicionar_habito.py', 'responsabilidade': 'cria habito', 'pseudocodigo': 'INSERT'}]}}

    imp = implementador_08.ImplementadorFase8(tmp_path)
    index = imp.executar('Rastreador de hábitos', stack_habitos, design_habitos)

    assert index is not None
    assert index['status'] == 'COMPLETO'
    assert index['schema_compartilhado'] == schema_sql
    assert index['tokens']['consumidos'] == 280  # 120 (schema) + 80 (impl) + 80 (integracao)
    assert index['processamento']['teste_integracao_gerado'] is True
    assert index['processamento']['teste_integracao_passou'] is True

    # Verifica que o prompt de implementação recebeu o schema injetado
    prompt_impl = next(p for f, p in prompts_enviados if f == 'phase_08')
    assert 'SCHEMA DE BANCO DE DADOS UNIFICADO' in prompt_impl
    assert schema_sql in prompt_impl

    # Verifica que o prompt de teste de integração também recebeu o schema injetado
    prompt_int = next(p for f, p in prompts_enviados if f == 'phase_08_integracao')
    assert 'SCHEMA DE BANCO DE DADOS UNIFICADO' in prompt_int
    assert schema_sql in prompt_int


def test_gate_i3_com_erros_de_pytest_falha(implementador_08):
    # Simula pytest com 2 passados e 1 erro de fixture (total 3, mas 1 erro)
    resultado_com_erro = {'passaram': 2, 'falharam': 0, 'erros': 1, 'total': 3, 'erro_coleta': False}
    gate = implementador_08.ValidadorGatesPhase8._gate_i3_testes_passam(resultado_com_erro)
    assert gate.passou is False
    assert '1 erro(s)' in gate.detalhes


def test_escrever_implementacao_preserva_utf8_sem_mojibake(implementador_08, tmp_path):
    imp = implementador_08.ImplementadorFase8(tmp_path)
    habito_str = "H\u00e1bito"  # Hábito
    natacao_str = "Nata\u00e7\u00e3o"  # Natação
    conteudo_acentuado = {
        'codigo': f'# -*- coding: utf-8 -*-\ndef registrar_habito(nome="{natacao_str}"):\n    print(f"{habito_str} \'{{nome}}\' registrado com sucesso!")\n',
        'teste': f'# -*- coding: utf-8 -*-\nfrom pacote.habito import registrar_habito\n\ndef test_habito():\n    assert "{habito_str}" == "{habito_str}"\n',
        'caminho_relativo': 'pacote/habito.py',
        'caminho_teste': 'test_habito.py',
    }
    imp._escrever_implementacao(conteudo_acentuado)

    codigo_lido = (tmp_path / 'src' / 'pacote' / 'habito.py').read_text(encoding='utf-8')
    teste_lido = (tmp_path / 'tests' / 'test_habito.py').read_text(encoding='utf-8')

    assert habito_str in codigo_lido
    assert natacao_str in codigo_lido
    assert habito_str in teste_lido
    assert "\ufffd" not in codigo_lido
    assert "\ufffd" not in teste_lido


def test_prompts_contem_regras_foreign_key_e_integridade_referencial(implementador_08):
    prompt_impl = implementador_08.PROMPT_IMPLEMENTAR_SCRIPT
    prompt_corr = implementador_08.PROMPT_CORRIGIR_SCRIPT

    # Verifica regras no prompt de implementação (prompts agora em EN — Caveman Ultra)
    assert "PRAGMA foreign_keys = ON" in prompt_impl
    assert "FOREIGN KEY" in prompt_impl
    assert "parent record" in prompt_impl.lower()
    assert "invalid reference" in prompt_impl.lower() or "nonexistent id" in prompt_impl.lower()

    # Verifica regras no prompt de correção
    assert "PRAGMA foreign_keys = ON" in prompt_corr
    assert "parent record" in prompt_corr.lower()


def test_validar_contrato_ast_detecta_autoimportacao_invalida(implementador_08):
    # Achado real (ENTREGA-FINAL, 2026-08-30): LLM gerou 'from relatorio import relatorio'
    # dentro do proprio relatorio.py, sem nunca definir a funcao de verdade. Como e
    # sintaticamente um import valido, o validador antigo tratava 'relatorio' como
    # definido e nao pegava o contrato quebrado.
    codigo = "from relatorio import relatorio\nimport sqlite3\ndef outra_funcao():\n    pass\n"
    teste = "from relatorio import relatorio\ndef test_relatorio():\n    relatorio(None)\n"
    resultado = implementador_08.ImplementadorFase8._validar_contrato_ast(codigo, teste)
    assert resultado is not None
    assert "relatorio" in resultado
    assert "autoimporta" in resultado.lower()


def test_validar_contrato_ast_import_normal_nao_e_autoimportacao(implementador_08):
    # Import legitimo de outro modulo nao deve ser confundido com autoimportacao
    codigo = "from outro_modulo import funcao_real\ndef usa_funcao():\n    return funcao_real()\n"
    teste = "from outro_modulo import funcao_real\ndef test_usa():\n    funcao_real()\n"
    resultado = implementador_08.ImplementadorFase8._validar_contrato_ast(codigo, teste)
    assert resultado is None


def test_validar_contrato_ast_detecta_autoimportacao_multipla(implementador_08):
    # Achado real (ENTREGA-FINAL, 2026-08-30): autoimportacao onde os nomes importados
    # sao DIFERENTES do nome do modulo (from coletar_dados import coletar_habitos, ...),
    # nao coberta pelo caso simples 'from X import X'. So detectavel sabendo o nome real
    # do modulo sendo implementado (passado explicitamente para a validacao).
    codigo = "from coletar_dados import coletar_habitos, coletar_checkins\nimport sqlite3\n"
    teste = "from coletar_dados import coletar_habitos, coletar_checkins\ndef test_coleta():\n    coletar_habitos(None)\n"
    resultado = implementador_08.ImplementadorFase8._validar_contrato_ast(codigo, teste, modulo='coletar_dados')
    assert resultado is not None
    assert "coletar_habitos" in resultado
    assert "autoimporta" in resultado.lower()

