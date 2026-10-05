import json
import pytest
from pathlib import Path

def test_manifesto_vsa_handoff_gerado_e_valido(tmp_path):
    from scripts.handoff_vsa import gerar_e_assinar_manifesto_handoff

    destino = tmp_path / "MANIFESTO-VSA-MODULOS.json"
    manifesto = gerar_e_assinar_manifesto_handoff(destino)

    assert destino.exists()
    conteudo = json.loads(destino.read_text(encoding="utf-8"))

    assert "versao" in conteudo
    assert "status_dimensoes_15d" in conteudo
    assert "slices" in conteudo
    assert "assinatura_sha256" in conteudo
    assert len(conteudo["status_dimensoes_15d"]) == 15
    assert len(conteudo["slices"]) == 4

def test_manifesto_vsa_rejeita_adulteracao(tmp_path):
    from scripts.handoff_vsa import gerar_e_assinar_manifesto_handoff, validar_assinatura_manifesto

    destino = tmp_path / "MANIFESTO-VSA-MODULOS.json"
    gerar_e_assinar_manifesto_handoff(destino)

    assert validar_assinatura_manifesto(destino) is True

    # Adulterar o conteúdo
    dados = json.loads(destino.read_text(encoding="utf-8"))
    dados["versao"] = "99.9"
    destino.write_text(json.dumps(dados), encoding="utf-8")

    assert validar_assinatura_manifesto(destino) is False
