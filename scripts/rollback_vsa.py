# -*- coding: utf-8 -*-
"""
Limpeza Determinística e Rollback Transacional (VSA).
Dimensão D14: Critério de Rejeição (Rollback).
"""

import os
from pathlib import Path
from typing import List


class TransacaoModularVSA:
    def __init__(self, diretorio_base: Path):
        self.diretorio_base = Path(diretorio_base).resolve()
        self.artefatos_temporarios: List[Path] = []
        self._sucesso = False

    def __enter__(self):
        return self

    def criar_artefato_temporario(self, nome_relativo: str, conteudo: str) -> Path:
        caminho = self.diretorio_base / nome_relativo
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(conteudo, encoding="utf-8")
        self.artefatos_temporarios.append(caminho)
        return caminho

    def marcar_sucesso(self) -> None:
        self._sucesso = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None or not self._sucesso:
            # Rollback: remove todos os artefatos temporarios criados
            for arq in self.artefatos_temporarios:
                if arq.exists():
                    try:
                        arq.unlink()
                    except OSError:
                        pass
        else:
            # Sucesso: limpa arquivos marcados como temporários
            for arq in self.artefatos_temporarios:
                if arq.exists():
                    try:
                        arq.unlink()
                    except OSError:
                        pass
