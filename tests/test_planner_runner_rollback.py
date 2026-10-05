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

rollback = _carregar_modulo("aidd_planner_rollback", "componentes/compartilhado/skills/aidd-planner/scripts/rollback.py")


def test_rollback_planner_em_caso_de_erro():
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir)
        pasta_projeto = dest / "projeto-falho"

        with pytest.raises(RuntimeError):
            with rollback.executar_com_rollback() as rastreador:
                pasta_projeto.mkdir()
                rastreador.registrar(pasta_projeto)
                (pasta_projeto / "PLANNER.json").write_text("parcial", encoding="utf-8")
                raise RuntimeError("Falha intencional")

        assert not pasta_projeto.exists()
