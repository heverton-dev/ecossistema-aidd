# -*- coding: utf-8 -*-
"""
Isolamento de Raio de Impacto para aidd-forge (D3 / DoD 2).
Confina toda escrita da ferramenta ao diretorio alvo (repo_root) ou a uma
worktree efemera isolada; qualquer outro caminho dispara SandboxViolationError.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

PathLike = Union[str, Path]


class SandboxViolationError(PermissionError):
    """Lancada quando ha tentativa de escrita fora do raio de impacto autorizado de forge."""


def validar_caminho_escrita(
    caminho: PathLike,
    repo_root: PathLike,
    worktree_dir: Optional[PathLike] = None,
) -> bool:
    """
    Valida se um caminho pretendido para escrita respeita o isolamento de forge:
      - Permitido: dentro de worktree_dir (worktree efemera isolada).
      - Permitido: dentro de repo_root (diretorio alvo).
      - Proibido: qualquer outro caminho (inclusive via traversal `..`).
    """
    caminho_abs = Path(caminho).resolve()
    repo_abs = Path(repo_root).resolve()

    if worktree_dir is not None:
        wt_abs = Path(worktree_dir).resolve()
        try:
            caminho_abs.relative_to(wt_abs)
            return True
        except ValueError:
            pass

    try:
        caminho_abs.relative_to(repo_abs)
        return True
    except ValueError:
        pass

    raise SandboxViolationError(
        f"[SANDBOX VIOLATION] Escrita bloqueada: '{caminho_abs}'. "
        f"Em aidd-forge, escrita so e permitida dentro do diretorio alvo '{repo_abs}' "
        f"ou dentro de worktree efemera isolada."
    )


def escrever_com_isolamento(
    repo_root: PathLike,
    alvo_relativo: PathLike,
    conteudo: str,
    worktree_dir: Optional[PathLike] = None,
) -> Path:
    """
    Guard de escrita: valida o caminho final contra as fronteiras do repositorio
    alvo antes de criar o arquivo. Retorna o caminho absoluto escrito.
    """
    base_destino = Path(worktree_dir) if worktree_dir is not None else Path(repo_root)
    alvo_final = (base_destino / alvo_relativo).resolve()
    validar_caminho_escrita(alvo_final, repo_root=repo_root, worktree_dir=worktree_dir)

    alvo_final.parent.mkdir(parents=True, exist_ok=True)
    alvo_final.write_text(conteudo, encoding="utf-8")
    return alvo_final
