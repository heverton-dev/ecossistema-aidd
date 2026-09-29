# -*- coding: utf-8 -*-
"""
Isolamento de Raio de Impacto para aidd-enterprise (D3).
Confina toda escrita da ferramenta aos componentes autorizados (allowlist)
dentro de repo_root ou dentro de uma worktree efemera isolada; a raiz do
repositorio e qualquer diretorio nao listado disparam SandboxViolationError.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional, Union

PathLike = Union[str, Path]


class SandboxViolationError(PermissionError):
    """Lancada quando ha tentativa de escrita fora do raio de impacto autorizado de aidd-enterprise."""


def _normalizar_permitidos(caminhos_permitidos: Iterable[PathLike]) -> list[Path]:
    return [Path(p) for p in caminhos_permitidos]


def validar_caminho_escrita(
    caminho: PathLike,
    repo_root: PathLike,
    caminhos_permitidos: Iterable[PathLike],
    worktree_dir: Optional[PathLike] = None,
) -> bool:
    """
    Valida se um caminho pretendido para escrita respeita o isolamento de aidd-enterprise:
      - Permitido: dentro de worktree_dir (worktree efemera isolada).
      - Permitido: dentro de repo_root E coberto por um dos caminhos permitidos.
      - Proibido: raiz do repositorio, diretorios nao listados, qualquer outro
        caminho (inclusive via traversal `..`).
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
    except ValueError:
        raise SandboxViolationError(
            f"[SANDBOX VIOLATION] Escrita bloqueada: '{caminho_abs}'. "
            f"Em aidd-enterprise, escrita so e permitida dentro de worktree efemera isolada "
            f"ou dentro dos componentes autorizados de '{repo_abs}'."
        )

    if caminho_abs == repo_abs:
        raise SandboxViolationError(
            f"[SANDBOX VIOLATION] Escrita na raiz do repositorio bloqueada: '{caminho_abs}'. "
            f"Em aidd-enterprise, a raiz nao e um componente autorizado."
        )

    for permitido in _normalizar_permitidos(caminhos_permitidos):
        permitido_abs = (repo_abs / permitido).resolve()
        try:
            caminho_abs.relative_to(permitido_abs)
            return True
        except ValueError:
            continue

    permitidos_txt = ", ".join(str(p) for p in _normalizar_permitidos(caminhos_permitidos))
    raise SandboxViolationError(
        f"[SANDBOX VIOLATION] Escrita bloqueada: '{caminho_abs}'. "
        f"Em aidd-enterprise, escrita so e permitida nos componentes autorizados: {permitidos_txt}."
    )


def escrever_com_isolamento(
    repo_root: PathLike,
    alvo_relativo: PathLike,
    conteudo: str,
    caminhos_permitidos: Iterable[PathLike],
    worktree_dir: Optional[PathLike] = None,
) -> Path:
    """
    Guard de escrita: valida o caminho final contra a allowlist de componentes
    e a worktree efemera antes de criar o arquivo. Retorna o caminho absoluto escrito.
    """
    base_destino = Path(worktree_dir) if worktree_dir is not None else Path(repo_root)
    alvo_final = (base_destino / alvo_relativo).resolve()
    validar_caminho_escrita(
        alvo_final,
        repo_root=repo_root,
        caminhos_permitidos=caminhos_permitidos,
        worktree_dir=worktree_dir,
    )

    alvo_final.parent.mkdir(parents=True, exist_ok=True)
    alvo_final.write_text(conteudo, encoding="utf-8")
    return alvo_final
