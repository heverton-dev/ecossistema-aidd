# -*- coding: utf-8 -*-
"""
Tratamento de exceções, resolução de colisões e fallback de contexto (D11).
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Dict, List


def resolver_colisao_nome(caminho: Path) -> Path:
    if not caminho.exists():
        return caminho

    diretorio = caminho.parent
    stem = caminho.stem
    ext = caminho.suffix
    contador = 2

    while True:
        candidato = diretorio / f"{stem}-{contador}{ext}"
        if not candidato.exists():
            return candidato
        contador += 1


def extrair_fatos_git_fallback(repo_root: Path, base: str = "HEAD~1") -> Dict[str, List[str]]:
    arquivos: List[str] = []
    commits: List[str] = []

    try:
        res_diff = subprocess.run(
            ["git", "diff", "--name-only", base, "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        if res_diff.returncode == 0:
            arquivos = [linha.strip() for linha in res_diff.stdout.splitlines() if linha.strip()]
    except Exception:
        pass

    try:
        res_log = subprocess.run(
            ["git", "log", "--oneline", f"{base}..HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        if res_log.returncode == 0:
            commits = [linha.strip() for linha in res_log.stdout.splitlines() if linha.strip()]
    except Exception:
        pass

    return {
        "arquivos_modificados": arquivos,
        "commits": commits,
    }
