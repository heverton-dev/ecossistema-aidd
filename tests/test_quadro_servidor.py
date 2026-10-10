import json
import os
import tempfile
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path("scripts").resolve()))
sys.path.insert(0, str(Path("scripts/quadro").resolve()))

def test_quadro_leitor_coleta_execucoes():
    import quadro_leitor
    import estado_execucao
    
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["AIDD_HOME"] = tmpdir
        try:
            with estado_execucao.Execucao.abrir(pipeline="pure", chave="proj-a", titulo="Projeto A") as ex:
                ex.etapa("fundacao", "concluida")
                run_id = ex.run_id
                
            leitor = quadro_leitor.QuadroLeitor(raiz_aidd=Path(tmpdir))
            execucoes = leitor.listar_execucoes()
            assert len(execucoes) == 1
            assert execucoes[0]["run_id"] == run_id
            assert execucoes[0]["pipeline"] == "pure"
            
            resumo = leitor.resumo_pipelines()
            assert "pure" in resumo
            assert resumo["pure"]["total"] == 1
        finally:
            os.environ.pop("AIDD_HOME", None)

def test_quadro_api_rotas():
    import quadro_servidor
    import estado_execucao
    
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["AIDD_HOME"] = tmpdir
        try:
            with estado_execucao.Execucao.abrir(pipeline="bateria-gates", chave="gate-run", titulo="Bateria Gates") as ex:
                ex.etapa("execucao-portoes", "agente")
                run_id = ex.run_id
                
            app = quadro_servidor.QuadroApp(raiz_aidd=Path(tmpdir))
            
            # Rota /api/pipelines
            status, headers, body = app.tratar_requisicao("/api/pipelines")
            assert status == 200
            dados = json.loads(body.decode("utf-8"))
            assert "pipelines" in dados
            assert "bateria-gates" in dados["pipelines"]
            
            # Rota /api/pipeline/bateria-gates
            status, headers, body = app.tratar_requisicao("/api/pipeline/bateria-gates")
            assert status == 200
            dados = json.loads(body.decode("utf-8"))
            assert dados["id"] == "bateria-gates"
            assert len(dados["execucoes"]) == 1
            
            # Rota /api/execucao/<run_id>
            status, headers, body = app.tratar_requisicao(f"/api/execucao/{run_id}")
            assert status == 200
            dados = json.loads(body.decode("utf-8"))
            assert dados["run_id"] == run_id
            
            # Rota 404 para desconhecido
            status, _, _ = app.tratar_requisicao("/api/execucao/inexistente")
            assert status == 404
        finally:
            os.environ.pop("AIDD_HOME", None)
