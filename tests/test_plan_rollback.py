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

rollback = _carregar_modulo("aidd_plan_rollback", "componentes/compartilhado/skills/aidd-plan/scripts/rollback.py")


def test_rollback_remove_arquivos_parciais_em_caso_de_erro():
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir)
        pasta_parcial = dest / "PLAN-0001-falha"

        with pytest.raises(RuntimeError):
            with rollback.executar_com_rollback() as rastreador:
                pasta_parcial.mkdir()
                rastreador.registrar(pasta_parcial)
                (pasta_parcial / "arquivo.md").write_text("parcial", encoding="utf-8")
                raise RuntimeError("Falha intencional")

        assert not pasta_parcial.exists()


def test_rollback_mantem_arquivos_quando_sucesso():
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir)
        pasta_sucesso = dest / "PLAN-0001-sucesso"

        with rollback.executar_com_rollback() as rastreador:
            pasta_sucesso.mkdir()
            rastreador.registrar(pasta_sucesso)

        assert pasta_sucesso.exists()
