import json
import os
import tempfile
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path("scripts").resolve()))
import quadro_alertas
import estado_execucao

def test_detector_alertas_pid_morto():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["AIDD_HOME"] = tmpdir
        try:
            with estado_execucao.Execucao.abrir(pipeline="pure", chave="alvo-1", titulo="Alvo 1") as ex:
                ex.pid = 9999999  # PID fictício morto
                run_id = ex.run_id
                
            # Forçar PID morto e status executando
            estado_path = Path(tmpdir) / "execucoes" / run_id / "estado.json"
            dados = json.loads(estado_path.read_text(encoding="utf-8"))
            dados["status"] = "executando"
            dados["processo"]["pid"] = 9999999
            estado_path.write_text(json.dumps(dados), encoding="utf-8")
            
            alertas = quadro_alertas.verificar_alertas(raiz_aidd=Path(tmpdir))
            tipos = [a["tipo"] for a in alertas]
            assert "pid_morto" in tipos
        finally:
            os.environ.pop("AIDD_HOME", None)
