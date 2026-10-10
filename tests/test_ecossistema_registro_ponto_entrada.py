import os
import subprocess
import tempfile
import json
import sys
from pathlib import Path

def test_ponto_entrada_registra_execucao_pipeline():
    with tempfile.TemporaryDirectory() as tmpdir:
        env = os.environ.copy()
        env["AIDD_HOME"] = tmpdir
        # Chama um comando de pipeline rapido
        res = subprocess.run(
            [sys.executable, "ecossistema.py", "audit", "--help"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env
        )
        assert res.returncode == 0
        
        # Verifica se gravou em execucoes/
        execucoes_dir = Path(tmpdir) / "execucoes"
        assert execucoes_dir.exists(), "Diretorio execucoes/ nao foi criado"
        runs = list(execucoes_dir.glob("*/estado.json"))
        assert len(runs) >= 1, "Nenhum estado.json gravado"
        dados = json.loads(runs[0].read_text(encoding="utf-8"))
        assert dados["pipeline"] == "bateria-gates"
        assert dados["status"] == "concluido"
