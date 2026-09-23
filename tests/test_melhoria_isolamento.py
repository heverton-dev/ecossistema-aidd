# -*- coding: utf-8 -*-
"""
Teste de Raio de Impacto e Isolamento (Ticket 1 / D3 / DoD 5).
Exige que qualquer escrita fora de docs/ ou fora do Git Worktree efêmero isolado seja bloqueada (exit 1 / exceção).
"""

import os
import sys
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
SKILL_SCRIPTS = ROOT_DIR / ".agents" / "skills" / "aidd-melhoria" / "scripts"
if str(SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS))


def test_escrita_fora_de_docs_ou_worktree_e_bloqueada(tmp_path):
    """Garante que tentativa de escrita na raiz do repositório fora de docs/ é terminantemente bloqueada."""
    from isolamento import validar_caminho_escrita, SandboxViolationError

    repo_falso = tmp_path / "repo"
    repo_falso.mkdir()
    docs_melhorias = repo_falso / "docs" / "melhorias"
    docs_melhorias.mkdir(parents=True)
    worktree_dir = tmp_path / "vsa_worktree"
    worktree_dir.mkdir()

    # Escrita permitida em docs/melhorias
    arq_ok_docs = docs_melhorias / "relatorio.json"
    assert validar_caminho_escrita(arq_ok_docs, repo_root=repo_falso, worktree_dir=worktree_dir) is True

    # Escrita permitida dentro do worktree isolado
    arq_ok_wt = worktree_dir / "src" / "codigo.py"
    assert validar_caminho_escrita(arq_ok_wt, repo_root=repo_falso, worktree_dir=worktree_dir) is True

    # Escrita PROIBIDA na raiz do repositório (ex: ecossistema.py ou README.md)
    arq_bloqueado = repo_falso / "ecossistema.py"
    with pytest.raises(SandboxViolationError):
        validar_caminho_escrita(arq_bloqueado, repo_root=repo_falso, worktree_dir=worktree_dir)

    # Escrita PROIBIDA em pasta interna fora de docs/melhorias (ex: scripts/ ou gates/)
    arq_bloqueado_scripts = repo_falso / "scripts" / "infiltrado.py"
    with pytest.raises(SandboxViolationError):
        validar_caminho_escrita(arq_bloqueado_scripts, repo_root=repo_falso, worktree_dir=worktree_dir)


def test_worktree_vsa_lifecycle(tmp_path):
    """Garante ciclo de vida do Git Worktree efêmero isolado com criação e expurgo seguro."""
    from isolamento import VSAWorktreeManager
    import subprocess

    repo = tmp_path / "git_repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=str(repo), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "audit@aidd.dev"], cwd=str(repo), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Audit Runner"], cwd=str(repo), check=True, capture_output=True)

    dummy_file = repo / "init.txt"
    dummy_file.write_text("root init", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=str(repo), check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=str(repo), check=True, capture_output=True)

    manager = VSAWorktreeManager(repo_root=repo)
    with manager.sessao_isolada(prefixo="analise-teste") as wt_path:
        assert wt_path.exists()
        assert wt_path != repo
        # Cria arquivo dentro do worktree
        teste_wt = wt_path / "analise.tmp"
        teste_wt.write_text("dados temporarios", encoding="utf-8")
        assert teste_wt.exists()

    # Ao sair do context manager, o worktree deve ter sido limpo e expurgado
    assert not wt_path.exists()
