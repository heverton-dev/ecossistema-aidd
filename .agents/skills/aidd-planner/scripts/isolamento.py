# -*- coding: utf-8 -*-
"""
Isolamento de raio de impacto e sandbox para aidd-planner-runner (D3).
"""

from pathlib import Path
import tempfile
import shutil
from typing import Optional


class SandboxViolationError(Exception):
    pass


def validar_caminho_escrita(caminho: Path | str, base_permitida: Optional[Path] = None) -> Path:
    p = Path(caminho).resolve()
    base = (base_permitida or Path.cwd()).resolve()

    try:
        p.relative_to(base)
    except ValueError:
        raise SandboxViolationError(f"Caminho '{p}' viola sandbox. Permitido sob '{base}'.")

    return p


class PlannerWorktreeManager:
    def __init__(self):
        self.temp_path: Optional[Path] = None

    def __enter__(self) -> Path:
        self.temp_path = Path(tempfile.mkdtemp(prefix="aidd_planner_sandbox_"))
        return self.temp_path

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.temp_path and self.temp_path.exists():
            shutil.rmtree(self.temp_path, ignore_errors=True)
