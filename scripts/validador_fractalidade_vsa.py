# -*- coding: utf-8 -*-
"""
Autocontenção Fractal e Verificação de Submódulos (VSA).
Dimensão D4: Componentes e Fractalidade.
"""

from pathlib import Path
from typing import List, Tuple

LIMITE_TOKENS_README = 500
ELEMENTOS_OBRIGATORIOS = ("core", "skills", "gates", "tests", "README.md")


def estimar_tokens(texto: str) -> int:
    palavras = len(texto.split())
    return int(palavras * 1.3)


def validar_fractalidade_slice(caminho_slice: Path) -> Tuple[bool, List[str]]:
    erros: List[str] = []
    caminho = Path(caminho_slice).resolve()

    if not caminho.exists() or not caminho.is_dir():
        return False, [f"Caminho do slice '{caminho}' não existe ou não é diretório."]

    for elemento in ELEMENTOS_OBRIGATORIOS:
        alvo = caminho / elemento
        if not alvo.exists():
            erros.append(f"Elemento obrigatório ausente no slice: {elemento}")

    readme = caminho / "README.md"
    if readme.exists() and readme.is_file():
        conteudo = readme.read_text(encoding="utf-8", errors="replace")
        tokens = estimar_tokens(conteudo)
        if tokens > LIMITE_TOKENS_README:
            erros.append(
                f"README.md excede orçamento de tokens: {tokens} tokens estimados "
                f"(máximo permitido: {LIMITE_TOKENS_README})"
            )

    return len(erros) == 0, erros
