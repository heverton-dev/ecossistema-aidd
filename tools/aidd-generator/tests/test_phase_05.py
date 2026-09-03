# -*- coding: utf-8 -*-
"""
Testes reais da Phase 5 (Criador de Projeto) — Correção 5/5.

Cobre: gates E1-E5 + S1 (auditoria de segurança), CriadorProjetoFase5
(_criar_estrutura, _criar_arquivos_configuracao, _criar_sqlite,
_git_init_commit, _gerar_index, executar) e main(). Fase 100% determinística.
"""

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest


# =============================================================================
# HELPERS
# =============================================================================

def configurar_git(monkeypatch):
    """Identidade git via env vars (funciona em CI sem user.name/email)."""
    monkeypatch.setenv('GIT_AUTHOR_NAME', 'Teste AIDD')
    monkeypatch.setenv('GIT_AUTHOR_EMAIL', 'teste@aidd.local')
    monkeypatch.setenv('GIT_COMMITTER_NAME', 'Teste AIDD')
    monkeypatch.setenv('GIT_COMMITTER_EMAIL', 'teste@aidd.local')


def criar_projeto_completo(pasta: Path):
    """Cria um projeto que passa em todos os gates E1-E5 + S1."""
    (pasta / '.claude').mkdir(parents=True)
    (pasta / '.aidd').mkdir(parents=True)
    (pasta / 'scripts').mkdir(parents=True)
    (pasta / '.claude' / 'CLAUDE.md').write_text('# Setup', encoding='utf-8')
    (pasta / '.aidd' / 'config.json').write_text('{}', encoding='utf-8')
    (pasta / '.aidd' / 'rules.md').write_text('# Regras', encoding='utf-8')
    (pasta / 'scripts' / 'orquestrador.py').write_text('print("ok")\n', encoding='utf-8')
    (pasta / 'README.md').write_text('# Projeto\n\n## Segurança\n\ncredenciais via env\n', encoding='utf-8')
    (pasta / '.gitignore').write_text('.env\nsecrets.json\n', encoding='utf-8')
    (pasta / 'requirements.txt').write_text('requests>=2.31.0\n', encoding='utf-8')
    (pasta / 'pytest.ini').write_text('[pytest]\ntestpaths = tests\npythonpath = src\n', encoding='utf-8')
    conn = sqlite3.connect(str(pasta / 'estado_projeto.db'))
    conn.execute('CREATE TABLE yt_videos (id INTEGER PRIMARY KEY)')
    conn.commit()
    conn.close()


def git_init_commit(pasta: Path):
    """git init + add + commit com identidade via env vars."""
    (pasta / 'a.txt').write_text('x', encoding='utf-8')
    subprocess.run(['git', 'init'], cwd=str(pasta), capture_output=True)
    subprocess.run(['git', 'add', '.'], cwd=str(pasta), capture_output=True)
    subprocess.run(['git', 'commit', '-m', 'feat: inicial'], cwd=str(pasta), capture_output=True)


# =============================================================================
# GATE (estrutura base)
# =============================================================================

def test_gate_to_dict(criador_05):
    assert criador_05.Gate('E1', 'd', True, 'x').to_dict()['status'] == 'PASSOU'
    assert criador_05.Gate('E1', 'd', False, 'x').to_dict()['status'] == 'FALHOU'


# =============================================================================
# GATES E1-E5 + S1
# =============================================================================

def test_gate_e1_arquivos_criados(criador_05, tmp_path):
    criar_projeto_completo(tmp_path)
    gate = criador_05.ValidadorGatesPhase5._gate_e1_arquivos_criados(tmp_path)
    assert gate.passou is True
    assert '7/7' in gate.detalhes

    vazio = tmp_path / 'vazio'
    vazio.mkdir()
    gate_falhou = criador_05.ValidadorGatesPhase5._gate_e1_arquivos_criados(vazio)
    assert gate_falhou.passou is False


def test_gate_e2_git_commit(criador_05, tmp_path, tmp_path_factory, monkeypatch):
    configurar_git(monkeypatch)
    git_init_commit(tmp_path)

    gate = criador_05.ValidadorGatesPhase5._gate_e2_git_commit(tmp_path)
    # Nota: o gate E2 retorna `passou` como string truthy (não bool)
    assert gate.passou
    assert gate.to_dict()['status'] == 'PASSOU'
    assert 'feat: inicial' in gate.detalhes

    # Fora do repo git (senão git log sobe a árvore e encontra o commit do pai)
    sem_git = tmp_path_factory.mktemp('sem-git')
    gate_falhou = criador_05.ValidadorGatesPhase5._gate_e2_git_commit(sem_git)
    assert not gate_falhou.passou


def test_gate_e3_sqlite_schema(criador_05, tmp_path):
    conn = sqlite3.connect(str(tmp_path / 'estado_projeto.db'))
    conn.execute('CREATE TABLE yt_videos (id INTEGER PRIMARY KEY)')
    conn.commit()
    conn.close()

    gate = criador_05.ValidadorGatesPhase5._gate_e3_sqlite_schema(tmp_path)
    assert gate.passou is True
    assert '1 tabelas' in gate.detalhes

    sem_db = tmp_path / 'sem-db'
    sem_db.mkdir()
    gate_falhou = criador_05.ValidadorGatesPhase5._gate_e3_sqlite_schema(sem_db)
    assert gate_falhou.passou is False


def test_gate_e4_permissoes(criador_05, tmp_path):
    (tmp_path / 'scripts').mkdir()
    (tmp_path / 'scripts' / 'x.py').write_text('print(1)\n', encoding='utf-8')
    gate = criador_05.ValidadorGatesPhase5._gate_e4_permissoes(tmp_path)
    assert gate.passou is True

    sem_scripts = tmp_path / 'sem-scripts'
    sem_scripts.mkdir()
    gate_falhou = criador_05.ValidadorGatesPhase5._gate_e4_permissoes(sem_scripts)
    assert gate_falhou.passou is False


def test_gate_s1_auditoria_seguranca_ok(criador_05, tmp_path):
    criar_projeto_completo(tmp_path)
    gate = criador_05.ValidadorGatesPhase5._gate_s1_auditoria_seguranca(tmp_path)
    assert gate.passou is True


def test_gate_s1_auditoria_seguranca_env_fora_gitignore(criador_05, tmp_path):
    criar_projeto_completo(tmp_path)
    (tmp_path / '.gitignore').write_text('apenas isso\n', encoding='utf-8')
    gate = criador_05.ValidadorGatesPhase5._gate_s1_auditoria_seguranca(tmp_path)
    assert gate.passou is False
    assert '.env' in gate.detalhes


def test_gate_s1_auditoria_seguranca_secret_hardcoded(criador_05, tmp_path):
    criar_projeto_completo(tmp_path)
    # Padrão detectado: 'api_key=' sem espaço (como o gate varre)
    (tmp_path / 'scripts' / 'vazamento.py').write_text(
        'api_key="sk-123456"\n', encoding='utf-8'
    )
    gate = criador_05.ValidadorGatesPhase5._gate_s1_auditoria_seguranca(tmp_path)
    assert gate.passou is False
    assert 'vazamento.py' in gate.detalhes


def test_executar_todos_gates(criador_05, tmp_path, monkeypatch):
    configurar_git(monkeypatch)
    criar_projeto_completo(tmp_path)
    git_init_commit(tmp_path)

    gates, todos_passaram = criador_05.ValidadorGatesPhase5.executar_todos(tmp_path)
    assert len(gates) == 5
    assert todos_passaram is True


# =============================================================================
# CRIADORPROJETOFASE5
# =============================================================================

def test_criar_symlink_ou_copia_sucesso(criador_05, tmp_path, monkeypatch, capsys):
    """Ambiente com privilégio de symlink (ex: Linux/macOS, ou Windows com
    Modo Desenvolvedor): symlink_to() não levanta erro, então o caminho de
    fallback (cópia + aviso) nunca deve executar."""
    alvo = tmp_path / 'AGENTS.md'
    alvo.write_text('conteudo real', encoding='utf-8')
    link = tmp_path / '.claude' / 'CLAUDE.md'

    chamadas = []

    def symlink_ok(self, target):
        chamadas.append((self, target))
    monkeypatch.setattr(Path, 'symlink_to', symlink_ok)

    criador_05.CriadorProjetoFase5._criar_symlink_ou_copia(link, alvo)

    assert len(chamadas) == 1
    assert chamadas[0][0] == link
    assert chamadas[0][1] == alvo.resolve()
    assert 'Não foi possível criar symlink' not in capsys.readouterr().out
    assert not link.exists()  # symlink_to mockado não grava nada de fato — sem fallback de cópia


def test_criar_symlink_ou_copia_fallback_honesto(criador_05, tmp_path, monkeypatch, capsys):
    """Sem privilégio para symlink (comum no Windows): cai para cópia,
    mas AVISA explicitamente — nunca finge que criou um symlink real."""
    alvo = tmp_path / 'AGENTS.md'
    alvo.write_text('conteudo real', encoding='utf-8')
    link = tmp_path / '.claude' / 'CLAUDE.md'

    def symlink_falha(self, *a, **kw):
        raise OSError("sem privilegio")
    monkeypatch.setattr(Path, 'symlink_to', symlink_falha)

    criador_05.CriadorProjetoFase5._criar_symlink_ou_copia(link, alvo)

    assert not link.is_symlink()
    assert link.read_text(encoding='utf-8') == 'conteudo real'
    assert 'Não foi possível criar symlink' in capsys.readouterr().out


def test_criar_symlinks_globais_wiring_fase4(criador_05, tmp_path, monkeypatch):
    """Achado na auditoria pós-Fase 5: decisões GLOBAL da Fase 4 nunca
    chegavam à Fase 5. Este teste prova que agora chegam e viram symlink
    real dentro do projeto (mockado aqui — symlink de verdade depende de
    privilégio do SO, testado separadamente no teste de fallback)."""
    global_skills = tmp_path / 'global' / 'skills'
    global_skills.mkdir(parents=True)
    (global_skills / 'exemplo.md').write_text('skill global', encoding='utf-8')

    chamadas = []
    monkeypatch.setattr(Path, 'symlink_to', lambda self, alvo, **kw: chamadas.append((self, alvo)))

    criador = criador_05.CriadorProjetoFase5(tmp_path / 'projeto')
    config_fase4 = {'decisoes': {'skills': 'GLOBAL'}, 'symlinks_paths': [str(global_skills)]}

    criados = criador._criar_symlinks_globais(config_fase4)

    assert criados == 1
    assert len(chamadas) == 1
    assert chamadas[0][0] == tmp_path / 'projeto' / '.claude' / 'skills'
    assert chamadas[0][1] == global_skills.resolve()


def test_criar_symlinks_globais_sem_config(criador_05, tmp_path):
    """Sem config_fase4 (ou vazia), executar() não tenta criar symlinks
    de skills/mcps/hooks — só AGENTS.md/CLAUDE.md, que independe disso."""
    criador = criador_05.CriadorProjetoFase5(tmp_path / 'projeto')
    assert criador._criar_symlinks_globais({}) == 0
    assert not (tmp_path / 'projeto' / '.claude' / 'skills').exists()


def test_criar_symlink_dir_ou_copia_sem_privilegio_nao_copia(criador_05, tmp_path, monkeypatch, capsys):
    """Achado real em execução multi-harness: copiar um diretório GLOBAL
    inteiro (ex: ~/.claude/skills, 39MB de conteúdo pessoal do usuário)
    como fallback bloa o projeto e viola Zero Duplicidade. Sem symlink
    real, o item GLOBAL simplesmente não é materializado — nunca copiado."""
    alvo = tmp_path / 'global_mcps'
    alvo.mkdir()
    (alvo / 'servidor.json').write_text('{}', encoding='utf-8')
    link = tmp_path / 'projeto' / '.claude' / 'mcps'

    def symlink_falha(self, *a, **kw):
        raise OSError("sem privilegio")
    monkeypatch.setattr(Path, 'symlink_to', symlink_falha)

    criado_como_symlink = criador_05.CriadorProjetoFase5._criar_symlink_dir_ou_copia(link, alvo)

    assert criado_como_symlink is False
    assert not link.exists()  # nada foi copiado — item GLOBAL simplesmente ausente
    assert 'NÃO será copiado' in capsys.readouterr().out


def test_criar_estrutura(criador_05, tmp_path):
    criador = criador_05.CriadorProjetoFase5(tmp_path / 'projeto')
    criador._criar_estrutura()
    for diretorio in criador_05.ESTRUTURA_PADRAO:
        assert (tmp_path / 'projeto' / diretorio).exists()
    assert (tmp_path / 'projeto' / '.aidd' / 'cache' / 'data').exists()
    assert (tmp_path / 'projeto' / 'scripts' / 'phases').exists()
    assert (tmp_path / 'projeto' / 'scripts' / 'gates').exists()


def test_criar_arquivos_configuracao_harness_real_via_env(criador_05, tmp_path, monkeypatch):
    """Achado crítico para testes comparativos multi-harness: harness/modelo
    eram hardcoded 'Claude Code'/'claude-haiku-4-5-20251001' SEMPRE, mesmo
    rodando em outro harness. Prova que agora refletem o ambiente real."""
    monkeypatch.setenv('AIDD_HARNESS_NAME', 'MimoCode')
    monkeypatch.setenv('AIDD_LLM_MODEL', 'mimo-v2.5-pro')

    criador = criador_05.CriadorProjetoFase5(tmp_path / 'projeto')
    criador._criar_estrutura()
    criador._criar_arquivos_configuracao('Ideia de teste')

    config = json.loads((tmp_path / 'projeto' / '.aidd' / 'config.json').read_text(encoding='utf-8'))
    assert config['harness'] == 'MimoCode'
    assert config['lm'] == 'mimo-v2.5-pro'

    settings = json.loads((tmp_path / 'projeto' / '.claude' / 'settings.json').read_text(encoding='utf-8'))
    assert settings['harness'] == 'MimoCode'
    assert settings['modelo'] == 'mimo-v2.5-pro'


def test_criar_arquivos_configuracao_sem_env_e_honesto(criador_05, tmp_path, monkeypatch):
    """Sem nenhuma variável de identificação, nunca finge ser 'Claude Code'
    — reporta 'desconhecido' (Zero Alucinação)."""
    for var in ['AIDD_HARNESS_NAME', 'AIDD_LLM_MODEL', 'LLM_MODEL', 'CLAUDECODE',
                'CLAUDE_MODEL', 'ANTHROPIC_MODEL']:
        monkeypatch.delenv(var, raising=False)

    criador = criador_05.CriadorProjetoFase5(tmp_path / 'projeto')
    criador._criar_estrutura()
    criador._criar_arquivos_configuracao('Ideia de teste')

    config = json.loads((tmp_path / 'projeto' / '.aidd' / 'config.json').read_text(encoding='utf-8'))
    assert config['harness'] == 'desconhecido'
    assert config['lm'] == 'desconhecido'


def test_criar_arquivos_configuracao(criador_05, tmp_path):
    criador = criador_05.CriadorProjetoFase5(tmp_path / 'projeto')
    criador._criar_estrutura()
    criador._criar_arquivos_configuracao('Ideia de teste')

    assert (tmp_path / 'projeto' / 'scripts' / 'orquestrador.py').exists()
    assert (tmp_path / 'projeto' / 'AGENTS.md').exists()
    assert (tmp_path / 'projeto' / '.claude' / 'CLAUDE.md').exists()
    # .claude/CLAUDE.md deve refletir AGENTS.md (symlink real ou cópia honesta
    # de fallback quando o SO não permite symlink) — nunca conteúdo próprio
    assert (tmp_path / 'projeto' / '.claude' / 'CLAUDE.md').read_text(encoding='utf-8') == \
        (tmp_path / 'projeto' / 'AGENTS.md').read_text(encoding='utf-8')
    assert (tmp_path / 'projeto' / '.claude' / 'settings.json').exists()
    assert (tmp_path / 'projeto' / '.aidd' / 'config.json').exists()
    assert (tmp_path / 'projeto' / '.aidd' / 'rules.md').exists()
    assert (tmp_path / 'projeto' / 'requirements.txt').exists()
    assert (tmp_path / 'projeto' / 'README.md').exists()
    assert (tmp_path / 'projeto' / '.gitignore').exists()

    config = json.loads((tmp_path / 'projeto' / '.aidd' / 'config.json').read_text(encoding='utf-8'))
    assert config['ideia_original'] == 'Ideia de teste'
    assert config['arquitetura'] == 'AIDD 5-camadas'

    claude_md = (tmp_path / 'projeto' / '.claude' / 'CLAUDE.md').read_text(encoding='utf-8')
    assert 'Ideia de teste' in claude_md


def test_criar_sqlite(criador_05, tmp_path):
    criador = criador_05.CriadorProjetoFase5(tmp_path / 'projeto')
    criador._criar_estrutura()
    criador._criar_sqlite()

    db_path = tmp_path / 'projeto' / 'estado_projeto.db'
    assert db_path.exists()
    conn = sqlite3.connect(str(db_path))
    tabelas = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    conn.close()
    assert any('yt_videos_processados' in t[0] for t in tabelas)


def test_git_init_commit(criador_05, tmp_path, monkeypatch):
    configurar_git(monkeypatch)
    criador = criador_05.CriadorProjetoFase5(tmp_path / 'projeto')
    criador._criar_estrutura()
    criador._criar_arquivos_configuracao('Ideia')
    criador._git_init_commit('Ideia')

    resultado = subprocess.run(
        ['git', 'log', '--oneline', '-1'],
        cwd=str(tmp_path / 'projeto'), capture_output=True, text=True,
        encoding='utf-8', errors='replace'
    )
    assert resultado.returncode == 0
    assert 'Inicialização de projeto AIDD' in resultado.stdout


def test_gerar_index(criador_05, tmp_path, monkeypatch):
    configurar_git(monkeypatch)
    criar_projeto_completo(tmp_path)
    git_init_commit(tmp_path)

    gates, _ = criador_05.ValidadorGatesPhase5.executar_todos(tmp_path)
    index = criador_05.CriadorProjetoFase5(tmp_path)._gerar_index(gates, 1.0)

    assert index['fase_id'] == 'phase_05_creation'
    assert index['tokens']['consumidos'] == 0
    assert index['tokens']['percentual_determinismo'] == '100%'
    assert index['processamento']['git_commits'] >= 1
    assert index['processamento']['arquivos_criados'] >= 1
    assert index['processamento']['diretorios_criados'] >= 1
    esperado = sum(1 for f in tmp_path.rglob('*') if f.is_symlink())
    assert index['processamento']['symlinks_criados'] == esperado  # medido via rglob, nunca fixo
    assert 'gates_executados' in index


def test_executar_sucesso(criador_05, tmp_path, monkeypatch):
    configurar_git(monkeypatch)
    criador = criador_05.CriadorProjetoFase5(tmp_path / 'projeto')
    index = criador.executar('Sistema de vídeos YouTube')

    assert index is not None
    assert index['status'] == 'COMPLETO'
    assert (tmp_path / 'projeto' / '.aidd' / 'cache' / '_phase_05_index.json').exists()
    assert (tmp_path / 'projeto' / 'estado_projeto.db').exists()
    assert (tmp_path / 'projeto' / 'scripts' / 'orquestrador.py').exists()


# =============================================================================
# MAIN (CLI)
# =============================================================================

def test_main_sucesso(criador_05, tmp_path, monkeypatch):
    monkeypatch.setattr(
        sys, 'argv',
        ['05_criador.py', str(tmp_path / 'projeto'), '--ideia', 'Ideia de teste']
    )
    monkeypatch.setattr(
        criador_05.CriadorProjetoFase5, 'executar',
        lambda self, ideia, config_fase4=None: {'status': 'COMPLETO'}
    )
    with pytest.raises(SystemExit) as exc:
        criador_05.main()
    assert exc.value.code == 0


def test_main_falha(criador_05, tmp_path, monkeypatch):
    monkeypatch.setattr(
        sys, 'argv',
        ['05_criador.py', str(tmp_path / 'projeto'), '--ideia', 'Ideia de teste']
    )
    monkeypatch.setattr(
        criador_05.CriadorProjetoFase5, 'executar',
        lambda self, ideia, config_fase4=None: None
    )
    with pytest.raises(SystemExit) as exc:
        criador_05.main()
    assert exc.value.code == 1