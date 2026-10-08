# -*- coding: utf-8 -*-
"""
Autocontenção Fractal e Verificação de Submódulos (VSA).
Dimensão D4: Componentes e Fractalidade.

Decisão do usuário (08/10, ciclo-03 Bloco 7): a fatia exige sempre AGENTS.md e README.md
na raiz, dentro do orçamento de tokens, e testes em algum ponto da fatia. As pastas
core/, skills/ e gates/ só existem quando a fatia tem esse conteúdo (sem pasta vazia).
"""

from pathlib import Path
from typing import List, Tuple

LIMITE_TOKENS_AGENTS = 400
LIMITE_TOKENS_README = 500
ARQUIVOS_OBRIGATORIOS = {"AGENTS.md": LIMITE_TOKENS_AGENTS, "README.md": LIMITE_TOKENS_README}
PASTAS_IGNORADAS = {"node_modules", ".venv", "venv", "__pycache__", ".git"}


def estimar_tokens(texto: str) -> int:
    palavras = len(texto.split())
    return int(palavras * 1.3)


def _tem_pasta_de_testes(caminho: Path) -> bool:
    for alvo in caminho.rglob("tests"):
        if alvo.is_dir() and not PASTAS_IGNORADAS.intersection(alvo.relative_to(caminho).parts):
            return True
    return False


def validar_fractalidade_slice(caminho_slice: Path) -> Tuple[bool, List[str]]:
    erros: List[str] = []
    caminho = Path(caminho_slice).resolve()

    if not caminho.exists() or not caminho.is_dir():
        return False, [f"Caminho do slice '{caminho}' não existe ou não é diretório."]

    for nome, limite in ARQUIVOS_OBRIGATORIOS.items():
        arquivo = caminho / nome
        if not arquivo.is_file():
            erros.append(f"Elemento obrigatório ausente no slice: {nome}")
            continue
        tokens = estimar_tokens(arquivo.read_text(encoding="utf-8", errors="replace"))
        if tokens >= limite:
            erros.append(
                f"{nome} excede orçamento de tokens: {tokens} tokens estimados "
                f"(máximo permitido: {limite - 1})"
            )

    if not _tem_pasta_de_testes(caminho):
        erros.append("Elemento obrigatório ausente no slice: tests (nenhuma pasta tests/ na fatia)")

    return len(erros) == 0, erros
