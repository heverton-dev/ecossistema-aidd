#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Leitor único do mapa de donos dos gates (ciclo-03 VSA, decisão C).

Fonte: modulos/04-nucleo-compartilhado/contracts/MAPA-GATES.json
  gates.<G_NOME>.dono          fatia dona (pasta sob modulos/)
  gates.<G_NOME>.transversal   true = vale para o ecossistema inteiro (dono = 04-nucleo)
  gates.<G_NOME>.caminho       onde o gate está hoje (o que runners e hooks executam)
  gates.<G_NOME>.caminho_final modulos/<dono>/gates/<G_NOME>.py

O .pre-commit-config.yaml é estático; ele "lê" o mapa por sincronização:
  python scripts/mapa_gates.py verificar    -> exit 1 se algum entry diverge do mapa
  python scripts/mapa_gates.py sincronizar  -> reescreve os entries pelo mapa
  python scripts/mapa_gates.py caminho G_X  -> imprime o caminho vigente do gate
"""

import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
MAPA_REL = Path("modulos") / "04-nucleo-compartilhado" / "contracts" / "MAPA-GATES.json"
PRECOMMIT = ".pre-commit-config.yaml"
_ENTRY = re.compile(r"(entry:\s*python\s+)(\S*?(G_\w+)\.py)")


def carregar(raiz: Path | None = None) -> dict:
    """Devolve {G_NOME: info} do mapa."""
    arquivo = Path(raiz or RAIZ) / MAPA_REL
    return json.loads(arquivo.read_text(encoding="utf-8"))["gates"]


def caminho(nome: str, raiz: Path | None = None) -> Path:
    """Caminho absoluto vigente do gate. KeyError se o gate não está no mapa."""
    base = Path(raiz or RAIZ)
    return base / carregar(base)[nome]["caminho"]


def caminhos(raiz: Path | None = None) -> list[Path]:
    """Caminhos absolutos vigentes de todos os gates do mapa, em ordem de nome."""
    base = Path(raiz or RAIZ)
    return [base / info["caminho"] for _, info in sorted(carregar(base).items())]


def verificar_precommit(raiz: Path | None = None, mapa: dict | None = None) -> list[str]:
    """Lista os entries do pre-commit que não batem com o caminho do mapa."""
    base = Path(raiz or RAIZ)
    mapa = mapa if mapa is not None else carregar(base)
    texto = (base / PRECOMMIT).read_text(encoding="utf-8")
    erros = []
    for m in _ENTRY.finditer(texto):
        nome, atual = m.group(3), m.group(2)
        if nome not in mapa:
            erros.append(f"{nome}: fora do mapa ({atual})")
        elif atual != mapa[nome]["caminho"]:
            erros.append(f"{nome}: pre-commit aponta {atual}, mapa diz {mapa[nome]['caminho']}")
    return erros


def sincronizar_precommit(raiz: Path | None = None, mapa: dict | None = None) -> int:
    """Reescreve cada entry de gate com o caminho do mapa. Devolve quantos mudaram."""
    base = Path(raiz or RAIZ)
    mapa = mapa if mapa is not None else carregar(base)
    arquivo = base / PRECOMMIT
    texto = arquivo.read_text(encoding="utf-8")
    trocas = 0

    def _trocar(m: re.Match) -> str:
        nonlocal trocas
        novo = mapa.get(m.group(3), {}).get("caminho", m.group(2))
        trocas += novo != m.group(2)
        return m.group(1) + novo

    novo_texto = _ENTRY.sub(_trocar, texto)
    if trocas:
        with open(arquivo, "w", encoding="utf-8", newline="\n") as f:
            f.write(novo_texto)
    return trocas


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in ("verificar", "sincronizar", "caminho"):
        print("Uso: python scripts/mapa_gates.py verificar|sincronizar|caminho G_NOME")
        return 1
    try:
        if argv[0] == "caminho":
            print(caminho(argv[1]).relative_to(RAIZ).as_posix())
            return 0
        if argv[0] == "sincronizar":
            print(f"[mapa_gates] {sincronizar_precommit()} entry(s) atualizado(s) no {PRECOMMIT}.")
            return 0
        erros = verificar_precommit()
    except (OSError, KeyError, IndexError, ValueError) as erro:
        print(f"[mapa_gates] ERRO: {erro!r}")
        return 1
    for e in erros:
        print(f"  - {e}")
    print(f"[mapa_gates] {len(erros)} divergência(s) entre {PRECOMMIT} e o mapa.")
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
