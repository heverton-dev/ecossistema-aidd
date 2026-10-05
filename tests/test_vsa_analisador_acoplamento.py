import pytest

def test_analisador_acoplamento_gera_envelope_estrito():
    from scripts.analisador_acoplamento_vsa import analisar_codigo_fonte

    codigo = """
import os
from tools.aidd_master.core import algo
from tools.aidd_pure.engine import roda
"""
    relatorio = analisar_codigo_fonte(codigo, modulo_origem="tools/aidd-forge")

    assert isinstance(relatorio, dict)
    assert "status" in relatorio
    assert "modulo_origem" in relatorio
    assert "total_imports" in relatorio
    assert "imports_externos" in relatorio
    assert "acoplamento_detectado" in relatorio

    # Validação do envelope estrito
    assert relatorio["modulo_origem"] == "tools/aidd-forge"
    assert relatorio["total_imports"] == 3
    assert len(relatorio["imports_externos"]) == 2
    assert "tools.aidd_master.core" in relatorio["imports_externos"]

def test_analisador_acoplamento_rejeita_modulo_invalido():
    from scripts.analisador_acoplamento_vsa import analisar_codigo_fonte

    with pytest.raises(ValueError, match="Envelope estrito: módulo de origem obrigatório"):
        analisar_codigo_fonte("import sys", modulo_origem="")
