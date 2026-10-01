# -*- coding: utf-8 -*-
"""
Testes para G_INTEGRACAO_CROSS_SCRIPT (Gate I3).

Cenários cobertos:
  1. Projeto sem módulos Python → passa (nada a validar)
  2. Módulo com syntax válida → passa I1
  3. Módulo com syntax inválida → falha I1
  4. Import cruzado válido → passa I2
  5. Import cruzado com função inexistente → falha I2
  6. Schema JSON válido → passa I3
  7. Schema JSON inválido → falha I3
  8. Tipos compatíveis → passa I4
  9. Gate completo em projeto real → integração
"""

import sys
import json
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / 'scripts'
sys.path.insert(0, str(_SCRIPTS_DIR / 'gates'))

import G_INTEGRACAO_CROSS_SCRIPT as gate


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def projeto_vazio(tmp_path):
    """Projeto sem nenhum arquivo Python."""
    return tmp_path


@pytest.fixture
def projeto_modulo_valido(tmp_path):
    """Projeto com um módulo Python válido."""
    modulo = tmp_path / 'servico.py'
    modulo.write_text(
        'def calcular_total(preco, quantidade):\n'
        '    return preco * quantidade\n'
        '\n'
        'class Carrinho:\n'
        '    def adicionar(self, item):\n'
        '        pass\n',
        encoding='utf-8',
    )
    return tmp_path


@pytest.fixture
def projeto_modulo_invalido(tmp_path):
    """Projeto com um módulo Python com syntax inválida."""
    modulo = tmp_path / 'quebrado.py'
    modulo.write_text(
        'def funcao_quebrada(\n'
        '    return 42\n',
        encoding='utf-8',
    )
    return tmp_path


@pytest.fixture
def projeto_imports_cruzados_validos(tmp_path):
    """Projeto com imports cruzados válidos entre módulos."""
    modulo_a = tmp_path / 'modulo_a.py'
    modulo_a.write_text(
        'def funcao_publica():\n'
        '    return 42\n'
        '\n'
        'class MinhaClasse:\n'
        '    def metodo(self):\n'
        '        pass\n',
        encoding='utf-8',
    )
    modulo_b = tmp_path / 'modulo_b.py'
    modulo_b.write_text(
        'from modulo_a import funcao_publica, MinhaClasse\n'
        '\n'
        'def usar_a():\n'
        '    return funcao_publica()\n',
        encoding='utf-8',
    )
    return tmp_path


@pytest.fixture
def projeto_imports_cruzados_invalidos(tmp_path):
    """Projeto com import de função inexistente."""
    modulo_a = tmp_path / 'modulo_a.py'
    modulo_a.write_text(
        'def funcao_real():\n'
        '    return 1\n',
        encoding='utf-8',
    )
    modulo_b = tmp_path / 'modulo_b.py'
    modulo_b.write_text(
        'from modulo_a import funcao_que_nao_existe\n'
        '\n'
        'def usar():\n'
        '    return funcao_que_nao_existe()\n',
        encoding='utf-8',
    )
    return tmp_path


@pytest.fixture
def projeto_com_schema_valido(tmp_path):
    """Projeto com schema JSON válido."""
    modulo = tmp_path / 'app.py'
    modulo.write_text('def main(): pass\n', encoding='utf-8')
    schema = tmp_path / 'schema_usuario.json'
    schema.write_text(
        json.dumps({
            'type': 'object',
            'properties': {
                'nome': {'type': 'string'},
                'idade': {'type': 'integer'},
            },
            'required': ['nome'],
        }),
        encoding='utf-8',
    )
    return tmp_path


@pytest.fixture
def projeto_com_schema_invalido(tmp_path):
    """Projeto com schema JSON inválido."""
    modulo = tmp_path / 'app.py'
    modulo.write_text('def main(): pass\n', encoding='utf-8')
    schema = tmp_path / 'schema_quebrado.json'
    schema.write_text('{invalid json content', encoding='utf-8')
    return tmp_path


# =============================================================================
# TESTES: EXTRAÇÃO DE CONTRATOS
# =============================================================================

class TestExtrairFuncoesPublicas:
    def test_funcoes_simples(self):
        codigo = 'def publica():\n    pass\n\ndef _privada():\n    pass\n'
        funcoes = gate.extrair_funcoes_publicas(codigo)
        nomes = [f['nome'] for f in funcoes]
        assert 'publica' in nomes
        assert '_privada' not in nomes

    def test_funcao_com_args(self):
        codigo = 'def soma(a: int, b: int) -> int:\n    return a + b\n'
        funcoes = gate.extrair_funcoes_publicas(codigo)
        assert len(funcoes) == 1
        assert funcoes[0]['nome'] == 'soma'
        assert len(funcoes[0]['args']) == 2

    def test_syntax_invalida(self):
        funcoes = gate.extrair_funcoes_publicas('def quebrado(\n')
        assert funcoes == []


class TestExtrairClassesPublicas:
    def test_classe_com_metodos(self):
        codigo = (
            'class Servico:\n'
            '    def __init__(self):\n'
            '        pass\n'
            '    def executar(self, dados):\n'
            '        pass\n'
            '    def _interno(self):\n'
            '        pass\n'
        )
        classes = gate.extrair_classes_publicas(codigo)
        assert len(classes) == 1
        assert classes[0]['nome'] == 'Servico'
        nomes_metodos = [m['nome'] for m in classes[0]['metodos']]
        assert 'executar' in nomes_metodos
        assert '_interno' not in nomes_metodos

    def test_classe_privada_ignorada(self):
        codigo = 'class _Interna:\n    def metodo(self): pass\n'
        classes = gate.extrair_classes_publicas(codigo)
        assert len(classes) == 0


# =============================================================================
# TESTES: VALIDAÇÃO I1 (SYNTAX)
# =============================================================================

class TestValidarImportabilidade:
    def test_modulo_valido(self, projeto_modulo_valido):
        arquivos = list(projeto_modulo_valido.glob('*.py'))
        modulos = [(f.stem, f) for f in arquivos]
        resultados = gate.validar_importabilidade(modulos)
        assert all(r.passou for r in resultados)

    def test_modulo_invalido(self, projeto_modulo_invalido):
        arquivos = list(projeto_modulo_invalido.glob('*.py'))
        modulos = [(f.stem, f) for f in arquivos]
        resultados = gate.validar_importabilidade(modulos)
        assert any(not r.passou for r in resultados)


# =============================================================================
# TESTES: VALIDAÇÃO I2 (CONTRATOS)
# =============================================================================

class TestValidarContratos:
    def test_imports_validos(self, projeto_imports_cruzados_validos):
        arquivos = list(projeto_imports_cruzados_validos.glob('*.py'))
        modulos = [(f.stem, f) for f in arquivos]
        resultados = gate.validar_contratos_entre_modulos(modulos)
        assert all(r.passou for r in resultados)

    def test_imports_invalidos(self, projeto_imports_cruzados_invalidos):
        arquivos = list(projeto_imports_cruzados_invalidos.glob('*.py'))
        modulos = [(f.stem, f) for f in arquivos]
        resultados = gate.validar_contratos_entre_modulos(modulos)
        falhas = [r for r in resultados if not r.passou]
        assert len(falhas) > 0
        assert 'funcao_que_nao_existe' in falhas[0].detalhes


# =============================================================================
# TESTES: VALIDAÇÃO I3 (SCHEMAS JSON)
# =============================================================================

class TestValidarSchemas:
    def test_schema_valido(self, projeto_com_schema_valido):
        resultados = gate.validar_schemas_json_compativeis(projeto_com_schema_valido)
        assert all(r.passou for r in resultados)

    def test_schema_invalido(self, projeto_com_schema_invalido):
        resultados = gate.validar_schemas_json_compativeis(projeto_com_schema_invalido)
        assert any(not r.passou for r in resultados)

    def test_sem_schemas(self, projeto_vazio):
        resultados = gate.validar_schemas_json_compativeis(projeto_vazio)
        assert all(r.passou for r in resultados)


# =============================================================================
# TESTES: VALIDAÇÃO I4 (TIPOS)
# =============================================================================

class TestValidarTipos:
    def test_tipos_compativeis(self, projeto_modulo_valido):
        arquivos = list(projeto_modulo_valido.glob('*.py'))
        modulos = [(f.stem, f) for f in arquivos]
        resultados = gate.validar_compatibilidade_tipos(modulos)
        assert all(r.passou for r in resultados)


# =============================================================================
# TESTES: DESCOBERTA DE MÓDULOS
# =============================================================================

class TestDescobrirModulos:
    def test_descobre_py_files(self, projeto_modulo_valido):
        modulos = gate.descobrir_modulos_python(projeto_modulo_valido)
        assert len(modulos) == 1
        assert modulos[0][0] == 'servico'

    def test_exclui_testes(self, tmp_path):
        (tmp_path / 'app.py').write_text('def main(): pass\n', encoding='utf-8')
        (tmp_path / 'test_app.py').write_text('def test_x(): pass\n', encoding='utf-8')
        modulos = gate.descobrir_modulos_python(tmp_path)
        assert len(modulos) == 1
        assert modulos[0][0] == 'app'

    def test_projeto_vazio(self, projeto_vazio):
        modulos = gate.descobrir_modulos_python(projeto_vazio)
        assert len(modulos) == 0


# =============================================================================
# TESTES: GATE COMPLETO (INTEGRAÇÃO)
# =============================================================================

class TestGateCompleto:
    def test_projeto_vazio_passa(self, projeto_vazio):
        resultado = gate.executar_gate(projeto_vazio)
        assert resultado == 0

    def test_projeto_valido_passa(self, projeto_modulo_valido):
        resultado = gate.executar_gate(projeto_modulo_valido)
        assert resultado == 0

    def test_projeto_com_import_invalido_falha(self, projeto_imports_cruzados_invalidos):
        resultado = gate.executar_gate(projeto_imports_cruzados_invalidos)
        assert resultado == 1

    def test_projeto_inexistente_falha(self, tmp_path):
        resultado = gate.executar_gate(tmp_path / 'nao_existe')
        assert resultado == 1

    def test_main_com_args(self, projeto_modulo_valido, monkeypatch):
        monkeypatch.setattr(sys, 'argv', ['G_INTEGRACAO_CROSS_SCRIPT.py', str(projeto_modulo_valido)])
        resultado = gate.main()
        assert resultado == 0
