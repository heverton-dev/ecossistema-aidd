# -*- coding: utf-8 -*-
"""
Testes do Repomix Runner (NIH #22) — Empacotamento de Contexto para LLM.
Testes herméticos (subprocess mockado) e de integração real contra o repomix instalado.
"""

import sys
import shutil
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

CORE_DIR = Path(__file__).parent.parent / 'scripts' / 'core'
PHASES_DIR = Path(__file__).parent.parent / 'scripts' / 'phases'
sys.path.insert(0, str(CORE_DIR))
sys.path.insert(0, str(PHASES_DIR))

import repomix_runner


def test_repomix_disponivel_retorna_bool():
    """Valida que repomix_disponivel retorna booleano."""
    res = repomix_runner.repomix_disponivel()
    assert isinstance(res, bool)


def test_obter_comando_repomix():
    """Valida retorno do comando repomix."""
    cmd = repomix_runner.obter_comando_repomix()
    if repomix_runner.repomix_disponivel():
        assert cmd is not None
        assert isinstance(cmd, list)
        assert len(cmd) >= 1
    else:
        assert cmd is None


def test_estimar_tokens():
    """Valida cálculo determinístico de tokens."""
    assert repomix_runner.estimar_tokens("") == 0
    assert repomix_runner.estimar_tokens("abcd") == 1
    assert repomix_runner.estimar_tokens("a" * 100) == 25


def test_empacotar_metodo_antigo_caseiro(tmp_path):
    """Valida empacotamento artesanal antigo concatenando arquivos."""
    src = tmp_path / 'src'
    src.mkdir()
    (src / 'app.py').write_text("print('hello')", encoding='utf-8')
    (src / 'calc.py').write_text("def add(a, b): return a + b", encoding='utf-8')

    res = repomix_runner.empacotar_metodo_antigo_caseiro(tmp_path)
    assert res['status'] == 'SUCESSO'
    assert res['total_arquivos'] == 2
    assert "MODULO: src/app.py" in res['conteudo'] or "MODULO: src\\app.py" in res['conteudo']
    assert "def add(a, b): return a + b" in res['conteudo']
    assert res['tokens_estimados'] > 0
    assert res['ferramenta'] == 'metodo_antigo_caseiro'


def test_empacotar_repositorio_diretorio_inexistente(tmp_path):
    """Valida tratamento de erro para pasta inexistente."""
    fake = tmp_path / 'nao_existe'
    res = repomix_runner.empacotar_repositorio(fake)
    assert res['status'] == 'FALHOU'
    assert 'não encontrado' in res['erro'].lower() or 'nao encontrado' in res['erro'].lower()


def test_empacotar_repositorio_sem_repomix_fallback(tmp_path, monkeypatch):
    """Valida fallback limpo quando repomix não está instalado."""
    src = tmp_path / 'src'
    src.mkdir()
    (src / 'main.py').write_text("print('test')", encoding='utf-8')

    monkeypatch.setattr(repomix_runner, 'obter_comando_repomix', lambda: None)
    out_file = tmp_path / 'out.txt'
    res = repomix_runner.empacotar_repositorio(tmp_path, saida_arquivo=out_file)

    assert res['status'] == 'SUCESSO'
    assert res['ferramenta'] == 'fallback_caseiro_sem_repomix'
    assert out_file.exists()
    assert "print('test')" in res['conteudo']


def test_empacotar_repositorio_hermetico_mockado(tmp_path, monkeypatch):
    """Valida fluxo de execução com subprocess mockado hermeticamente."""
    src = tmp_path / 'src'
    src.mkdir()
    (src / 'main.py').write_text("print('test')", encoding='utf-8')
    out_file = tmp_path / 'repomix-output.xml'

    def mock_run(args, **kwargs):
        out_file.write_text("<files><file path='src/main.py'>print('test')</file></files>", encoding='utf-8')
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(repomix_runner, 'obter_comando_repomix', lambda: ['fake-repomix'])
    monkeypatch.setattr(subprocess, 'run', mock_run)

    res = repomix_runner.empacotar_repositorio(
        tmp_path,
        saida_arquivo=out_file,
        formato='xml',
        remove_comments=True
    )
    assert res['status'] == 'SUCESSO'
    assert res['ferramenta'] == 'repomix'
    assert "<files>" in res['conteudo']
    assert res['tokens_estimados'] > 0


def test_empacotar_repositorio_erro_subprocess_fallback(tmp_path, monkeypatch):
    """Valida que falha do subprocess aciona fallback seguro sem estourar 500."""
    src = tmp_path / 'src'
    src.mkdir()
    (src / 'main.py').write_text("x = 10", encoding='utf-8')

    def mock_run_fail(args, **kwargs):
        return subprocess.CompletedProcess(args=args, returncode=1, stdout="", stderr="Repomix crash")

    monkeypatch.setattr(repomix_runner, 'obter_comando_repomix', lambda: ['fake-repomix'])
    monkeypatch.setattr(subprocess, 'run', mock_run_fail)

    res = repomix_runner.empacotar_repositorio(tmp_path)
    assert res['status'] == 'SUCESSO'
    assert res['ferramenta'] == 'fallback_repomix_returncode'
    assert "x = 10" in res['conteudo']


@pytest.mark.skipif(not repomix_runner.repomix_disponivel(), reason="Repomix não instalado no host")
def test_empacotar_repositorio_integracao_real(tmp_path):
    """INTEGRAÇÃO REAL: executa repomix de verdade e valida saída XML estruturada."""
    src = tmp_path / 'src'
    src.mkdir()
    (src / 'servico.py').write_text(
        "# Servico principal\n# Linha comentada\n\ndef executar_tarefa():\n    return 'OK'\n",
        encoding='utf-8'
    )
    saida = tmp_path / 'contexto.xml'

    res = repomix_runner.empacotar_repositorio(
        tmp_path,
        saida_arquivo=saida,
        formato='xml',
        remove_comments=True,
        remove_empty_lines=True,
        no_file_summary=True,
        includes=['src/**/*.py']
    )

    assert res['status'] == 'SUCESSO'
    assert res['ferramenta'] == 'repomix'
    assert saida.exists()
    conteudo = saida.read_text(encoding='utf-8')
    assert "<directory_structure>" in conteudo
    assert "servico.py" in conteudo
    assert "<file path=" in conteudo
    assert "def executar_tarefa():" in conteudo


@pytest.mark.skipif(not repomix_runner.repomix_disponivel(), reason="Repomix não instalado no host")
def test_comparar_empacotamento_tokens_economia_real(tmp_path):
    """INTEGRAÇÃO REAL: compara tokens entre método caseiro e Repomix com comentários removidos."""
    src = tmp_path / 'src'
    src.mkdir()
    (src / 'mod_a.py').write_text(
        "# ==========================================\n"
        "# Modulo A com comentarios extensos\n"
        "# Autor: Dev\n"
        "# ==========================================\n\n\n"
        "def funcao_a():\n"
        "    # comentario interno\n"
        "    return 100\n",
        encoding='utf-8'
    )
    (src / 'mod_b.py').write_text(
        "# Modulo B\n\ndef funcao_b():\n    return 200\n",
        encoding='utf-8'
    )

    comp = repomix_runner.comparar_empacotamento_tokens(tmp_path, includes=['src/**/*.py'])

    assert comp['metodo_antigo']['tokens'] > 0
    assert comp['repomix_padrao']['tokens'] > 0
    assert comp['repomix_otimizado']['tokens'] > 0
    assert comp['repomix_otimizado']['tokens'] <= comp['metodo_antigo']['tokens']
    assert comp['economia_tokens'] >= 0
    assert "Comparacao de Empacotamento de Contexto" in comp['relatorio_texto']


def test_implementador_fase8_contexto_repositorio(tmp_path):
    """Valida chamada de empacotamento no ImplementadorFase8."""
    from importlib import import_module
    mod8 = import_module('08_implementador')
    ImplementadorFase8 = mod8.ImplementadorFase8

    src = tmp_path / 'src'
    src.mkdir()
    (src / 'core.py').write_text("def core(): pass\n", encoding='utf-8')

    impl = ImplementadorFase8(tmp_path)
    res = impl.empacotar_contexto_repositorio()
    assert res is not None
    assert res['status'] == 'SUCESSO'
    assert (tmp_path / '.aidd' / 'cache' / 'contexto_repo.xml').exists()
