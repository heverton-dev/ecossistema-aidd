#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_ZERO_EMOJIS_DOCS (Documentação Corporativa)
=============================================================================
Quality Gate e Linter Determinístico de Documentação Corporativa (Lei #4 / Lei #13).
Audita os arquivos de documentação Markdown (README.md, docs/) contra emojis.

Critérios Corporativos:
  - Documentação institucional de engenharia não deve conter emojis.
  - Emojis reduzem a credibilidade e a sobriedade corporativa da plataforma.
  - Ícones semânticos devem ser em ASCII/texto puro (ex: [OK], [AVISO], ->, |).

Critérios de Aceite:
  - Exit 0: Nenhum emoji detectado nos arquivos auditados.
  - Exit 1: Qualquer emoji detectado (bloqueio do gate).
=============================================================================
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Faixa abrangente de emojis reais (smileys, pictogramas, gestos, objetos, animais)
# Exclui deliberadamente caracteres matemáticos e setas técnicas de fluxo (->, ➔, ◄, etc.)
_RE_EMOJI_DOCS = re.compile(
    r"[\U0001F000-\U0010FFFF"
    r"\u2600-\u26FF"
    r"\u2705\u274C\u2728\u274E\u2753\u2757\u27BF"
    r"\uFE0F"
    r"]"
)

# Documentos vivos da plataforma sujeitos à auditoria
_DOCS_CANONICOS = [
    "README.md",
    "AGENTS.md",
    "GEMINI.md",
    "MEMORY.md",
    "docs/protocolos",
    "docs/manuais",
    "docs/padroes",
]

_DIRS_IGNORADAS = {
    "node_modules",
    ".git",
    ".venv",
    "venv",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
    ".worktrees",
}


def auditar_arquivo_markdown(caminho: Path) -> List[Tuple[int, str, str]]:
    """Retorna lista de (linha, emoji_encontrado, texto_da_linha) se houver emojis."""
    ocorrencias: List[Tuple[int, str, str]] = []
    try:
        conteudo = caminho.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return [(0, "ERRO_LEITURA", str(e))]

    for idx, linha in enumerate(conteudo.splitlines(), start=1):
        encontrados = _RE_EMOJI_DOCS.findall(linha)
        if encontrados:
            emoji_str = "".join(sorted(set(encontrados)))
            ocorrencias.append((idx, emoji_str, linha.strip()))

    return ocorrencias


def auditar_documentacao(diretorio_raiz: Path) -> Tuple[bool, List[str]]:
    erros: List[str] = []

    for item in _DOCS_CANONICOS:
        alvo = diretorio_raiz / item
        if alvo.is_file():
            ocorr = auditar_arquivo_markdown(alvo)
            for linha_num, emoji_char, texto in ocorr:
                rel = alvo.relative_to(diretorio_raiz)
                erros.append(f"{rel}:L{linha_num}: emoji proibido '{emoji_char}' em: {texto[:60]}")
        elif alvo.is_dir():
            for md_file in alvo.rglob("*.md"):
                if any(p in _DIRS_IGNORADAS for p in md_file.parts):
                    continue
                ocorr = auditar_arquivo_markdown(md_file)
                for linha_num, emoji_char, texto in ocorr:
                    rel = md_file.relative_to(diretorio_raiz)
                    erros.append(f"{rel}:L{linha_num}: emoji proibido '{emoji_char}' em: {texto[:60]}")

    valido = len(erros) == 0
    return valido, erros


def main() -> int:
    parser = argparse.ArgumentParser(
        description="G_ZERO_EMOJIS_DOCS: Linter de Documentação Corporativa sem Emojis"
    )
    parser.add_argument(
        "--alvo",
        default=".",
        help="Diretório raiz da auditoria (padrão: repositório atual)"
    )
    args = parser.parse_args()

    raiz = Path(args.alvo).resolve()
    valido, erros = auditar_documentacao(raiz)

    if not valido:
        print(f"[G_ZERO_EMOJIS_DOCS] FALHA: {len(erros)} emoji(s) detectado(s) em documentação corporativa:", file=sys.stderr)
        for erro in erros[:20]:
            print(f"  [X] {erro}", file=sys.stderr)
        if len(erros) > 20:
            print(f"  ... e mais {len(erros) - 20} violação(ões).", file=sys.stderr)
        return 1

    print("[G_ZERO_EMOJIS_DOCS] PASS: Documentação em conformidade corporativa (Zero Emojis).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
