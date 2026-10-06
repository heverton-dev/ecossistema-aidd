# -*- coding: utf-8 -*-
"""
Testes unitários determinísticos do seletor e dispatcher de micro-gates via git diff.
"""
from pathlib import Path
from scripts.micro_gates import mapear_fatias_afetadas, FATIAS_MAPA


def test_mapear_fatias_governanca():
    arquivos = ["modulos/01-governanca-e-qualidade/core/aidd-forge/main.py", "README.md"]
    fatias = mapear_fatias_afetadas(arquivos)
    assert "01-governanca" in fatias
    assert len(fatias) == 1


def test_mapear_fatias_motores_e_plataforma():
    arquivos = [
        "modulos/02-triade-motores/aidd-pure/engine.py",
        "modulos/03-plataforma-e-entrega/aidd-master/server.py",
    ]
    fatias = mapear_fatias_afetadas(arquivos)
    assert "02-motores" in fatias
    assert "03-plataforma" in fatias
    assert len(fatias) == 2


def test_mapear_fatias_core_cli():
    arquivos = ["ecossistema.py", "scripts/exit_codes.py"]
    fatias = mapear_fatias_afetadas(arquivos)
    assert "core-cli" in fatias
    assert len(fatias) == 1


def test_mapear_fatias_sem_impacto():
    arquivos = ["docs/protocolos/LEI-13.md", "assets/logo.png"]
    fatias = mapear_fatias_afetadas(arquivos)
    assert len(fatias) == 0
