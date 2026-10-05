# -*- coding: utf-8 -*-
"""
Critério de rejeição e rollback automático para aidd-planner-runner (D14).
"""

from contextlib import contextmanager
from pathlib import Path
import shutil
from typing import List, Generator


class RastreadorArquivos:
    def __init__(self):
        self.caminhos: List[Path] = []

    def registrar(self, caminho: Path | str) -> Path:
        p = Path(caminho).resolve()
        self.caminhos.append(p)
        return p

    def limpar(self):
        for p in reversed(self.caminhos):
            if p.exists():
                if p.is_dir():
                    shutil.rmtree(p, ignore_errors=True)
                else:
                    try:
                        p.unlink()
                    except OSError:
                        pass


@contextmanager
def executar_com_rollback() -> Generator[RastreadorArquivos, None, None]:
    rastreador = RastreadorArquivos()
    try:
        yield rastreador
    except Exception:
        rastreador.limpar()
        raise
