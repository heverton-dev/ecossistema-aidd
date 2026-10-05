# -*- coding: utf-8 -*-
"""
Testes reais da Phase 4 (Decisor Global/Local) — Correção 5/5.

Cobre: gates C1-C2, DecisorFase4 (init, executar nos 2 modos,
_apresentar_modal_interativo com input() simulado, _apresentar_modal_nao_interativo,
_gerar_index) e main(). Fase 100% determinística — sem mocks de LLM.
"""

import sys
from pathlib import Path

import pytest


# =============================================================================
# GATE (estrutura base)
# =============================================================================

def test_gate_to_dict(decisor_04):
    assert decisor_04.Gate('C1', 'd', True, 'x').to_dict()['status'] == 'PASSOU'
    assert decisor_04.Gate('C1', 'd', False, 'x').to_dict()['status'] == 'FALHOU'


# =============================================================================
# GATES C1-C2
# =============================================================================

def test_gate_c1_decisoes_validas(decisor_04):
    config = {'decisoes': {'claude_md': 'LOCAL', 'skills': 'GLOBAL', 'mcps': 'LOCAL'}}
    gate = decisor_04.ValidadorGatesPhase4._gate_c1_decisoes_validas(config)
    assert gate.passou is True
    assert '3/3' in gate.detalhes

    invalida = {'decisoes': {'claude_md': 'TALVEZ'}}
    gate_falhou = decisor_04.ValidadorGatesPhase4._gate_c1_decisoes_validas(invalida)
    assert gate_falhou.passou is False

    vazia = {'decisoes': {}}
    gate_vazia = decisor_04.ValidadorGatesPhase4._gate_c1_decisoes_validas(vazia)
    assert gate_vazia.passou is False


def test_gate_c2_symlinks_resolvem(decisor_04, tmp_path):
    arquivo_real = tmp_path / 'skills'
    arquivo_real.mkdir()

    config_ok = {'symlinks_paths': [str(arquivo_real)]}
    gate = decisor_04.ValidadorGatesPhase4._gate_c2_symlinks_resolvem(config_ok)
    assert gate.passou is True

    config_falha = {'symlinks_paths': [str(tmp_path / 'nao-existe')]}
    gate_falhou = decisor_04.ValidadorGatesPhase4._gate_c2_symlinks_resolvem(config_falha)
    assert gate_falhou.passou is False
    assert 'nao-existe' in gate_falhou.detalhes

    # Achado na integração ponta a ponta: lista vazia (nada decidido GLOBAL)
    # é um estado VÁLIDO — projeto 100% LOCAL não pode bloquear a fase.
    config_vazia = {'symlinks_paths': []}
    gate_vazia = decisor_04.ValidadorGatesPhase4._gate_c2_symlinks_resolvem(config_vazia)
    assert gate_vazia.passou is True


def test_executar_todos_gates(decisor_04, tmp_path):
    skills = tmp_path / 'skills'
    skills.mkdir()
    config = {
        'decisoes': {'claude_md': 'LOCAL', 'skills': 'GLOBAL'},
        'symlinks_paths': [str(skills)],
    }
    gates, todos_passaram = decisor_04.ValidadorGatesPhase4.executar_todos(config)
    assert len(gates) == 2
    assert todos_passaram is True


# =============================================================================
# DECISORFASE4
# =============================================================================

def test_decisor_init(tmp_path, decisor_04):
    decisor = decisor_04.DecisorFase4(tmp_path / 'cache')
    assert (tmp_path / 'cache').exists()


def test_modal_interativo(decisor_04, tmp_path, monkeypatch):
    # 6 itens × (decisão + justificativa) = 12 inputs
    entradas = [
        'GLOBAL', 'just claude', 'LOCAL', 'just skills', 'GLOBAL', 'just mcps',
        'LOCAL', 'just hooks', 'LOCAL', 'just agents', 'LOCAL', 'just scripts',
    ]
    monkeypatch.setattr('builtins.input', lambda prompt='': entradas.pop(0))
    # skills = LOCAL → sem symlinks; Path.home não é usado neste caminho
    decisor = decisor_04.DecisorFase4(tmp_path / 'cache')
    config = decisor._apresentar_modal_interativo()

    assert config['decisoes']['claude_md'] == 'GLOBAL'
    assert config['decisoes']['skills'] == 'LOCAL'
    assert config['decisoes']['mcps'] == 'GLOBAL'
    assert config['decisoes']['hooks'] == 'LOCAL'
    assert config['decisoes']['agents_md'] == 'LOCAL'
    assert config['decisoes']['scripts'] == 'LOCAL'
    assert config['justificativas']['claude_md'] == 'just claude'
    assert config['symlinks_paths'] == []


def test_modal_interativo_resposta_invalida(decisor_04, tmp_path, monkeypatch):
    # Primeira resposta inválida força o loop a pedir de novo
    entradas = ['TALVEZ', 'LOCAL', 'just', 'LOCAL', 'just', 'LOCAL', 'just',
                'LOCAL', 'just', 'LOCAL', 'just', 'LOCAL', 'just']
    monkeypatch.setattr('builtins.input', lambda prompt='': entradas.pop(0))
    decisor = decisor_04.DecisorFase4(tmp_path / 'cache')
    config = decisor._apresentar_modal_interativo()
    assert config['decisoes']['claude_md'] == 'LOCAL'


def test_modal_interativo_symlink_global(decisor_04, tmp_path, monkeypatch):
    # skills = GLOBAL → symlink para ~/.claude/skills (Path.home mockado)
    skills_dir = tmp_path / '.claude' / 'skills'
    skills_dir.mkdir(parents=True)
    monkeypatch.setattr(decisor_04.Path, 'home', classmethod(lambda cls: tmp_path))

    entradas = [
        'LOCAL', 'j', 'GLOBAL', 'j', 'LOCAL', 'j',
        'LOCAL', 'j', 'LOCAL', 'j', 'LOCAL', 'j',
    ]
    monkeypatch.setattr('builtins.input', lambda prompt='': entradas.pop(0))
    decisor = decisor_04.DecisorFase4(tmp_path / 'cache')
    config = decisor._apresentar_modal_interativo()

    assert config['decisoes']['skills'] == 'GLOBAL'
    assert len(config['symlinks_paths']) == 1
    assert config['symlinks_paths'][0] == str(skills_dir)


def test_computar_symlinks_paths_cobre_skills_mcps_hooks(decisor_04, tmp_path, monkeypatch):
    """Antes desta correção, só 'skills' virava symlink_path mesmo quando
    mcps/hooks também eram GLOBAL — achado durante auditoria pós-Fase 5."""
    for item in ['skills', 'mcps', 'hooks']:
        (tmp_path / '.claude' / item).mkdir(parents=True)
    monkeypatch.setattr(decisor_04.Path, 'home', classmethod(lambda cls: tmp_path))

    decisoes = {'skills': 'GLOBAL', 'mcps': 'GLOBAL', 'hooks': 'GLOBAL', 'claude_md': 'LOCAL'}
    paths = decisor_04.DecisorFase4._computar_symlinks_paths(decisoes)

    assert sorted(Path(p).name for p in paths) == ['hooks', 'mcps', 'skills']


def test_computar_symlinks_paths_ignora_global_sem_pasta_real(decisor_04, tmp_path, monkeypatch):
    """GLOBAL sem a pasta ~/.claude/<item> existir de fato não gera symlink
    path — nunca inventa um caminho que não existe (Zero Alucinação)."""
    monkeypatch.setattr(decisor_04.Path, 'home', classmethod(lambda cls: tmp_path))
    decisoes = {'skills': 'GLOBAL', 'mcps': 'GLOBAL', 'hooks': 'GLOBAL'}

    paths = decisor_04.DecisorFase4._computar_symlinks_paths(decisoes)

    assert paths == []


def test_modal_nao_interativo_global(decisor_04, tmp_path, monkeypatch):
    skills_dir = tmp_path / '.claude' / 'skills'
    skills_dir.mkdir(parents=True)
    monkeypatch.setattr(decisor_04.Path, 'home', classmethod(lambda cls: tmp_path))

    decisor = decisor_04.DecisorFase4(tmp_path / 'cache')
    design_com_5_scripts = {'design': {'scripts': [{'nome': f's{i}.py'} for i in range(5)]}}
    config = decisor._apresentar_modal_nao_interativo(design_com_5_scripts)

    assert config['decisoes']['skills'] == 'GLOBAL'
    assert config['decisoes']['claude_md'] == 'LOCAL'
    assert config['decisoes']['mcps'] == 'GLOBAL'
    assert config['symlinks_paths'] == [str(skills_dir)]
    assert 'scripts_no_design=5' in config['justificativas']['skills']


def test_modal_nao_interativo_local(decisor_04, tmp_path):
    decisor = decisor_04.DecisorFase4(tmp_path / 'cache')
    design_com_1_script = {'design': {'scripts': [{'nome': 's1.py'}]}}
    config = decisor._apresentar_modal_nao_interativo(design_com_1_script)
    assert config['decisoes']['skills'] == 'LOCAL'
    assert config['symlinks_paths'] == []


def test_gerar_index(decisor_04):
    config = {'decisoes': {'skills': 'GLOBAL'}, 'symlinks_count': 1}
    gates, _ = decisor_04.ValidadorGatesPhase4.executar_todos({
        'decisoes': {'skills': 'GLOBAL'},
        'symlinks_paths': [],
    })
    index = decisor_04.DecisorFase4(Path('.'))._gerar_index(config, gates, 1.0)

    assert index['fase_id'] == 'phase_04_decision'
    assert index['tokens']['consumidos'] == 0
    assert index['tokens']['percentual_determinismo'] == 100
    assert index['processamento']['decisoes_tomadas'] == 1


def test_executar_nao_interativo_sucesso(decisor_04, tmp_path, monkeypatch):
    skills_dir = tmp_path / '.claude' / 'skills'
    skills_dir.mkdir(parents=True)
    monkeypatch.setattr(decisor_04.Path, 'home', classmethod(lambda cls: tmp_path))

    decisor = decisor_04.DecisorFase4(tmp_path / 'cache')
    design_com_5_scripts = {'design': {'scripts': [{'nome': f's{i}.py'} for i in range(5)]}}
    index = decisor.executar(design_com_5_scripts, nao_interativo=True)

    assert index is not None
    assert index['status'] == 'COMPLETO'
    assert (tmp_path / 'cache' / '_phase_04_index.json').exists()
    assert (tmp_path / 'cache' / 'data' / 'config_global_local_phase4.json').exists()


def test_executar_interativo_sucesso(decisor_04, tmp_path, monkeypatch):
    skills_dir = tmp_path / '.claude' / 'skills'
    skills_dir.mkdir(parents=True)
    monkeypatch.setattr(decisor_04.Path, 'home', classmethod(lambda cls: tmp_path))

    entradas = [
        'LOCAL', 'j', 'GLOBAL', 'j', 'LOCAL', 'j',
        'LOCAL', 'j', 'LOCAL', 'j', 'LOCAL', 'j',
    ]
    monkeypatch.setattr('builtins.input', lambda prompt='': entradas.pop(0))

    decisor = decisor_04.DecisorFase4(tmp_path / 'cache')
    index = decisor.executar({}, nao_interativo=False)

    assert index is not None
    assert index['status'] == 'COMPLETO'


def test_executar_gates_falham(decisor_04, tmp_path, monkeypatch):
    # Config com decisão inválida → C1 falha → executar retorna None
    monkeypatch.setattr(
        decisor_04.DecisorFase4, '_apresentar_modal_nao_interativo',
        lambda self, design: {'decisoes': {'claude_md': 'INVALIDO'}, 'symlinks_paths': [], 'justificativas': {}}
    )
    decisor = decisor_04.DecisorFase4(tmp_path / 'cache')
    assert decisor.executar({}, nao_interativo=True) is None


# =============================================================================
# MAIN (CLI)
# =============================================================================

def test_main_sucesso(decisor_04, tmp_path, monkeypatch):
    monkeypatch.setattr(
        sys, 'argv',
        ['04_decisor.py', '--cache-dir', str(tmp_path / 'cache'), '--nao-interativo']
    )
    monkeypatch.setattr(
        decisor_04.DecisorFase4, 'executar',
        lambda self, design, nao_interativo=False: {'status': 'COMPLETO'}
    )
    with pytest.raises(SystemExit) as exc:
        decisor_04.main()
    assert exc.value.code == 0


def test_main_falha(decisor_04, tmp_path, monkeypatch):
    monkeypatch.setattr(
        sys, 'argv',
        ['04_decisor.py', '--cache-dir', str(tmp_path / 'cache'), '--nao-interativo']
    )
    monkeypatch.setattr(
        decisor_04.DecisorFase4, 'executar',
        lambda self, design, nao_interativo=False: None
    )
    with pytest.raises(SystemExit) as exc:
        decisor_04.main()
    assert exc.value.code == 1