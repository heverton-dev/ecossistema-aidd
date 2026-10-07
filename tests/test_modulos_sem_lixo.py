# -*- coding: utf-8 -*-
"""
Ticket 6 (modularizacao-vsa ciclo-03, D4 / DoD 2): modulos/ nao versiona lixo.

Reprova se o git rastrear dentro de modulos/:
- sobra de teste e cache (sandbox-forge-teste/, _destino_teste*/, .aidd/cache/);
- registro de sessao fora de docs/secoes (secoes/);
- material de pesquisa arquivado (materiais-extras/);
- artefato de build ou banco (*.egg-info, *.db-wal, *.db-shm);
- pasta casca cujo unico arquivo e __init__.py (voltam quando tiverem codigo real).
"""
import re
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

LIXO = re.compile(
    r"(^|/)(sandbox-forge-teste|secoes|_destino_teste[^/]*|materiais-extras|[^/]+\.egg-info|\.aidd/cache)/"
    r"|\.db-(wal|shm)$"
)


def _rastreados():
    saida = subprocess.run(
        ["git", "ls-files", "-z", "modulos"], cwd=RAIZ, capture_output=True, check=True
    ).stdout
    return [c for c in saida.decode("utf-8").split("\0") if c]


def _cascas(arquivos):
    por_pasta = {}
    for arquivo in arquivos:
        partes = arquivo.split("/")
        for i in range(1, len(partes)):
            por_pasta.setdefault("/".join(partes[:i]), []).append(arquivo)
    return sorted(
        pasta for pasta, dentro in por_pasta.items()
        if len(dentro) == 1 and dentro[0] == pasta + "/__init__.py"
    )


def test_modulos_nao_versiona_lixo():
    sobra = [c for c in _rastreados() if LIXO.search(c)]
    assert not sobra, f"{len(sobra)} arquivo(s) de lixo em modulos/, ex.: {sobra[:10]}"


def test_modulos_sem_pasta_casca():
    cascas = _cascas(_rastreados())
    assert not cascas, f"{len(cascas)} pasta(s) com so __init__.py: {cascas}"


def test_gitignore_barra_o_lixo_de_volta():
    regras = (RAIZ / ".gitignore").read_text(encoding="utf-8")
    for padrao in ("sandbox-forge-teste/", "_destino_teste*/", "materiais-extras/", "modulos/**/.aidd/cache/"):
        assert padrao in regras, f".gitignore sem {padrao}"
