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

handoff = _carregar_modulo("aidd_planner_handoff", "componentes/compartilhado/skills/aidd-planner/scripts/handoff.py")


def test_emitir_e_verificar_manifesto_planner():
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir)
        pasta = dest / "meu-app"
        pasta.mkdir()
        (pasta / "PLANNER.json").write_text('{"app": "ok"}', encoding="utf-8")

        manifesto = handoff.emitir_manifesto(pasta)
        assert manifesto["tipo"] == "aidd-planner"
        assert "assinatura_hmac" in manifesto
        assert handoff.verificar_manifesto(manifesto) is True

        manifesto["arquivo_planner"] = "alterado"
        assert handoff.verificar_manifesto(manifesto) is False
