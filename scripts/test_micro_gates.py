# -*- coding: utf-8 -*-
"""
Testes unitários determinísticos do seletor e dispatcher de micro-gates via git diff.
"""
from scripts.micro_gates import mapear_fatias_afetadas


def test_mapear_subfatia_forge():
    arquivos = ["modulos/01-governanca-e-qualidade/core/aidd-forge/main.py", "README.md"]
    assert mapear_fatias_afetadas(arquivos) == {"forge"}


def test_mapear_subfatias_pure_e_master():
    arquivos = [
        "modulos/02-triade-motores/fluxo-01-pure/core/aidd-pure/engine.py",
        "modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/server.py",
    ]
    assert mapear_fatias_afetadas(arquivos) == {"pure", "master"}


def test_mapear_fatias_core_cli():
    arquivos = ["ecossistema.py", "scripts/exit_codes.py"]
    assert mapear_fatias_afetadas(arquivos) == {"core-cli"}


def test_mapear_fatias_sem_impacto():
    arquivos = ["docs/protocolos/LEI-13.md", "assets/logo.png"]
    assert mapear_fatias_afetadas(arquivos) == set()
