#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G_PACOTE_CORE.py — Quality Gate Determinístico (ISSUE-USA-0006 / Lei #1 + #13).

Falha se a árvore de distribuição (export / pacote usuário) contiver artefatos
dev-only: *.db, requirements-dev*, docs/relatorios/.

Exit 0: pacote limpo.
Exit 1: sujeira dev-only no escopo de distribuição.
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent

ALVOS = [
    ROOT / "ecossistema.py",
    ROOT / "gates",
    ROOT / "core",
    ROOT / "componentes",
    ROOT / "scripts",
    ROOT / "docs" / "protocolos",
]

PROIBIDOS_NOME = {
    "requirements-dev.txt",
    "requirements-dev.lock",
    "pytest.ini",
    "PLANO-EXECUCAO-ESTRUTURADO.json",
    ".pre-commit-config.yaml",
    ".secrets.baseline",
}
PROIBIDOS_SUFFIX = (".db",)
DIRS_PROIBIDAS = {"relatorios", "reports"}


def _iter_arquivos():
    for alvo in ALVOS:
        if alvo.is_file():
            yield alvo
        elif alvo.is_dir():
            for p in alvo.rglob("*"):
                if p.is_file():
                    yield p


def verificar() -> list[str]:
    erros = []
    for path in _iter_arquivos():
        if path.suffix in PROIBIDOS_SUFFIX:
            erros.append(f"{path.relative_to(ROOT)}: *.db não pode entrar no pacote")
        if path.name in PROIBIDOS_NOME:
            erros.append(f"{path.relative_to(ROOT)}: artefato dev-only no escopo core")
        partes = path.relative_to(ROOT).parts
        if "docs" in partes:
            i = partes.index("docs")
            if i + 1 < len(partes) and partes[i + 1] in DIRS_PROIBIDAS:
                erros.append(f"{path.relative_to(ROOT)}: docs de histórico fora do pacote")
    # export-ignore presente?
    ga = ROOT / ".gitattributes"
    if not ga.is_file() or "export-ignore" not in ga.read_text(encoding="utf-8", errors="ignore"):
        erros.append(".gitattributes: bloco export-ignore (ISSUE-USA-0006) ausente")
    # package_usuario presente?
    if not (ROOT / "scripts" / "package_usuario.py").is_file():
        erros.append("scripts/package_usuario.py ausente")
    return erros


def main() -> int:
    erros = verificar()
    if erros:
        print("=" * 70)
        print("VIOLACAO [G_PACOTE_CORE]: artefato dev-only no escopo de distribuicao!")
        print("=" * 70)
        for e in erros:
            print(f"- {e}")
        print(f"TOTAL VIOLATIONS: {len(erros)}")
        return 1
    print("[OK] G_PACOTE_CORE: escopo core livre de *.db, dev-requirements e historicos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
