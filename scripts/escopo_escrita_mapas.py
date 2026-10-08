#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Escopo de escrita dos mapas visuais (aidd-visual-maps, D3 / DoD 2).

garantir_escopo(caminho) aceita só:
  - dentro do repositório: docs/mapas-visuais/, docs/auditoria/mapa-pecas/ e
    docs/livros/mapas-aidd/ (o que o catálogo, os mapas e o livro produzem);
  - fora do repositório: o diretório temporário do sistema (tempfile.gettempdir()),
    onde ficam as saídas de teste e as worktrees efêmeras.
Uma worktree efêmera roda os próprios scripts, então a raiz dela é o "repositório" e as
mesmas três pastas valem lá dentro. Qualquer outro destino (AGENTS.md, scripts/, outra
pasta de docs/, ou um caminho que escape com '..') levanta ForaDoEscopo, que os scripts
transformam em linha [ERRO] e exit 1 sem tocar no arquivo.
"""
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTAS_PERMITIDAS = ("docs/mapas-visuais", "docs/auditoria/mapa-pecas", "docs/livros/mapas-aidd")


class ForaDoEscopo(ValueError):
    """Destino de escrita fora das pastas dos mapas e do diretório temporário."""


def _dentro(caminho: Path, base: Path) -> bool:
    return caminho == base or base in caminho.parents


def garantir_escopo(caminho: Path) -> Path:
    """Devolve o caminho resolvido se ele pode ser gravado; senão levanta ForaDoEscopo."""
    alvo = Path(caminho).resolve()
    if _dentro(alvo, RAIZ):
        if any(_dentro(alvo, RAIZ / pasta) for pasta in PASTAS_PERMITIDAS):
            return alvo
    elif _dentro(alvo, Path(tempfile.gettempdir()).resolve()):
        return alvo
    raise ForaDoEscopo(f"escrita fora do escopo: {alvo} (permitido: {', '.join(PASTAS_PERMITIDAS)} "
                       f"ou o diretório temporário)")
