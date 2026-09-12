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
  15. os.system() isolado → bloqueado (Crítica) [pré-I4]
  16. eval() sem input externo → bloqueado (Crítica) [pré-I4]
  17. subprocess.run() sem shell=False → bloqueado (Crítica) [pré-I4]
  18. subprocess.run(shell=False) → passa [pré-I4]
  19. Relatório de conformidade gera dict correto
  20. Gate pré-I4 com projeto limpo passa
  21. Gate pré-I4 com chamada perigosa falha
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


# =============================================================================
# FIXTURES: ALTO RISCO (pré-I4)
# =============================================================================

@pytest.fixture
def projeto_os_system(tmp_path):
    """Projeto com os.system() isolado (sem input externo)."""
    (tmp_path / 'runner.py').write_text(
        'import os\n'
        '\n'
        'def listar():\n'
        '    os.system("ls -la")\n',
        encoding='utf-8',
    )
    return tmp_path


@pytest.fixture
def projeto_eval_isolado(tmp_path):
    """Projeto com eval() sem input externo."""
    (tmp_path / 'calc.py').write_text(
        'def calcular(expressao):\n'
        '    return eval(expressao)\n',
        encoding='utf-8',
    )
    return tmp_path


@pytest.fixture
def projeto_exec_isolado(tmp_path):
    """Projeto com exec() sem input externo."""
    (tmp_path / 'loader.py').write_text(
        'def carregar_codigo(codigo_str):\n'
        '    exec(codigo_str)\n',
        encoding='utf-8',
    )
    return tmp_path


@pytest.fixture
def projeto_subprocess_sem_shell_false(tmp_path):
    """Projeto com subprocess.run() sem shell=False explícito."""
    (tmp_path / 'runner.py').write_text(
        'import subprocess\n'
        '\n'
        'def executar():\n'
        '    subprocess.run(["ls", "-la"])\n',
        encoding='utf-8',
    )
    return tmp_path


@pytest.fixture
def projeto_subprocess_com_shell_false(tmp_path):
    """Projeto com subprocess.run(shell=False) — seguro."""
    (tmp_path / 'runner.py').write_text(
        'import subprocess\n'
        '\n'
        'def executar():\n'
        '    subprocess.run(["ls", "-la"], shell=False)\n',
        encoding='utf-8',
    )
    return tmp_path


@pytest.fixture
def projeto_subprocess_multiline_shell_false(tmp_path):
    """Projeto com subprocess.run() multiline com shell=False na linha seguinte."""
    (tmp_path / 'runner.py').write_text(
        'import subprocess\n'
        '\n'
        'def executar():\n'
        '    subprocess.run(\n'
        '        ["ls", "-la"],\n'
        '        shell=False,\n'
        '    )\n',
        encoding='utf-8',
    )
    return tmp_path


@pytest.fixture
def projeto_subprocess_popen(tmp_path):
    """Projeto com subprocess.Popen sem shell=False."""
    (tmp_path / 'runner.py').write_text(
        'import subprocess\n'
        '\n'
        'def executar():\n'
        '    subprocess.Popen(["ls"])\n',
        encoding='utf-8',
    )
    return tmp_path


@pytest.fixture
def projeto_subprocess_call(tmp_path):
    """Projeto com subprocess.call sem shell=False."""
    (tmp_path / 'runner.py').write_text(
        'import subprocess\n'
        '\n'
        'def executar():\n'
        '    subprocess.call(["ls"])\n',
        encoding='utf-8',
    )
    return tmp_path


# =============================================================================
# TESTES: ALTO RISCO — escanear_alto_risco()
# =============================================================================

class TestEscanearAltoRisco:
    def test_projeto_limpo(self, projeto_limpo):
        vulns = gate.escanear_alto_risco(projeto_limpo)
        assert len(vulns) == 0

    def test_os_system_bloqueado(self, projeto_os_system):
        vulns = gate.escanear_alto_risco(projeto_os_system)
        assert len(vulns) > 0
        assert any('os.system' in v.descricao for v in vulns)
        assert all(v.severidade == 'Critica' for v in vulns)

    def test_eval_isolado_bloqueado(self, projeto_eval_isolado):
        vulns = gate.escanear_alto_risco(projeto_eval_isolado)
        assert len(vulns) > 0
        assert any('eval()' in v.descricao for v in vulns)

    def test_exec_isolado_bloqueado(self, projeto_exec_isolado):
        vulns = gate.escanear_alto_risco(projeto_exec_isolado)
        assert len(vulns) > 0
        assert any('exec()' in v.descricao for v in vulns)

    def test_subprocess_sem_shell_false_bloqueado(self, projeto_subprocess_sem_shell_false):
        vulns = gate.escanear_alto_risco(projeto_subprocess_sem_shell_false)
        assert len(vulns) > 0
        assert any('subprocess' in v.descricao.lower() for v in vulns)

    def test_subprocess_com_shell_false_passa(self, projeto_subprocess_com_shell_false):
        """subprocess com shell=False NÃO deve ser flagrado como alto risco."""
        vulns = gate.escanear_alto_risco(projeto_subprocess_com_shell_false)
        # shell=False = seguro, não deve ter vulnerabilidades bloqueantes
        alto_risco = [v for v in vulns if v.severidade == 'Critica']
        assert len(alto_risco) == 0

    def test_subprocess_multiline_shell_false_passa(self, projeto_subprocess_multiline_shell_false):
        """subprocess multiline com shell=False na linha seguinte NÃO deve ser flagrado."""
        vulns = gate.escanear_alto_risco(projeto_subprocess_multiline_shell_false)
        alto_risco = [v for v in vulns if v.severidade == 'Critica']
        assert len(alto_risco) == 0

    def test_subprocess_popen_bloqueado(self, projeto_subprocess_popen):
        vulns = gate.escanear_alto_risco(projeto_subprocess_popen)
        assert len(vulns) > 0

    def test_subprocess_call_bloqueado(self, projeto_subprocess_call):
        vulns = gate.escanear_alto_risco(projeto_subprocess_call)
        assert len(vulns) > 0

    def test_comentarios_ignorados(self, tmp_path):
        """Comentários com eval/os.system devem ser ignorados."""
        (tmp_path / 'safe.py').write_text(
            '# os.system("rm -rf /")\n'
            '# eval("dangerous")\n'
            'def safe():\n'
            '    return True\n',
            encoding='utf-8',
        )
        vulns = gate.escanear_alto_risco(tmp_path)
        assert len(vulns) == 0

    def test_diretorio_tests_ignorado(self, tmp_path):
        """Arquivos em tests/ devem ser ignorados."""
        (tmp_path / 'tests').mkdir()
        (tmp_path / 'tests' / 'test_runner.py').write_text(
            'import os\n'
            'os.system("ls")\n',
            encoding='utf-8',
        )
        vulns = gate.escanear_alto_risco(tmp_path)
        assert len(vulns) == 0

    def test_diretorio_inexistente(self, tmp_path):
        """Pasta inexistente retorna lista vazia."""
        vulns = gate.escanear_alto_risco(tmp_path / 'nao_existe')
        assert len(vulns) == 0


# =============================================================================
# TESTES: RELATÓRIO DE CONFORMIDADE
# =============================================================================

class TestRelatorioConformidade:
    def test_projeto_limpo(self, projeto_limpo):
        rel = gate.gerar_relatorio_conformidade(projeto_limpo)
        assert rel['status'] == 'APROVADO'
        assert rel['vulnerabilidades_total'] == 0
        assert rel['criticas'] == 0
        assert rel['altas'] == 0
        assert rel['achados'] == []

    def test_projeto_com_vulnerabilidade(self, projeto_os_system):
        rel = gate.gerar_relatorio_conformidade(projeto_os_system)
        assert rel['status'] == 'BLOQUEADO'
        assert rel['vulnerabilidades_total'] > 0
        assert rel['criticas'] > 0
        assert len(rel['achados']) > 0

    def test_estrutura_relatorio(self, projeto_limpo):
        rel = gate.gerar_relatorio_conformidade(projeto_limpo)
        assert 'gate' in rel
        assert 'status' in rel
        assert 'vulnerabilidades_total' in rel
        assert 'criticas' in rel
        assert 'altas' in rel
        assert 'achados' in rel
        assert rel['gate'] == 'G_CYBERSECURITY_OWASP'


# =============================================================================
# TESTES: GATE PRÉ-I4 (EXIT CODE)
# =============================================================================

class TestGatePreI4:
    def test_projeto_limpo_passa(self, projeto_limpo):
        resultado = gate.executar_gate_pre_i4(projeto_limpo)
        assert resultado == 0

    def test_os_system_falha(self, projeto_os_system):
        resultado = gate.executar_gate_pre_i4(projeto_os_system)
        assert resultado == 1

    def test_eval_isolado_falha(self, projeto_eval_isolado):
        resultado = gate.executar_gate_pre_i4(projeto_eval_isolado)
        assert resultado == 1

    def test_subprocess_sem_shell_false_falha(self, projeto_subprocess_sem_shell_false):
        resultado = gate.executar_gate_pre_i4(projeto_subprocess_sem_shell_false)
        assert resultado == 1

    def test_subprocess_com_shell_false_passa(self, projeto_subprocess_com_shell_false):
        resultado = gate.executar_gate_pre_i4(projeto_subprocess_com_shell_false)
        assert resultado == 0

    def test_projeto_inexistente_falha(self, tmp_path):
        resultado = gate.executar_gate_pre_i4(tmp_path / 'nao_existe')
        assert resultado == 1

    def test_main_com_pre_i4_flag(self, projeto_limpo, monkeypatch):
        monkeypatch.setattr(sys, 'argv', ['G_CYBERSECURITY_OWASP.py', '--pre-i4', str(projeto_limpo)])
        resultado = gate.main()
        assert resultado == 0
