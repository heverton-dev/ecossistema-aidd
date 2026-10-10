import json
import os
import tempfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path("scripts").resolve()))
import estado_execucao

def test_transicao_etapas_ao_vivo():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["AIDD_HOME"] = tmpdir
        try:
            with estado_execucao.Execucao.abrir(pipeline="auditoria-4f", chave="teste-4f", titulo="4F Teste") as ex:
                # Transicao Fase 1
                ex.etapa("fase-1", "agente", harness="claude", modelo="haiku")
                assert ex.etapa_atual == "fase-1"
                
                # Fase 1 Concluida com artefato
                ex.etapa("fase-1", "concluida", feito=["laudo emitido"], artefatos=["LAUDO-15D.md"])
                
                # Transicao Fase 2
                ex.etapa("fase-2", "agente", harness="agy", modelo="flash")
                assert ex.etapa_atual == "fase-2"
                
                # Humano
                ex.pedir_humano("Aprovar merge final", "python scripts/orquestrador_4f.py --aprovar")
                assert ex.humano is not None
                assert "Aprovar merge" in ex.humano["motivo"]
                
                run_id = ex.run_id

            # Validar persistencia em disco
            arquivo = Path(tmpdir) / "execucoes" / run_id / "estado.json"
            assert arquivo.exists()
            dados = json.loads(arquivo.read_text(encoding="utf-8"))
            assert len(dados["etapas"]) == 2
            assert dados["etapas"][0]["id"] == "fase-1"
            assert dados["etapas"][0]["status"] == "concluida"
            assert dados["etapas"][0]["artefatos"] == ["LAUDO-15D.md"]
            assert dados["etapas"][1]["id"] == "fase-2"
            assert dados["humano"]["comando"] == "python scripts/orquestrador_4f.py --aprovar"
        finally:
            os.environ.pop("AIDD_HOME", None)
