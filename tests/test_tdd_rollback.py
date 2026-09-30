import json
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent

def test_tdd_rollback_reverte_estado(tmp_path):
    sys.path.insert(0, str(ROOT / ".agents" / "skills" / "aidd-tdd" / "scripts"))
    import rollback

    sessao_file = tmp_path / "sessao.json"
    dados = {
        "alvo": "src/auth.py",
        "seam": "login",
        "fase_atual": "REFACTOR",
        "historico_fases": [
            {"fase": "SEAM_ACORDADO"},
            {"fase": "RED"},
            {"fase": "GREEN"},
            {"fase": "REFACTOR"}
        ]
    }
    sessao_file.write_text(json.dumps(dados), encoding="utf-8")

    res = rollback.reverter_para_ultimo_green(sessao_file)
    assert res is True

    with open(sessao_file, "r", encoding="utf-8") as f:
        atualizado = json.load(f)
    assert atualizado["fase_atual"] == "GREEN"
    assert atualizado["historico_fases"][-1]["fase"] == "ROLLBACK_PARA_GREEN"
