# -*- coding: utf-8 -*-
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parent.parent

def test_handoff_isolamento_bloqueia_fora_de_docs_secoes(tmp_path):
    sys.path.insert(0, str(ROOT / "componentes" / "compartilhado" / "skills" / "aidd-handoff" / "scripts"))
    import isolamento

    manager = isolamento.HandoffWorktreeManager(repo_root=tmp_path)
    arquivo_valido = tmp_path / "docs" / "secoes" / "sessao-teste.md"
    arquivo_invalido = tmp_path / "src" / "malicioso.py"

    assert manager.validar_caminho_escrita(arquivo_valido) is True
    with pytest.raises(isolamento.SandboxViolationError):
        manager.validar_caminho_escrita(arquivo_invalido)

def test_validar_caminho_escrita_helper(tmp_path):
    sys.path.insert(0, str(ROOT / "componentes" / "compartilhado" / "skills" / "aidd-handoff" / "scripts"))
    import isolamento

    arquivo_valido = tmp_path / "docs" / "secoes" / "sessao-teste.md"
    arquivo_invalido = tmp_path / "root.py"
    assert isolamento.validar_caminho_escrita(arquivo_valido, repo_root=tmp_path) is True
    with pytest.raises(isolamento.SandboxViolationError):
        isolamento.validar_caminho_escrita(arquivo_invalido, repo_root=tmp_path)
