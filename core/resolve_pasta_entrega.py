#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""resolve_pasta_entrega — posicionamento determinístico da entrega (ISSUE-USA-0002)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

# Diretórios da ferramenta (nunca contam como projeto legado do usuário).
DIRS_FERRAMENTA = frozenset(
    {
        "tools",
        "gates",
        "componentes",
        "scripts",
        "core",
        "docs",
        "tests",
        "testes",
        "secoes",
        "chaves",
        "node_modules",
        "__pycache__",
        ".git",
        ".venv",
        "venv",
    }
)

MARCADORES_ARQUIVO = frozenset({"package.json", "pyproject.toml", "Cargo.toml", "go.mod"})
MARCADORES_DIR = frozenset({"src", "app", "backend"})


@dataclass(frozen=True)
class ResultadoPasta:
    """Resultado da resolução: caminho, ou erro estruturado de ambiguidade."""

    caminho: Optional[Path] = None
    erro: Optional[str] = None
    opcoes: Optional[List[dict]] = None

    @property
    def ok(self) -> bool:
        return self.erro is None and self.caminho is not None

    def como_dict(self) -> dict:
        if self.ok:
            return {"caminho": str(self.caminho)}
        return {
            "erro": self.erro,
            "opcoes": self.opcoes or [],
            "instrucao": "Escolha com --pasta <caminho> e rode de novo.",
        }


def _eh_marcador(path: Path) -> bool:
    if path.is_file() and path.name in MARCADORES_ARQUIVO:
        return True
    if path.is_dir() and path.name in MARCADORES_DIR:
        return True
    return False


def _tem_legado(dir_path: Path, ignorar: Optional[set[str]] = None) -> bool:
    """True se `dir_path` contém projeto legado do usuário (fora de dirs da ferramenta)."""
    if not dir_path.is_dir():
        return False
    ignorar = set(ignorar or ())
    try:
        filhos = list(dir_path.iterdir())
    except OSError:
        return False
    for filho in filhos:
        if filho.name in DIRS_FERRAMENTA or filho.name in ignorar:
            continue
        if _eh_marcador(filho):
            return True
        if filho.is_dir():
            try:
                for sub in filho.iterdir():
                    if _eh_marcador(sub):
                        return True
            except OSError:
                continue
    return False


def _eh_raiz_ferramenta(dir_path: Path) -> bool:
    return (
        (dir_path / "ecossistema.py").is_file()
        and (dir_path / "gates").is_dir()
        and (dir_path / "componentes").is_dir()
    )


def resolve_pasta_entrega(
    cwd: Path,
    nome_projeto: str,
    pasta_arg: Optional[str] = None,
) -> ResultadoPasta:
    """Resolve a pasta de entrega do app do usuário.

    Regras (especificação §2.2):
    1. `pasta_arg` explícita sempre vence.
    2. Legado irmão presente ⇒ raiz do workspace, NUNCA `<clone>/projetos/`.
    3. CWD exclusivamente ferramenta ⇒ `<clone>/projetos/<slug>`.
    4. Ambiguidade (2+ candidatos) ⇒ erro estruturado, zero escrita (Lei #7).
    """
    cwd = Path(cwd).resolve()

    if pasta_arg:
        return ResultadoPasta(caminho=Path(pasta_arg).expanduser().resolve())

    slug = _slugificar(nome_projeto)

    # Onde está a ferramenta e quais bases de workspace considerar.
    if _eh_raiz_ferramenta(cwd):
        raiz_ferramenta = cwd
        bases = [cwd.parent]
    else:
        raiz_ferramenta = None
        tem_clone_filho = False
        if cwd.is_dir():
            try:
                tem_clone_filho = any(_eh_raiz_ferramenta(f) for f in cwd.iterdir() if f.is_dir())
            except OSError:
                tem_clone_filho = False
        if tem_clone_filho:
            # cwd é o workspace que contém o clone — só ele decide.
            bases = [cwd]
        else:
            # Contexto incerto: cwd e pai podem ser workspace (Lei #7).
            bases = [cwd, cwd.parent]

    candidatos: List[dict] = []
    for base in bases:
        if not base.is_dir():
            continue
        ignorar = (
            {raiz_ferramenta.name}
            if raiz_ferramenta is not None and raiz_ferramenta.parent == base
            else set()
        )
        if _tem_legado(base, ignorar=ignorar):
            alvo = base / slug
            rotulo = "Na pasta atual (junto ao projeto antigo)"
            if not any(c["caminho"] == alvo for c in candidatos):
                candidatos.append({"rotulo": rotulo, "caminho": alvo, "base": base})

    if len(candidatos) > 1:
        return ResultadoPasta(
            erro="pasta_entrega_ambigua",
            opcoes=[
                {"rotulo": c["rotulo"], "caminho": str(c["caminho"])}
                for c in candidatos
            ],
        )

    if len(candidatos) == 1:
        return ResultadoPasta(caminho=candidatos[0]["caminho"])

    # Sem legado: ferramenta pura ⇒ projetos/<slug> sob a raiz da ferramenta.
    base_ferramenta = raiz_ferramenta if raiz_ferramenta is not None else cwd
    return ResultadoPasta(caminho=(base_ferramenta / "projetos" / slug))


def _slugificar(nome: str) -> str:
    import re

    return re.sub(r"[^a-z0-9]+", "-", (nome or "").lower()).strip("-") or "projeto-app"
