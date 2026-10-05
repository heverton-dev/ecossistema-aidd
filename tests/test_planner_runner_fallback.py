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

fallback = _carregar_modulo("aidd_planner_fallback", "componentes/compartilhado/skills/aidd-planner/scripts/fallback.py")


def test_resolver_colisao_pasta_projeto():
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir)
        pasta = dest / "meu-projeto"
        pasta.mkdir()

        segura = fallback.resolver_colisao_pasta(pasta)
        assert segura != pasta
        assert str(segura).endswith("-2")
