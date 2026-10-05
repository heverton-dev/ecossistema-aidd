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

fallback = _carregar_modulo("aidd_plan_fallback", "componentes/compartilhado/skills/aidd-plan/scripts/fallback.py")


def test_resolver_conflito_diretorio():
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir)
        pasta_original = dest / "PLAN-0001-teste"
        pasta_original.mkdir()

        segura = fallback.resolver_colisao_pasta(pasta_original)
        assert segura != pasta_original
        assert str(segura).endswith("-2")


def test_corrigir_cercas_aninhadas():
    conteudo_aninhado = "texto\n```bash\n```python\necho 1\n```\n```\n"
    corrigido = fallback.corrigir_cercas_aninhadas(conteudo_aninhado)
    assert "~~~" in corrigido
