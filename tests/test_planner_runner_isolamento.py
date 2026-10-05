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

isolamento = _carregar_modulo("aidd_planner_isolamento", "componentes/compartilhado/skills/aidd-planner/scripts/isolamento.py")


def test_validar_caminho_escrita_planner():
    raiz = Path("C:/repo_fake")
    caminho_invalido = raiz / "sistema_operacional" / "invalido.json"
    with pytest.raises(isolamento.SandboxViolationError):
        isolamento.validar_caminho_escrita(caminho_invalido, base_permitida=raiz / "projetos")

    caminho_valido = raiz / "projetos" / "meu_app" / "PLANNER.json"
    assert isolamento.validar_caminho_escrita(caminho_valido, base_permitida=raiz / "projetos") == caminho_valido.resolve()


def test_worktree_manager_planner():
    with isolamento.PlannerWorktreeManager() as sandbox_dir:
        assert sandbox_dir.exists()
        assert sandbox_dir.is_dir()
    assert not sandbox_dir.exists()
