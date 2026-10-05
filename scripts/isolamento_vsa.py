# -*- coding: utf-8 -*-
"""
Isolamento de Raio de Impacto e Worktree Efêmera (VSA).
Dimensão D3: Raio de Impacto e Isolamento.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional


class VSAWorktreeContext:
    def __init__(self, nome: str = "vsa-worktree"):
        self.nome = nome
        self._temp_dir: Optional[str] = None
        self.worktree_path: Optional[Path] = None

    def __enter__(self):
        self._temp_dir = tempfile.mkdtemp(prefix=f"wt_{self.nome}_")
        self.worktree_path = Path(self._temp_dir).resolve()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._temp_dir and os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir, ignore_errors=True)

    def validar_caminho_permitido(self, caminho: Path) -> Path:
        caminho_resolvido = Path(caminho).resolve()
        try:
            caminho_resolvido.relative_to(self.worktree_path)
        except ValueError:
            raise PermissionError(
                f"Mutação proibida fora do worktree efêmero: {caminho_resolvido} "
                f"não está contido em {self.worktree_path}"
            )
        return caminho_resolvido

    def escrever_arquivo(self, caminho: Path, conteudo: str, encoding: str = "utf-8") -> None:
        alvo = self.validar_caminho_permitido(caminho)
        alvo.parent.mkdir(parents=True, exist_ok=True)
        alvo.write_text(conteudo, encoding=encoding)
