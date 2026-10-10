from pathlib import Path
import json
import pytest

CONTRATO_PATH = Path("modulos/04-nucleo-compartilhado/contracts/PIPELINES.json")

def test_contrato_pipelines_existe_e_valido():
    assert CONTRATO_PATH.exists(), f"Contrato {CONTRATO_PATH} nao existe"
    data = json.loads(CONTRATO_PATH.read_text(encoding="utf-8"))
    
    assert "schema" in data
    assert "pipelines" in data
    pipelines = data["pipelines"]
    assert len(pipelines) == 12, f"Esperado 12 pipelines, encontrado {len(pipelines)}"
    
    ids_obrigatorios = {
        "pure", "open", "freedom",
        "auditoria-4f", "evolucao", "melhoria-plan-orchestrate",
        "aidd-ingest", "aidd-ops", "aidd-pipeline",
        "bateria-gates", "despacho-vsa", "run-plan"
    }
    
    ids_encontrados = {p["id"] for p in pipelines}
    assert ids_obrigatorios == ids_encontrados, f"Divergencia de pipelines: {ids_obrigatorios ^ ids_encontrados}"
    
    for p in pipelines:
        assert "id" in p and p["id"]
        assert "nome" in p and p["nome"]
        assert "comando" in p and p["comando"]
        assert "origem_estado" in p and p["origem_estado"]
        assert "etapas" in p and isinstance(p["etapas"], list)
        assert len(p["etapas"]) > 0, f"Pipeline {p['id']} deve ter ao menos 1 etapa"
        for etapa in p["etapas"]:
            assert "id" in etapa and etapa["id"]
            assert "titulo" in etapa and etapa["titulo"]
