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

cli = _carregar_modulo("aidd_plan_cli", "componentes/compartilhado/skills/aidd-plan/scripts/cli.py")


def test_cli_falha_sem_argumentos():
    assert cli.main([]) == 1


def test_cli_falha_subcomando_invalido():
    assert cli.main(["comando_inexistente"]) == 1


def test_cli_executa_init_e_check_fences():
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir)
        rc = cli.main(["init", "teste-cli", "--itens", "Item 1", "--destino", str(dest)])
        assert rc == 0

        pasta = dest / "PLAN-0001-teste-cli"
        assert pasta.exists()

        rc_check = cli.main(["check-fences", str(pasta)])
        assert rc_check == 0
