import json
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent

def test_tdd_handoff_geracao_e_assinatura_hmac(tmp_path):
    sys.path.insert(0, str(ROOT / ".agents" / "skills" / "aidd-tdd" / "scripts"))
    import handoff

    sessao_file = tmp_path / "sessao.json"
    dados = {
        "alvo": "src/module.py",
        "seam": "feature_seam",
        "fase_atual": "GREEN",
        "testes": ["tests/test_feature.py"]
    }
    sessao_file.write_text(json.dumps(dados), encoding="utf-8")

    handoff_file = tmp_path / "handoff-tdd.json"
    sucesso = handoff.gerar_handoff(sessao_file, handoff_file, chave="chave_secreta_teste")
    assert sucesso is True
    assert handoff_file.exists()

    valido = handoff.verificar_handoff(handoff_file, chave="chave_secreta_teste")
    assert valido is True

    # Se adulterar conteudo, HMAC deve falhar
    with open(handoff_file, "r", encoding="utf-8") as f:
        adulterado = json.load(f)
    adulterado["payload"]["alvo"] = "src/hack.py"
    handoff_file.write_text(json.dumps(adulterado), encoding="utf-8")

    valido_adulterado = handoff.verificar_handoff(handoff_file, chave="chave_secreta_teste")
    assert valido_adulterado is False
