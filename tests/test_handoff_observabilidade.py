# -*- coding: utf-8 -*-
import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent

def carregar_observabilidade():
    obs_path = ROOT / "componentes" / "compartilhado" / "skills" / "aidd-handoff" / "scripts" / "observabilidade.py"
    spec = importlib.util.spec_from_file_location("aidd_handoff_observabilidade", str(obs_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_rastreador_handoff_computa_metricas():
    obs = carregar_observabilidade()
    rastreador = obs.RastreadorHandoff()

    texto = """# Handoff
## Initial Goal
Meta
## Completed Work
Trabalho
## Quality Gate State
OK
## Next Actions
Acoes
## Discovered Invariants & Gotchas
Invariantes
"""
    metricas = rastreador.analisar_texto(texto)
    assert metricas["total_linhas"] > 0
    assert metricas["total_secoes"] == 5
    assert metricas["estimativa_tokens"] > 0
    assert "timestamp" in metricas
