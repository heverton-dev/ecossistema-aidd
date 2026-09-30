import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent

def test_validador_seams_detecta_stubs_e_assert_trivial(tmp_path):
    sys.path.insert(0, str(ROOT / ".agents" / "skills" / "aidd-tdd" / "scripts"))
    import validador_seams

    # Arquivo com stub vazio
    arq_stub = tmp_path / "test_stub.py"
    arq_stub.write_text("def test_vazio():\n    pass\n", encoding="utf-8")
    
    valido, msgs = validador_seams.validar_arquivo_teste(arq_stub)
    assert valido is False
    assert any("stub vazio" in m.lower() or "pass" in m.lower() for m in msgs)

    # Arquivo com assert trivial
    arq_trivial = tmp_path / "test_trivial.py"
    arq_trivial.write_text("def test_trivial():\n    assert True\n", encoding="utf-8")
    
    valido, msgs = validador_seams.validar_arquivo_teste(arq_trivial)
    assert valido is False
    assert any("assert trivial" in m.lower() or "true" in m.lower() for m in msgs)

    # Arquivo com asserção real
    arq_bom = tmp_path / "test_bom.py"
    arq_bom.write_text("def test_real():\n    resultado = 2 + 2\n    assert resultado == 4\n", encoding="utf-8")
    
    valido, msgs = validador_seams.validar_arquivo_teste(arq_bom)
    assert valido is True
    assert len(msgs) == 0
