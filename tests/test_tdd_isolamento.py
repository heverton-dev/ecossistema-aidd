import os
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent

def test_tdd_isolamento_valida_escrita_permitida(tmp_path):
    sys.path.insert(0, str(ROOT / ".agents" / "skills" / "aidd-tdd" / "scripts"))
    import isolamento

    manager = isolamento.TddWorktreeManager(repo_root=tmp_path)
    
    # docs/tdd e permitido
    permitido = tmp_path / "docs" / "tdd" / "teste.json"
    assert manager.validar_caminho_escrita(permitido) is True

    # fora de docs/tdd sem worktree deve disparar excecao
    proibido = tmp_path / "src" / "perigoso.py"
    with pytest.raises(isolamento.SandboxViolationError):
        manager.validar_caminho_escrita(proibido)

def test_tdd_isolamento_worktree_ciclo(tmp_path):
    sys.path.insert(0, str(ROOT / ".agents" / "skills" / "aidd-tdd" / "scripts"))
    import isolamento

    manager = isolamento.TddWorktreeManager(repo_root=tmp_path)
    worktree_path = manager.obter_caminho_worktree("seam_teste")
    assert "worktrees_tdd-seam_teste" in str(worktree_path)
