from pathlib import Path
import pytest
import os
import tempfile
import json
import sys

sys.path.insert(0, str(Path("scripts").resolve()))
import estado_execucao

def test_schema_estado_execucao_existe():
    schema_path = Path("modulos/04-nucleo-compartilhado/contracts/estado-execucao.schema.json")
    assert schema_path.exists(), "Schema estado-execucao.schema.json nao existe"
    data = json.loads(schema_path.read_text(encoding="utf-8"))
    assert data.get("title") or data.get("description")
    assert "properties" in data
    assert "run_id" in data["properties"]
    assert "pipeline" in data["properties"]
    assert "etapa_atual" in data["properties"]

def test_emissor_estado_execucao_grava_corretamente():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["AIDD_HOME"] = tmpdir
        try:
            with estado_execucao.Execucao.abrir(pipeline="pure", chave="teste-app", titulo="App Teste") as ex:
                ex.etapa("fundacao", "agente", harness="claude", modelo="haiku")
                run_id = ex.run_id
                
            estado_file = Path(tmpdir) / "execucoes" / run_id / "estado.json"
            assert estado_file.exists(), "estado.json nao foi gravado"
            conteudo = json.loads(estado_file.read_text(encoding="utf-8"))
            assert conteudo["pipeline"] == "pure"
            assert conteudo["status"] == "concluido"
            assert conteudo["etapa_atual"] == "fundacao"
            assert len(conteudo["etapas"]) >= 1
            assert conteudo["etapas"][0]["id"] == "fundacao"
            assert conteudo["etapas"][0]["status"] == "agente"
        finally:
            os.environ.pop("AIDD_HOME", None)

def test_desativacao_via_aidd_quadro_zero():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["AIDD_HOME"] = tmpdir
        os.environ["AIDD_QUADRO"] = "0"
        try:
            with estado_execucao.Execucao.abrir(pipeline="pure", chave="teste-off", titulo="App Off") as ex:
                ex.etapa("fundacao", "concluida")
                run_id = ex.run_id
            estado_file = Path(tmpdir) / "execucoes" / run_id / "estado.json"
            assert not estado_file.exists(), "Nao deveria gravar com AIDD_QUADRO=0"
        finally:
            os.environ.pop("AIDD_HOME", None)
            os.environ.pop("AIDD_QUADRO", None)

def test_captura_de_falha_por_excecao():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["AIDD_HOME"] = tmpdir
        try:
            with pytest.raises(RuntimeError):
                with estado_execucao.Execucao.abrir(pipeline="pure", chave="teste-fail", titulo="App Fail") as ex:
                    run_id = ex.run_id
                    raise RuntimeError("Falha simulada intencional")
                    
            estado_file = Path(tmpdir) / "execucoes" / run_id / "estado.json"
            assert estado_file.exists()
            conteudo = json.loads(estado_file.read_text(encoding="utf-8"))
            assert conteudo["status"] == "falhou"
            assert conteudo["exit_code"] == 1
            assert "Falha simulada intencional" in conteudo["parada"]["motivo"]
        finally:
            os.environ.pop("AIDD_HOME", None)
