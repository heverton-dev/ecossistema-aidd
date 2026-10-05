# -*- coding: utf-8 -*-
"""
Tratamento de exceções, resolução de colisões e recuperação resiliente para aidd-plan (D11).
"""

from pathlib import Path
import re


def resolver_colisao_pasta(caminho_pasta: Path | str) -> Path:
    p = Path(caminho_pasta).resolve()
    if not p.exists():
        return p

    contador = 2
    while True:
        candidato = p.parent / f"{p.name}-{contador}"
        if not candidato.exists():
            return candidato
        contador += 1


def corrigir_cercas_aninhadas(conteudo_md: str) -> str:
    """Detecta cercas aninhadas e substitui a cerca externa por ~~~."""
    linhas = conteudo_md.splitlines(keepends=True)
    pilha_cercas = []
    indices_abertura = []

    for idx, linha in enumerate(linhas):
        linha_strip = linha.strip()
        if linha_strip.startswith("```"):
            if not pilha_cercas:
                pilha_cercas.append("```")
                indices_abertura.append(idx)
            else:
                # Possível aninhamento
                pilha_cercas.pop()

    # Se houve mais aberturas que fechamentos ou sobreposição, alternar para ~~~
    if "```" in conteudo_md and conteudo_md.count("```") > 2:
        # Se houver cerca dentro de bloco de código, converte cerca mais externa
        return re.sub(r"^```(\w*)", r"~~~\1", conteudo_md, flags=re.MULTILINE)

    return conteudo_md
