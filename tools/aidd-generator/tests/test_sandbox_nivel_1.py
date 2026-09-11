# -*- coding: utf-8 -*-
"""
Testes reais do SANDBOX NÍVEL 1 (item PLAN-0018:
sandbox-nivel-1-subprocess-env-minimo-fase-08).

Cobre os 4 itens da Definition of Done: env sanitizado por allowlist, cwd
isolado em tempdir, auditoria AST de subprocessos herdando os.environ, e o
gate G_SANDBOX_NIVEL_1 que aplica essa auditoria a um projeto gerado inteiro.
Nenhum stub falso — o teste de vazamento de segredo roda um subprocess real.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from sandbox_nivel_1 import (
    SandboxNivel1,
    auditar_subprocess_env_ast,
    formatar_violacoes_auditoria,
    montar_env_minimo,
)


# =============================================================================
# montar_env_minimo — allowlist estrita (DoD item 1)
# =============================================================================

def test_montar_env_minimo_so_tem_chaves_da_allowlist():
    env = montar_env_minimo(pythonpath='/src', tmpdir='/tmp/x', path_host='/usr/bin')
    assert set(env) <= {'PATH', 'PYTHONPATH', 'PYTHONUTF8', 'TMPDIR'}
    assert env['PATH'] == '/usr/bin'
    assert env['PYTHONPATH'] == '/src'
    assert env['TMPDIR'] == '/tmp/x'
    assert env['PYTHONUTF8'] == '1'


def test_montar_env_minimo_nunca_espelha_environ_do_host(monkeypatch):
    monkeypatch.setenv('MEU_SEGREDO_API_KEY', 'sk-nao-pode-vazar')
    env = montar_env_minimo()
    assert 'MEU_SEGREDO_API_KEY' not in env
    assert set(env) <= {'PATH', 'PYTHONPATH', 'PYTHONUTF8', 'TMPDIR'}


# =============================================================================
# SandboxNivel1 — cwd isolado + env mínimo (DoD itens 1, 2 e 4 — real)
# =============================================================================

def test_sandbox_isola_cwd_em_tempdir_e_limpa_ao_sair():
    with SandboxNivel1() as sandbox:
        cwd_durante = sandbox.cwd
        assert cwd_durante.exists()
        assert cwd_durante.is_dir()
    assert not cwd_durante.exists(), 'tempdir do sandbox deveria ser removido ao sair'


def test_sandbox_subprocess_nao_enxerga_segredo_do_host(monkeypatch):
    """DoD item 4, sem stub: um subprocess real, dentro do sandbox, dumpa
    os.environ e o segredo do host precisa estar ausente."""
    monkeypatch.setenv('MEU_SEGREDO_API_KEY', 'sk-super-secreto-12345')
    with SandboxNivel1() as sandbox:
        resultado = sandbox.rodar(
            [sys.executable, '-c', 'import os; print(sorted(os.environ.keys()))'],
            capture_output=True, text=True, timeout=10,
        )
    assert resultado.returncode == 0
    assert 'MEU_SEGREDO_API_KEY' not in resultado.stdout
    assert set(eval(resultado.stdout.strip())) <= {'PATH', 'PYTHONPATH', 'PYTHONUTF8', 'TMPDIR'}


def test_sandbox_rodar_usa_cwd_e_env_do_sandbox():
    with SandboxNivel1() as sandbox:
        cwd_esperado = sandbox.cwd.resolve()
        resultado = sandbox.rodar(
            [sys.executable, '-c', 'import os; print(os.getcwd())'],
            capture_output=True, text=True, timeout=10,
        )
        assert resultado.returncode == 0
        assert Path(resultado.stdout.strip()).resolve() == cwd_esperado


# =============================================================================
# auditar_subprocess_env_ast — deteccao real via AST (DoD item 3)
# =============================================================================

@pytest.mark.parametrize('codigo', [
    'import subprocess, os\nsubprocess.run(["ls"], env=os.environ)\n',
    'import subprocess, os\nsubprocess.run(["ls"], env=os.environ.copy())\n',
    'import subprocess, os\nsubprocess.Popen(["ls"], env={**os.environ, "X": "1"})\n',
    'from subprocess import run\nimport os\nrun(["ls"], env=os.environ)\n',
])
def test_auditoria_ast_detecta_heranca_de_environ(codigo):
    violacoes = auditar_subprocess_env_ast(codigo)
    assert len(violacoes) == 1
    assert 'linha' in violacoes[0] and 'detalhe' in violacoes[0]


@pytest.mark.parametrize('codigo', [
    'import subprocess\nsubprocess.run(["ls"], env={"PATH": "/usr/bin"})\n',
    'import subprocess\nsubprocess.run(["ls"])\n',
    'x = 1\n',
])
def test_auditoria_ast_nao_marca_falso_positivo(codigo):
    assert auditar_subprocess_env_ast(codigo) == []


def test_auditoria_ast_ignora_syntax_error_sem_crashar():
    assert auditar_subprocess_env_ast('def f(:\n') == []


def test_formatar_violacoes_gera_mensagem_de_correcao():
    violacoes = auditar_subprocess_env_ast('import subprocess, os\nsubprocess.run(["ls"], env=os.environ)\n')
    msg = formatar_violacoes_auditoria(violacoes)
    assert 'CONTRATO SANDBOX QUEBRADO' in msg
    assert 'env=os.environ' in msg


# =============================================================================
# G_SANDBOX_NIVEL_1 (gate) — integração real, arquivos reais em disco
# =============================================================================

def _carregar_gate():
    import importlib.util
    gate_path = (
        Path(__file__).resolve().parent.parent
        / 'scripts' / 'gates' / 'G_SANDBOX_NIVEL_1.py'
    )
    spec = importlib.util.spec_from_file_location('G_SANDBOX_NIVEL_1', gate_path)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_gate_falha_com_arquivo_violando_sandbox(tmp_path):
    (tmp_path / 'ruim.py').write_text(
        'import subprocess, os\nsubprocess.run(["ls"], env=os.environ)\n', encoding='utf-8'
    )
    gate = _carregar_gate()
    assert gate.executar_gate(tmp_path) == 1


def test_gate_passa_com_projeto_limpo(tmp_path):
    (tmp_path / 'bom.py').write_text(
        'import subprocess\nsubprocess.run(["ls"], env={"PATH": "/usr/bin"})\n', encoding='utf-8'
    )
    gate = _carregar_gate()
    assert gate.executar_gate(tmp_path) == 0


def test_gate_falha_se_pasta_nao_existe(tmp_path):
    gate = _carregar_gate()
    assert gate.executar_gate(tmp_path / 'nao-existe') == 1
