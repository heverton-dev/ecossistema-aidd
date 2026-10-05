# -*- coding: utf-8 -*-
import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent

def carregar_rollback():
    rb_path = ROOT / "componentes" / "compartilhado" / "skills" / "aidd-handoff" / "scripts" / "rollback.py"
    spec = importlib.util.spec_from_file_location("aidd_handoff_rollback", str(rb_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_rollback_remove_arquivo_em_caso_de_erro(tmp_path):
    rb = carregar_rollback()
    arquivo_temp = tmp_path / "sessao-parcial.md"

    with pytest.raises(RuntimeError):
        with rb.executar_com_rollback(arquivo_temp):
            arquivo_temp.write_text("conteudo parcial", encoding="utf-8")
            assert arquivo_temp.exists()
            raise RuntimeError("Falha forcada no meio da geracao")

    assert not arquivo_temp.exists()

def test_rollback_mantem_arquivo_em_sucesso(tmp_path):
    rb = carregar_rollback()
    arquivo_temp = tmp_path / "sessao-sucesso.md"

    with rb.executar_com_rollback(arquivo_temp):
        arquivo_temp.write_text("conteudo final", encoding="utf-8")

    assert arquivo_temp.exists()
