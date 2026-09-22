# -*- coding: utf-8 -*-
"""Varredura determinística de vendor lock-in (ISSUE-USA-0008 / Lei #1).

Nunca apaga arquivo do usuário (Lei #7) — apenas lista e, se houver
allowlist, sinaliza como intencional (Lei #8).
"""

from __future__ import annotations

import re
from pathlib import Path

EXTENSOES = {".json", ".ts", ".tsx", ".js", ".py", ".toml", ".yml", ".yaml", ".md"}
PADRAO = re.compile(r"\b(lovable|supabase|firebase)\b", re.IGNORECASE)
DIRS_RESIDUAIS = {".lovable", "supabase"}
DIRS_FERRAMENTA = {
    "tools", "gates", "componentes", "scripts", "core", "docs",
    "tests", "testes", ".git", ".venv", "venv", "node_modules",
    "__pycache__", ".worktrees",
    # harnesses/destinos gerados — menção a Lovable é o produto do Bridge
    ".claude", ".agents", ".mimocode", ".opencode", ".gemini",
    ".cursor", ".codebuddy", ".skills", ".hooks", ".github",
}
# Allowlist opcional: um arquivo `lockin-allowlist.txt` na raiz da entrega,
# uma palavra por linha (ex.: supabase), comjustificativa após #.


def _allowlist(raiz: Path) -> set[str]:
    alvo = raiz / "lockin-allowlist.txt"
    if not alvo.is_file():
        return set()
    out: set[str] = set()
    for linha in alvo.read_text(encoding="utf-8", errors="ignore").splitlines():
        termo = linha.split("#", 1)[0].strip().lower()
        if termo:
            out.add(termo)
    return out


def varredura(raiz: Path) -> dict:
    """Retorna {'hits': [...], 'dirs': [...], 'permitidos': [...]} sem escrever nada."""
    raiz = Path(raiz).resolve()
    allow = _allowlist(raiz)
    hits: list[str] = []
    dirs: list[str] = []
    permitidos: list[str] = []

    if not raiz.is_dir():
        return {"hits": hits, "dirs": dirs, "permitidos": permitidos}

    for path in raiz.rglob("*"):
        partes = set(path.relative_to(raiz).parts)
        if partes & DIRS_FERRAMENTA:
            continue
        if path.is_dir() and path.name in DIRS_RESIDUAIS:
            chave = path.name.lstrip(".").lower()
            if chave in allow:
                permitidos.append(str(path.relative_to(raiz)))
            else:
                dirs.append(str(path.relative_to(raiz)))
            continue
        if not path.is_file() or path.suffix.lower() not in EXTENSOES:
            continue
        try:
            texto = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in PADRAO.finditer(texto):
            termo = m.group(1).lower()
            rel = str(path.relative_to(raiz))
            if termo in allow:
                permitidos.append(f"{rel}:{m.group(1)}")
            else:
                hits.append(f"{rel}: {m.group(1)}")
    return {"hits": hits, "dirs": dirs, "permitidos": permitidos}


def possui_sujeira(resultado: dict) -> bool:
    return bool(resultado["hits"] or resultado["dirs"])


def descrever(resultado: dict, raiz: Path | None = None) -> str:
    """Mensagem PT-BR simples — lista, nunca apaga (Lei #7)."""
    if not possui_sujeira(resultado):
        extra = ""
        if resultado["permitidos"]:
            extra = f" ({len(resultado['permitidos'])} item(ns) na allowlist, intencional)"
        return f"Varredura anti-lock-in limpa{extra}."
    linhas = [
        "Resíduo de fornecedor detectado (nada foi apagado):",
    ]
    for d in resultado["dirs"]:
        linhas.append(f"  pasta: {d}")
    for h in resultado["hits"][:30]:
        linhas.append(f"  {h}")
    if len(resultado["hits"]) > 30:
        linhas.append(f"  ... e mais {len(resultado['hits']) - 30}")
    linhas.append("Para remover, confirme item a item (Lei #7).")
    linhas.append("Se o uso for intencional, crie lockin-allowlist.txt com o termo.")
    return "\n".join(linhas)
