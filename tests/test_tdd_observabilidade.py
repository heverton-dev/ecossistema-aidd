import json
import sys
import time
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent

def test_tdd_observabilidade_grava_metricas(tmp_path):
    sys.path.insert(0, str(ROOT / ".agents" / "skills" / "aidd-tdd" / "scripts"))
    import observabilidade

    rastreador = observabilidade.RastreadorTdd(seam="auth_seam")
    rastreador.iniciar_fase("RED")
    time.sleep(0.01)
    rastreador.finalizar_fase("RED")

    rastreador.registrar_metrica("total_assercoes", 5)
    
    arquivo_metricas = tmp_path / "metricas.json"
    rastreador.salvar_metricas(arquivo_metricas)

    assert arquivo_metricas.exists()
    with open(arquivo_metricas, "r", encoding="utf-8") as f:
        dados = json.load(f)

    assert dados["seam"] == "auth_seam"
    assert "RED" in dados["duracao_fases"]
    assert dados["duracao_fases"]["RED"] >= 0.009
    assert dados["metricas_customizadas"]["total_assercoes"] == 5
