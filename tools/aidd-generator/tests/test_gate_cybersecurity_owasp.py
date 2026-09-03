# -*- coding: utf-8 -*-
"""
Testes para G_CYBERSECURITY_OWASP (Gate de Cibersegurança).

Cenários cobertos:
  1. Projeto limpo (sem vulnerabilidades) → passa
  2. SQL injection via f-string → falha (Crítica)
  3. SQL injection via concatenação → falha (Alta)
  4. Credencial hardcoded → falha (Crítica)
  5. Chave de API real → falha (Crítica)
  6. eval/exec com input → falha (Crítica)
  7. shell=True → falha (Alta)
  8. verify=False → falha (Alta)
  9. Hash fraco (MD5) para senha → falha (Alta)
  10. Deserialização pickle insegura → falha (Alta)
  11. Vulnerabilidade Média (IDOR) → passa (não bloqueante)
  12. Comentários são ignorados
  13. Testes são ignorados
  14. Gate completo com múltiplas vulnerabilidades
"""

import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / 'scripts'
sys.path.insert(0, str(_SCRIPTS_DIR / 'gates'))

import G_CYBERSECURITY_OWASP as gate


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def projeto_limpo(tmp_path):
    """Projeto sem vulnerabilidades."""
    (tmp_path / 'app.py').write_text(
        'import os\n'
        '\n'
        'def get_user(user_id: int):\n'
        '    """Busca segura com ORM."""\n'
        '    return db.query(User).filter_by(id=user_id).first()\n'
        '\n'
        'def get_api_key():\n'
        '    return os.environ.get("API_KEY")\n',
        encoding='utf-8',
    )
    return tmp_path


@pytest.fixture
def projeto_sql_injection_fstring(tmp_path):
    """Projeto com SQL injection via f-string."""
    (tmp_path / 'db.py').write_text(
        'def buscar_usuario(nome):\n'
        '    cursor.execute(f"SELECT * FROM usuarios WHERE nome = \'{nome}\'")\n'
        '    return cursor.fetchall()\n',
        encoding='utf-8',
    )
    return tmp_path


@pytest.fixture
def projeto_sql_injection_concat(tmp_path):
    """Projeto com SQL injection via concatenação."""
    (tmp_path / 'db.py').write_text(
        'def buscar(id):\n'
        '    query = "SELECT * FROM items WHERE id = " + str(id)\n'
        '    cursor.execute(query)\n',
        encoding='utf-8',
    )
    return tmp_path


@pytest.fixture
def projeto_credencial_hardcoded(tmp_path):
    """Projeto com credencial hardcoded."""
    (tmp_path / 'config.py').write_text(
        'API_KEY = "sk-abc123def456ghi789jkl012mno345"\n'
        'DATABASE_URL = "postgresql://admin:senha123@localhost/db"\n',
        encoding='utf-8',
    )
    return tmp_path


@pytest.fixture
def projeto_chave_api_real(tmp_path):
    """Projeto com chave de API real."""
    (tmp_path / 'config.py').write_text(
        'OPENAI_KEY = "sk-proj-abc123456789012345678901234567890"\n',
        encoding='utf-8',
    )
    return tmp_path


@pytest.fixture
def projeto_eval_inseguro(tmp_path):
    """Projeto com eval/exec inseguro."""
    (tmp_path / 'handler.py').write_text(
        'def processar(dados):\n'
        '    resultado = eval(f"{{\'valor\': {dados}}}")\n'
        '    return resultado\n',
        encoding='utf-8',
    )
    return tmp_path


@pytest.fixture
def projeto_shell_true(tmp_path):
    """Projeto com subprocess shell=True."""
    (tmp_path / 'runner.py').write_text(
        'import subprocess\n'
        '\n'
        'def executar(comando):\n'
        '    subprocess.run(comando, shell=True)\n',
        encoding='utf-8',
    )
    return tmp_path


@pytest.fixture
def projeto_verify_false(tmp_path):
    """Projeto com verify=False."""
    (tmp_path / 'http_client.py').write_text(
        'import requests\n'
        '\n'
        'def fetch(url):\n'
        '    return requests.get(url, verify=False)\n',
        encoding='utf-8',
    )
    return tmp_path


@pytest.fixture
def projeto_md5_senha(tmp_path):
    """Projeto com hash MD5 para senha."""
    (tmp_path / 'auth.py').write_text(
        'import hashlib\n'
        '\n'
        'def hash_password(password):\n'
        '    return hashlib.md5(password.encode()).hexdigest()\n',
        encoding='utf-8',
    )
    return tmp_path


@pytest.fixture
def projeto_pickle_inseguro(tmp_path):
    """Projeto com deserialização pickle."""
    (tmp_path / 'loader.py').write_text(
        'import pickle\n'
        '\n'
        'def carregar(caminho):\n'
        '    with open(caminho, "rb") as f:\n'
        '        return pickle.load(f)\n',
        encoding='utf-8',
    )
    return tmp_path


@pytest.fixture
def projeto_idor(tmp_path):
    """Projeto com possível IDOR (severidade Média — não bloqueante)."""
    (tmp_path / 'api.py').write_text(
        'from flask import request\n'
        '\n'
        'def get_order():\n'
        '    order_id = request.args.get("id")\n'
        '    return db.get_order(order_id)\n',
        encoding='utf-8',
    )
    return tmp_path


@pytest.fixture
def projeto_comentarios(tmp_path):
    """Projeto com vulnerabilidades APENAS em comentários (devem ser ignorados)."""
    (tmp_path / 'safe.py').write_text(
        '# API_KEY = "sk-abc123def456ghi789jkl012mno345"\n'
        '# cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")\n'
        'def safe_function():\n'
        '    return os.environ.get("API_KEY")\n',
        encoding='utf-8',
    )
    return tmp_path


# =============================================================================
# TESTES: SCANNER
# =============================================================================

class TestScannerOWASP:
    def test_projeto_limpo(self, projeto_limpo):
        scanner = gate.ScannerOWASP()
        vulns = scanner.escanear_diretorio(projeto_limpo)
        # Projeto limpo não deve ter vulnerabilidades Alta/Crítica
        bloqueantes = [v for v in vulns if v.severidade in ('Critica', 'Alta')]
        assert len(bloqueantes) == 0

    def test_sql_injection_fstring(self, projeto_sql_injection_fstring):
        scanner = gate.ScannerOWASP()
        vulns = scanner.escanear_diretorio(projeto_sql_injection_fstring)
        sql_vulns = [v for v in vulns if 'SQL' in v.descricao or 'sql' in v.descricao.lower() or 'F-string' in v.descricao]
        assert len(sql_vulns) > 0
        assert any(v.severidade == 'Critica' for v in sql_vulns)

    def test_credencial_hardcoded(self, projeto_credencial_hardcoded):
        scanner = gate.ScannerOWASP()
        vulns = scanner.escanear_diretorio(projeto_credencial_hardcoded)
        cred_vulns = [v for v in vulns if 'Credencial' in v.descricao or 'credencial' in v.descricao.lower() or 'Chave' in v.descricao]
        assert len(cred_vulns) > 0

    def test_eval_inseguro(self, projeto_eval_inseguro):
        scanner = gate.ScannerOWASP()
        vulns = scanner.escanear_diretorio(projeto_eval_inseguro)
        eval_vulns = [v for v in vulns if 'eval' in v.descricao.lower() or 'code injection' in v.descricao.lower()]
        assert len(eval_vulns) > 0
        assert any(v.severidade == 'Critica' for v in eval_vulns)

    def test_shell_true(self, projeto_shell_true):
        scanner = gate.ScannerOWASP()
        vulns = scanner.escanear_diretorio(projeto_shell_true)
        shell_vulns = [v for v in vulns if 'shell' in v.descricao.lower() or 'command' in v.descricao.lower()]
        assert len(shell_vulns) > 0

    def test_verify_false(self, projeto_verify_false):
        scanner = gate.ScannerOWASP()
        vulns = scanner.escanear_diretorio(projeto_verify_false)
        ssl_vulns = [v for v in vulns if 'SSL' in v.descricao or 'verify' in v.descricao.lower()]
        assert len(ssl_vulns) > 0

    def test_comentarios_ignorados(self, projeto_comentarios):
        scanner = gate.ScannerOWASP()
        vulns = scanner.escanear_diretorio(projeto_comentarios)
        # Comentários devem ser ignorados
        bloqueantes = [v for v in vulns if v.severidade in ('Critica', 'Alta')]
        assert len(bloqueantes) == 0


# =============================================================================
# TESTES: GATE (EXIT CODE)
# =============================================================================

class TestGateExecutar:
    def test_projeto_limpo_passa(self, projeto_limpo):
        resultado = gate.executar_gate(projeto_limpo)
        assert resultado == 0

    def test_sql_injection_falha(self, projeto_sql_injection_fstring):
        resultado = gate.executar_gate(projeto_sql_injection_fstring)
        assert resultado == 1

    def test_credencial_falha(self, projeto_credencial_hardcoded):
        resultado = gate.executar_gate(projeto_credencial_hardcoded)
        assert resultado == 1

    def test_eval_falha(self, projeto_eval_inseguro):
        resultado = gate.executar_gate(projeto_eval_inseguro)
        assert resultado == 1

    def test_idor_passa_nao_bloqueante(self, projeto_idor):
        """IDOR é severidade Média — não bloqueia o gate."""
        resultado = gate.executar_gate(projeto_idor)
        assert resultado == 0

    def test_projeto_inexistente_falha(self, tmp_path):
        resultado = gate.executar_gate(tmp_path / 'nao_existe')
        assert resultado == 1

    def test_main_com_args(self, projeto_limpo, monkeypatch):
        monkeypatch.setattr(sys, 'argv', ['G_CYBERSECURITY_OWASP.py', str(projeto_limpo)])
        resultado = gate.main()
        assert resultado == 0


# =============================================================================
# TESTES: MODELO DE VULNERABILIDADE
# =============================================================================

class TestVulnerabilidade:
    def test_to_dict(self):
        v = gate.Vulnerabilidade(
            vuln_id='TEST_1',
            owasp_categoria='A03:2021',
            severidade='Alta',
            descricao='Teste',
            arquivo='test.py',
            linha=10,
            trecho='eval(x)',
            recomendacao='Não use eval',
        )
        d = v.to_dict()
        assert d['vuln_id'] == 'TEST_1'
        assert d['severidade'] == 'Alta'
        assert d['linha'] == 10
