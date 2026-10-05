import pytest
from pathlib import Path
import tempfile
import importlib.util

def _carregar_modulo(nome, rel_path):
    p = Path(__file__).resolve().parent.parent / rel_path
    spec = importlib.util.spec_from_file_location(nome, str(p))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

handoff = _carregar_modulo("aidd_plan_handoff", "componentes/compartilhado/skills/aidd-plan/scripts/handoff.py")


def test_emitir_e_verificar_manifesto_plano():
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir)
        pasta = dest / "PLAN-0001-teste"
        pasta.mkdir()
        (pasta / "00-PROCESSO-E-DECISOES.md").write_text("# Processo\n", encoding="utf-8")
        (pasta / "01-item.md").write_text("# Item 1\n", encoding="utf-8")

        manifesto = handoff.emitir_manifesto(pasta)
        assert manifesto["tipo"] == "aidd-plan"
        assert "assinatura_hmac" in manifesto
        assert handoff.verificar_manifesto(manifesto) is True

        # Adulteração
        manifesto["total_arquivos"] = 999
        assert handoff.verificar_manifesto(manifesto) is False
