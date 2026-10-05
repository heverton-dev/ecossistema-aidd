import json
import pytest
from pathlib import Path

def test_telemetria_observabilidade_persiste_relatorio(tmp_path):
    from scripts.observabilidade_vsa import GravadorTelemetriaVSA

    destino = tmp_path / "telemetria_vsa.json"
    telemetria = GravadorTelemetriaVSA(arquivo_saida=destino)

    telemetria.iniciar()
    telemetria.registrar_slice("01-governanca-e-qualidade", tokens=120)
    telemetria.registrar_slice("02-triade-motores", tokens=340)
    telemetria.finalizar()

    assert destino.exists()
    dados = json.loads(destino.read_text(encoding="utf-8"))

    assert dados["total_slices_verificados"] == 2
    assert dados["orcamento_tokens_consumido"] == 460
    assert "duracao_segundos" in dados
    assert len(dados["slices"]) == 2

def test_telemetria_falha_se_nao_iniciada(tmp_path):
    from scripts.observabilidade_vsa import GravadorTelemetriaVSA

    destino = tmp_path / "telemetria_vsa.json"
    telemetria = GravadorTelemetriaVSA(arquivo_saida=destino)

    with pytest.raises(RuntimeError, match="Telemetria não iniciada"):
        telemetria.registrar_slice("01-governanca", tokens=50)
