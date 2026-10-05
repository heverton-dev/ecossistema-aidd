# -*- coding: utf-8 -*-
"""
Isolamento de raio de impacto e gerenciador de sandbox/worktree para aidd-plan (D3).
"""

from pathlib import Path
import tempfile
import shutil
from typing import Optional


class SandboxViolationError(Exception):
    """Lançada quando há tentativa de escrita fora do escopo permitido."""
    pass


def validar_caminho_escrita(caminho: Path | str, raiz: Optional[Path] = None) -> Path:
    p = Path(caminho).resolve()
    base_raiz = (raiz or Path.cwd()).resolve()
    permitido = (base_raiz / "docs" / "planos").resolve()

    try:
        p.relative_to(permitido)
    except ValueError:
        raise SandboxViolationError(f"Caminho '{p}' viola o isolamento. Permitido apenas sob '{permitido}'.")

    return p


class PlanWorktreeManager:
    """Gerencia sandbox efêmero em diretório temporário isolado."""
    def __init__(self):
        self.temp_path: Optional[Path] = None

    def __enter__(self) -> Path:
        self.temp_path = Path(tempfile.mkdtemp(prefix="aidd_plan_sandbox_"))
        return self.temp_path

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.temp_path and self.temp_path.exists():
            shutil.rmtree(self.temp_path, ignore_errors=True)
