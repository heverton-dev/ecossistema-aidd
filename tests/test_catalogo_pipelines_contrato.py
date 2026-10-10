from pathlib import Path
import pytest
import sys

sys.path.insert(0, str(Path("scripts").resolve()))
import catalogo_pecas

def test_coletar_pipelines_le_contrato():
    assert hasattr(catalogo_pecas, "coletar_pipelines"), "catalogo_pecas nao tem funcao coletar_pipelines"
    pipelines = catalogo_pecas.coletar_pipelines()
    assert isinstance(pipelines, list)
    assert len(pipelines) == 12
    ids = {p["id"] for p in pipelines}
    assert "pure" in ids
    assert "auditoria-4f" in ids
    assert "evolucao" in ids
    assert "aidd-ops" in ids

def test_catalogo_gerado_inclui_pipelines():
    cat = catalogo_pecas.gerar(com_encaixe=False)
    assert "pipelines" in cat
    assert len(cat["pipelines"]) == 12
