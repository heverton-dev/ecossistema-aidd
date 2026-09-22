#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G_LAYOUT_ENTREGA.py — Quality Gate Determinístico (ISSUE-USA-0002 / Lei #1 + #13).

Bloqueia entrega do usuário gerada sob `<clone>/projetos/` quando existe
projeto legado irmão (a regra do livro: projeto nasce irmão do clone).

Exit 0: layout conforme.
Exit 1: layout aninhado com legado, ou helper/alias desmapeado.
"""

import os
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = Path(__file__).resolve().parent.parent


def verificar_helper_mapeado() -> list[str]:
    erros = []
    helper = ROOT_DIR / "core" / "resolve_pasta_entrega.py"
    if not helper.is_file():
        return ["core/resolve_pasta_entrega.py ausente"]
    texto = helper.read_text(encoding="utf-8", errors="ignore")
    if "def resolve_pasta_entrega" not in texto:
        erros.append("core/resolve_pasta_entrega.py: funcao resolve_pasta_entrega ausente")
    orc = ROOT_DIR / "scripts" / "orquestrador_sincrono.py"
    if not orc.is_file():
        erros.append("scripts/orquestrador_sincrono.py ausente")
    else:
        otexto = orc.read_text(encoding="utf-8", errors="ignore")
        if "resolve_pasta_entrega" not in otexto:
            erros.append(
                "scripts/orquestrador_sincrono.py nao usa resolve_pasta_entrega "
                "(default ./projetos/ ainda local)"
            )
        if re.search(r'pasta\s*=\s*f["\']\./projetos/', otexto):
            erros.append(
                "scripts/orquestrador_sincrono.py ainda atribui ./projetos/<slug> diretamente"
            )
    return erros


def verificar_docs_livro() -> list[str]:
    erros = []
    alvo = ROOT_DIR / "docs" / "livros" / "partes" / "02-fluxos.md"
    if not alvo.is_file():
        # mini-livro alternativo
        candidatos = list((ROOT_DIR / "docs" / "livros").rglob("*FLUXOS*.md")) + list(
            (ROOT_DIR / "docs" / "livros").rglob("*fluxos*.md")
        )
        if not candidatos:
            return ["docs/livros/**fluxos**.md ausente (caso 'clone dentro de projeto' nao documentado)"]
        alvo = candidatos[0]
    texto = alvo.read_text(encoding="utf-8", errors="ignore").lower()
    if "clone" not in texto or "projeto" not in texto:
        erros.append(f"{alvo.name}: caso 'clone dentro de projeto existente' nao documentado")
    return erros


def verificar_layout_sintetico() -> list[str]:
    """Detecta projetos sob projetos/ coexistindo com legado irmao (pareamento 1:1)."""
    erros = []
    raiz_ferramenta = ROOT_DIR
    # Legado irmao de projetos/: dentro da raiz (excluindo dirs da ferramenta)
    # ou no pai imediato (clone dentro de workspace do usuario).
    legados = []
    for base, desloc in ((raiz_ferramenta, "raiz"), (raiz_ferramenta.parent, "pai")):
        if not base.is_dir():
            continue
        for filho in base.iterdir():
            if filho.name == raiz_ferramenta.name or filho.name.startswith("."):
                continue
            if filho.name in DIRS_FERRAMENTA:
                continue
            if filho.is_dir() and (
                (filho / "package.json").is_file()
                or (filho / "src").is_dir()
                or (filho / "app").is_dir()
                or (filho / "backend").is_dir()
            ):
                legados.append((desloc, filho.name))

    projetos = raiz_ferramenta / "projetos"
    if not projetos.is_dir():
        return erros
    conteudo = [p for p in projetos.iterdir() if p.is_dir() and p.name != ".gitkeep"]
    if not conteudo:
        return erros

    # So reprova no pareamento 1:1 (cenario do teste de usabilidade).
    # Pai movimentado (Desktop com varios apps) nao e o caso A4.
    if len(legados) == 1:
        for item in conteudo:
            erros.append(
                f"projetos/{item.name} existe com legado irmao {legados[0][1]} "
                f"(em {legados[0][0]}) — layout aninhado proibido pela especificacao §2.2"
            )
    return erros


DIRS_FERRAMENTA = {
    "tools",
    "gates",
    "componentes",
    "scripts",
    "core",
    "docs",
    "tests",
    "testes",
}


def main() -> int:
    erros = verificar_helper_mapeado() + verificar_docs_livro() + verificar_layout_sintetico()
    if erros:
        print("=" * 70)
        print("VIOLACAO [G_LAYOUT_ENTREGA]: posicionamento de entrega fora da regra!")
        print("Regra: com legado irmao, o app nasce na raiz do workspace — nunca em projetos/.")
        print("=" * 70)
        for e in erros:
            print(f"- {e}")
        print(f"TOTAL VIOLATIONS: {len(erros)}")
        return 1
    print("[OK] G_LAYOUT_ENTREGA: helper mapeado e layout de entrega conforme.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
