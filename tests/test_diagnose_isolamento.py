# -*- coding: utf-8 -*-
"""
Teste de Raio de Impacto e Isolamento para aidd-diagnose (Ticket 2 / D3 / DoD 2).
Exige:
- Criação de worktree efêmera ../worktrees_diagnose-<slug>/ ao entrar na Fase 4 e expurgo na saída.
- Bloqueio de escrita fora da worktree, exceto em docs/diagnosticos/.
- Reuso da lógica de aidd-melhoria sem duplicação de código.
- Escrita de instrumentação na árvore principal reprova (exit 1 / SandboxViolationError).
- Árvore principal limpa (git status clean) após a Fase 4.
"""

import os
import subprocess
import sys
from pathlib import Path
import pytest

import importlib.util
import os
import subprocess
import sys
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
SKILL_SCRIPTS = ROOT_DIR / ".agents" / "skills" / "aidd-diagnose" / "scripts"


def carregar_isolamento_diagnose():
    caminho = SKILL_SCRIPTS / "isolamento.py"
    spec = importlib.util.spec_from_file_location("aidd_diagnose_isolamento", str(caminho))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_import_isolamento():
    """Importa o módulo de isolamento de aidd-diagnose."""
    isolamento = carregar_isolamento_diagnose()
    assert hasattr(isolamento, "validar_caminho_escrita")
    assert hasattr(isolamento, "DiagnoseWorktreeManager")
    assert hasattr(isolamento, "SandboxViolationError")


def test_escrita_fora_de_docs_diagnosticos_ou_worktree_e_bloqueada(tmp_path):
    """Bloqueia escritas fora da worktree, permitindo APENAS docs/diagnosticos/."""
    diag_mod = carregar_isolamento_diagnose()
    validar_caminho_escrita = diag_mod.validar_caminho_escrita
    SandboxViolationError = diag_mod.SandboxViolationError

    repo_falso = tmp_path / "repo"
    repo_falso.mkdir()
    docs_diag = repo_falso / "docs" / "diagnosticos"
    docs_diag.mkdir(parents=True)
    docs_melhorias = repo_falso / "docs" / "melhorias"
    docs_melhorias.mkdir(parents=True)
    worktree_dir = tmp_path / "worktrees_diagnose-meu-sintoma"
    worktree_dir.mkdir()

    # Permitido: docs/diagnosticos/
    arq_ok_diag = docs_diag / "20260924_teste" / "sessao.json"
    assert validar_caminho_escrita(arq_ok_diag, repo_root=repo_falso, worktree_dir=worktree_dir) is True

    # Permitido: dentro da worktree efêmera
    arq_ok_wt = worktree_dir / "src" / "instrumentacao.py"
    assert validar_caminho_escrita(arq_ok_wt, repo_root=repo_falso, worktree_dir=worktree_dir) is True

    # PROIBIDO: raiz do repo
    with pytest.raises(SandboxViolationError):
        validar_caminho_escrita(repo_falso / "main.py", repo_root=repo_falso, worktree_dir=worktree_dir)

    # PROIBIDO: docs/melhorias (diagnose só permite docs/diagnosticos/)
    with pytest.raises(SandboxViolationError):
        validar_caminho_escrita(docs_melhorias / "relatorio.json", repo_root=repo_falso, worktree_dir=worktree_dir)

    # PROIBIDO: pastas de código fonte no repositório principal
    with pytest.raises(SandboxViolationError):
        validar_caminho_escrita(repo_falso / "scripts" / "infiltrado.py", repo_root=repo_falso, worktree_dir=worktree_dir)


def test_escrever_instrumentacao_no_working_tree_principal_falha(tmp_path):
    """Teste exigido: tentativa de escrever instrumentação na main working tree deve falhar (exit 1 / erro)."""
    diag_mod = carregar_isolamento_diagnose()
    instrumentar_com_isolamento = diag_mod.instrumentar_com_isolamento
    SandboxViolationError = diag_mod.SandboxViolationError

    repo = tmp_path / "repo_git"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=str(repo), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "audit@aidd.dev"], cwd=str(repo), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Audit Runner"], cwd=str(repo), check=True, capture_output=True)

    dummy_file = repo / "app.py"
    dummy_file.write_text("def hello(): return 'world'\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=str(repo), check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=str(repo), check=True, capture_output=True)

    # Tentativa de instrumentar apontando para a raiz sem worktree deve disparar violação de sandbox
    with pytest.raises(SandboxViolationError):
        instrumentar_com_isolamento(
            repo_root=repo,
            alvo_relativo="app.py",
            conteudo="# INSTRUMENTACAO\n",
            worktree_dir=None,  # Sem worktree -> tentativa na árvore principal
        )


def test_fase4_worktree_lifecycle_e_git_status_clean(tmp_path):
    """
    Ao entrar na Fase 4 cria ephemeral worktree ../worktrees_diagnose-<slug>/.
    Remove ao sair. Após sair, o git status da árvore principal fica limpo (clean).
    """
    diag_mod = carregar_isolamento_diagnose()
    DiagnoseWorktreeManager = diag_mod.DiagnoseWorktreeManager

    repo = tmp_path / "repo_principal"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=str(repo), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "audit@aidd.dev"], cwd=str(repo), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Audit Runner"], cwd=str(repo), check=True, capture_output=True)

    codigo = repo / "servico.py"
    codigo.write_text("def process(): pass\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=str(repo), check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "commit inicial"], cwd=str(repo), check=True, capture_output=True)

    manager = DiagnoseWorktreeManager(repo_root=repo)
    slug = "falha-conexao-banco"

    # Fase 4 entra na worktree
    with manager.sessao_fase_4(slug=slug) as wt_path:
        # Verifica padrão do caminho ../worktrees_diagnose-<slug>/
        assert wt_path.name == f"worktrees_diagnose-{slug}"
        assert wt_path.exists()
        assert wt_path.resolve() != repo.resolve()

        # Escreve instrumentação DENTRO da worktree
        arquivo_wt = wt_path / "servico.py"
        arquivo_wt.write_text("def process(): print('AIDD-DIAGNOSE-TEMP'); pass\n", encoding="utf-8")
        assert "AIDD-DIAGNOSE-TEMP" in arquivo_wt.read_text(encoding="utf-8")

        # Verifica que o repositório principal está limpo (sem modificação de servico.py)
        diff_res = subprocess.run(["git", "status", "--porcelain"], cwd=str(repo), capture_output=True, text=True)
        assert diff_res.stdout.strip() == "", "Árvore principal não deveria ter alterações durante a Fase 4"

    # Ao sair da Fase 4: worktree foi removida
    assert not wt_path.exists(), "Worktree efêmera deve ser removida na saída"

    # git status da árvore principal deve continuar 100% limpo
    res_status = subprocess.run(["git", "status", "--porcelain"], cwd=str(repo), capture_output=True, text=True)
    assert res_status.returncode == 0
    assert res_status.stdout.strip() == "", f"git status deve estar limpo após a Fase 4: {res_status.stdout}"
