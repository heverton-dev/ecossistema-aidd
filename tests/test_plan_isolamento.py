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

isolamento = _carregar_modulo("aidd_plan_isolamento", "componentes/compartilhado/skills/aidd-plan/scripts/isolamento.py")


def test_validar_caminho_escrita_rejeita_fora_de_docs_planos():
    raiz = Path("C:/repo_fake")
    caminho_invalido = raiz / "src" / "invalido.md"
    with pytest.raises(isolamento.SandboxViolationError):
        isolamento.validar_caminho_escrita(caminho_invalido, raiz=raiz)

    caminho_valido = raiz / "docs" / "planos" / "PLAN-0001-teste" / "01-item.md"
    assert isolamento.validar_caminho_escrita(caminho_valido, raiz=raiz) == caminho_valido.resolve()


def test_worktree_manager_cria_diretorio_temporario():
    with isolamento.PlanWorktreeManager() as sandbox_dir:
        assert sandbox_dir.exists()
        assert sandbox_dir.is_dir()
    assert not sandbox_dir.exists()
