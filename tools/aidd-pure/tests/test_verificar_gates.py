# -*- coding: utf-8 -*-
"""
Testes para scripts/verificar_gates.py (Validador Central de Gates).

Cenários cobertos:
  1. Projeto limpo → todos os gates obrigatórios passam (exit 0)
  2. Projeto com vulnerabilidade OWASP → falha (exit 1)
  3. Flag --apenas para executar gate específico
  4. Flag --pular para ignorar gate
  5. Projeto inexistente → falha
"""

import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / 'scripts'
sys.path.insert(0, str(_SCRIPTS_DIR))

import verificar_gates


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def projeto_limpo(tmp_path):
    """Projeto sem problemas — todos os gates devem passar."""
    (tmp_path / 'app.py').write_text(
        'import os\n'
        '\n'
        'def get_config():\n'
        '    return os.environ.get("API_KEY")\n'
        '\n'
        'def process(data):\n'
        '    return data\n',
        encoding='utf-8',
    )
    return tmp_path


@pytest.fixture
def projeto_com_segredo(tmp_path):
    """Projeto com segredo hardcoded — gate de segredos deve falhar."""
    (tmp_path / 'config.py').write_text(
        'API_KEY = "sk-proj-abc123456789012345678901234567890"\n',
        encoding='utf-8',
    )
    return tmp_path


@pytest.fixture
def projeto_com_owasp(tmp_path):
    """Projeto com vulnerabilidade OWASP — gate de cibersegurança deve falhar."""
    (tmp_path / 'db.py').write_text(
        'def buscar(nome):\n'
        '    cursor.execute(f"SELECT * FROM users WHERE nome = \'{nome}\'")\n',
        encoding='utf-8',
    )
    return tmp_path


# =============================================================================
# TESTES: CARREGAMENTO DE MÓDULOS
# =============================================================================

class TestCarregarModulo:
    def test_carrega_modulo_existente(self):
        caminho = Path(__file__).resolve().parent.parent / 'scripts' / 'gates' / 'G_BLOQUEAR_SEGREDOS.py'
        mod = verificar_gates._carregar_modulo('G_BLOQUEAR_SEGREDOS', caminho)
        assert hasattr(mod, 'escanear_conteudo')
        assert hasattr(mod, 'main')

    def test_modulo_inexistente_erro(self, tmp_path):
        with pytest.raises((ImportError, FileNotFoundError)):
            verificar_gates._carregar_modulo('fake', tmp_path / 'nao_existe.py')


# =============================================================================
# TESTES: MAIN DO VALIDADOR
# =============================================================================

class TestVerificarGates:
    def test_projeto_limpo_passa(self, projeto_limpo, monkeypatch):
        monkeypatch.setattr(sys, 'argv', [
            'verificar_gates.py', str(projeto_limpo),
            '--pular', 'harness',  # pular harness (precisa de .env/git)
            '--pular', 'llm',      # pular llm (precisa de env vars)
        ])
        resultado = verificar_gates.main()
        assert resultado == 0

    def test_projeto_com_segredo_falha(self, projeto_com_segredo, monkeypatch):
        monkeypatch.setattr(sys, 'argv', [
            'verificar_gates.py', str(projeto_com_segredo),
            '--pular', 'harness',
            '--pular', 'llm',
        ])
        resultado = verificar_gates.main()
        assert resultado == 1

    def test_projeto_com_owasp_falha(self, projeto_com_owasp, monkeypatch):
        monkeypatch.setattr(sys, 'argv', [
            'verificar_gates.py', str(projeto_com_owasp),
            '--pular', 'harness',
            '--pular', 'llm',
        ])
        resultado = verificar_gates.main()
        assert resultado == 1

    def test_apenas_I3(self, projeto_limpo, monkeypatch):
        monkeypatch.setattr(sys, 'argv', [
            'verificar_gates.py', str(projeto_limpo),
            '--apenas', 'I3',
        ])
        resultado = verificar_gates.main()
        assert resultado == 0

    def test_apenas_owasp(self, projeto_limpo, monkeypatch):
        monkeypatch.setattr(sys, 'argv', [
            'verificar_gates.py', str(projeto_limpo),
            '--apenas', 'OWASP',
        ])
        resultado = verificar_gates.main()
        assert resultado == 0

    def test_projeto_inexistente(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sys, 'argv', [
            'verificar_gates.py', str(tmp_path / 'nao_existe'),
            '--apenas', 'I3',
        ])
        resultado = verificar_gates.main()
        assert resultado == 1


# =============================================================================
# TESTES: GATES INDIVIDUAIS VIA ORQUESTRADOR
# =============================================================================

class TestGatesIndividuais:
    def test_gate_segredos_limpo(self, projeto_limpo):
        resultado = verificar_gates._gate_bloquear_segredos(projeto_limpo)
        assert resultado == 0

    def test_gate_segredos_com_segredo(self, projeto_com_segredo):
        resultado = verificar_gates._gate_bloquear_segredos(projeto_com_segredo)
        assert resultado == 1

    def test_gate_integracao_limpo(self, projeto_limpo):
        resultado = verificar_gates._gate_integracao_cross_script(projeto_limpo)
        assert resultado == 0

    def test_gate_owasp_limpo(self, projeto_limpo):
        resultado = verificar_gates._gate_cybersecurity_owasp(projeto_limpo)
        assert resultado == 0

    def test_gate_owasp_vulneravel(self, projeto_com_owasp):
        resultado = verificar_gates._gate_cybersecurity_owasp(projeto_com_owasp)
        assert resultado == 1
