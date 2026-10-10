from pathlib import Path
import pytest
import sys

sys.path.insert(0, str(Path("scripts").resolve()))
import catalogo_pecas

def test_detector_vivo_pipelines_valida_conformidade_atual():
    assert hasattr(catalogo_pecas, "verificar_contrato_vivo_pipelines"), "Falta verificar_contrato_vivo_pipelines"
    divergencias = catalogo_pecas.verificar_contrato_vivo_pipelines()
    assert divergencias == [], f"Divergencias encontradas no estado atual: {divergencias}"

def test_detector_vivo_morde_se_pipeline_faltar_no_contrato():
    assert hasattr(catalogo_pecas, "verificar_contrato_vivo_pipelines")
    # Simula lista de pipelines conhecidos com um pipeline extra ausente no contrato
    divergencias = catalogo_pecas.verificar_contrato_vivo_pipelines(pipelines_extras=["pipeline-sintetico-novo"])
    assert len(divergencias) > 0
    assert "pipeline-sintetico-novo" in divergencias[0]
