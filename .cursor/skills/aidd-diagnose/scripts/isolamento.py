# -*- coding: utf-8 -*-
"""
Módulo de Isolamento de Raio de Impacto e Gestão de Worktree Efêmera para aidd-diagnose (D3).
Garante que a ferramenta aidd-diagnose opere de forma estritamente sandboxed:
- Escritas no repositório principal permitidas APENAS em docs/diagnosticos/.
- Na Fase 4 (experimentação e instrumentação temporária), cria worktree efêmera ../worktrees_diagnose-<slug>/ e expurga na saída.
- Reaproveita a infraestrutura base de isolamento de aidd-melhoria (DRY).
"""

from __future__ import annotations

import contextlib
import importlib.util
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Generator, Optional


def _carregar_base_melhoria_isolamento():
    """Carrega dinamicamente classes base de aidd-melhoria para garantir DRY estrito."""
    try:
        from isolamento import SandboxViolationError as _Err, VSAWorktreeManager as _Mgr
        # Certifica que não importou a si mesmo
        if _Mgr.__module__ != __name__:
            return _Err, _Mgr
    except (ImportError, AttributeError):
        pass

    current = Path(__file__).resolve()
    candidates = [current] + list(current.parents)
    for parent in candidates:
        alvo = parent / ".agents" / "skills" / "aidd-melhoria" / "scripts" / "isolamento.py"
        if alvo.is_file():
            spec = importlib.util.spec_from_file_location("aidd_melhoria_isolamento_base", str(alvo))
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                return mod.SandboxViolationError, mod.VSAWorktreeManager

    class _FallbackSandboxViolationError(PermissionError):
        pass

    class _FallbackVSAWorktreeManager:
        def __init__(self, repo_root: str | Path):
            self.repo_root = Path(repo_root).resolve()

    return _FallbackSandboxViolationError, _FallbackVSAWorktreeManager


_BaseSandboxViolationError, _BaseVSAWorktreeManager = _carregar_base_melhoria_isolamento()


class SandboxViolationError(_BaseSandboxViolationError):
    """Lançada quando há tentativa de escrita fora do raio de impacto autorizado de diagnose."""
    pass


def validar_caminho_escrita(
    caminho: str | Path,
    repo_root: str | Path,
    worktree_dir: Optional[str | Path] = None,
) -> bool:
    """
    Valida se um caminho pretendido para escrita respeita o isolamento de diagnose:
    Regra:
      - Permitido: dentro de worktree_dir (espaço de experimentação isolado da Fase 4)
      - Permitido: dentro de repo_root / "docs" / "diagnosticos"
      - Proibido: qualquer outro caminho no repo_root (inclusive outros subdirs de docs/) ou fora dele.
    """
    caminho_abs = Path(caminho).resolve()
    repo_abs = Path(repo_root).resolve()
    docs_diag_permitido = (repo_abs / "docs" / "diagnosticos").resolve()

    # 1. Se estiver dentro do worktree temporário isolado da Fase 4
    if worktree_dir is not None:
        wt_abs = Path(worktree_dir).resolve()
        try:
            caminho_abs.relative_to(wt_abs)
            return True
        except ValueError:
            pass

    # 2. Se estiver dentro de docs/diagnosticos/
    try:
        caminho_abs.relative_to(docs_diag_permitido)
        return True
    except ValueError:
        pass

    # Bloqueio estrito
    raise SandboxViolationError(
        f"[SANDBOX VIOLATION] Tentativa de escrita bloqueada: '{caminho_abs}'. "
        f"Em aidd-diagnose, escrita no repositório só é permitida em 'docs/diagnosticos/' "
        f"ou dentro de worktree efêmera isolada."
    )


def criar_worktree_fase4(repo_root: str | Path, slug: str) -> Path:
    """
    Cria o git worktree efêmero ../worktrees_diagnose-<slug>/ (branch diagnose/<slug>-<id>).
    Sem limpeza automática: quem chama descarta depois (rollback.finalizar_fase5 / `diagnose limpar`).
    """
    raiz = Path(repo_root).resolve()
    branch_name = f"diagnose/{slug}-{uuid.uuid4().hex[:6]}"
    worktree_path = (raiz.parent / f"worktrees_diagnose-{slug}").resolve()

    # Remove previamente caso exista resquício anterior
    if worktree_path.exists():
        shutil.rmtree(worktree_path, ignore_errors=True)

    res = subprocess.run(
        ["git", "worktree", "add", "-b", branch_name, str(worktree_path), "HEAD"],
        cwd=str(raiz),
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        raise RuntimeError(f"Falha ao criar Git Worktree isolado de diagnose: {res.stderr or res.stdout}")
    return worktree_path


def _branch_da_worktree(repo_root: Path, worktree_path: Path) -> Optional[str]:
    res = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=str(repo_root), capture_output=True, text=True,
    )
    atual: Optional[Path] = None
    for linha in res.stdout.splitlines():
        if linha.startswith("worktree "):
            atual = Path(linha[len("worktree "):].strip()).resolve()
        elif linha.startswith("branch ") and atual == worktree_path:
            return linha[len("branch "):].strip().replace("refs/heads/", "", 1)
    return None


class DiagnoseWorktreeManager(_BaseVSAWorktreeManager):
    """Gerenciador de Worktrees efêmeros para experimentação de aidd-diagnose (Fase 4)."""

    def __init__(self, repo_root: str | Path):
        super().__init__(repo_root)
        self.repo_root = Path(repo_root).resolve()

    @contextlib.contextmanager
    def sessao_fase_4(self, slug: str) -> Generator[Path, None, None]:
        """
        Cria um git worktree efêmero isolado em ../worktrees_diagnose-<slug>/ ao entrar na Fase 4.
        Garante limpeza determinística completa (worktree remove + branch delete + rmtree) na saída.
        """
        worktree_path = criar_worktree_fase4(self.repo_root, slug)
        branch_name = _branch_da_worktree(self.repo_root, worktree_path)

        try:
            yield worktree_path
        finally:
            # Expurgo determinístico
            try:
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(worktree_path)],
                    cwd=str(self.repo_root),
                    capture_output=True,
                    text=True,
                )
            except Exception:
                pass

            if branch_name:
                try:
                    subprocess.run(
                        ["git", "branch", "-D", branch_name],
                        cwd=str(self.repo_root),
                        capture_output=True,
                        text=True,
                    )
                except Exception:
                    pass

            if worktree_path.exists():
                shutil.rmtree(worktree_path, ignore_errors=True)


def instrumentar_com_isolamento(
    repo_root: str | Path,
    alvo_relativo: str | Path,
    conteudo: str,
    worktree_dir: Optional[str | Path] = None,
) -> Path:
    """
    Realiza escrita de instrumentação respeitando o sandbox.
    Se worktree_dir for None, tentativa de escrita na árvore principal é bloqueada com SandboxViolationError.
    """
    base_destino = Path(worktree_dir) if worktree_dir else Path(repo_root)
    alvo_final = (base_destino / alvo_relativo).resolve()
    validar_caminho_escrita(alvo_final, repo_root=repo_root, worktree_dir=worktree_dir)

    alvo_final.parent.mkdir(parents=True, exist_ok=True)
    alvo_final.write_text(conteudo, encoding="utf-8")
    return alvo_final
