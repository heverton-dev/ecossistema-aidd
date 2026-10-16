# -*- coding: utf-8 -*-
"""
Achado do /pure real (16/10/2026): o prompt da Fase 8 manda importar direto
(`from persistencia_nucleo import ...`, arquivo em src/infrastructure/) e o
sandbox da Fase 8 poe src/ e cada camada no PYTHONPATH, mas o `pytest.ini`
gerado so listava `src`. Resultado: a suite passava na Fase 8 e reprovava no
G_TESTES_REAIS do despacho VSA (`ModuleNotFoundError: persistencia_nucleo`).
"""

import subprocess
import sys


def test_pytest_ini_gerado_importa_modulos_das_camadas(criador_05, tmp_path):
    criador_05.CriadorProjetoFase5(tmp_path)._criar_pytest_ini()
    (tmp_path / 'src' / 'infrastructure').mkdir(parents=True)
    (tmp_path / 'src' / 'infrastructure' / 'persistencia_x.py').write_text('VALOR = 7\n', encoding='utf-8')
    (tmp_path / 'tests').mkdir()
    (tmp_path / 'tests' / 'test_x.py').write_text(
        'from persistencia_x import VALOR\n\ndef test_x():\n    assert VALOR == 7\n', encoding='utf-8')
    proc = subprocess.run(
        [sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider'],
        cwd=tmp_path, capture_output=True, text=True, encoding='utf-8', errors='replace')
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_pytest_ini_lista_src_e_camadas_conhecidas(criador_05, tmp_path):
    criador_05.CriadorProjetoFase5(tmp_path)._criar_pytest_ini()
    conteudo = (tmp_path / 'pytest.ini').read_text(encoding='utf-8')
    for caminho in ('src', 'src/infrastructure', 'src/domain', 'src/application', 'src/interfaces'):
        assert caminho in conteudo.split('pythonpath =')[1].split('\n')[0].split(), caminho
