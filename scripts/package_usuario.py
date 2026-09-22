# -*- coding: utf-8 -*-
"""Empacota o núcleo de distribuição para o usuário final (ISSUE-USA-0006).

Uso:
    python scripts/package_usuario.py [--outdir dist]
    python ecossistema.py package --perfil usuario [--outdir dist]

Gera dist/ecossistema-aidd-usuario.zip (ou instruções git archive) contendo
apenas o núcleo: sem tests, *.db, requirements-dev*, docs/relatorios, docs/livros.
"""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

INCLUDE_DIRS = [
    "gates",
    "core",
    "componentes",
    "scripts",
    "tools",
    "docs/protocolos",
    "docs/glossario",
    "docs/issues",
    "docs/melhorias",
    "docs/teste-end-to-end",
    "docs/testes",
    "docs/planos",
    "docs/features",
    "docs/protocolos",
]
INCLUDE_FILES = [
    "ecossistema.py",
    "requirements.txt",
    "README.md",
    "LICENSE",
    "AGENTS.md",
    "GEMINI.md",
    "MEMORY.md",
]
# Também sobem schemas/docs vivos já cobertos por docs/protocolos.

EXCLUDE_NAME = {
    "__pycache__",
    ".pytest_cache",
    ".git",
    ".venv",
    "venv",
    "node_modules",
    ".worktrees",
    ".ade_tmp",
    "testes",
    "tests",
}
EXCLUDE_SUFFIX = (".db", ".pyc", ".pyo")
EXCLUDE_PREFIX = ("requirements-dev",)
EXCLUDE_RELS = (
    "PLANO-EXECUCAO-ESTRUTURADO.json",
    ".pre-commit-config.yaml",
    ".secrets.baseline",
    "pytest.ini",
)


def _deve_pular(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    partes = rel.parts
    for p in partes:
        if p in EXCLUDE_NAME:
            return True
    if path.name in ("pytest.ini", "PLANO-EXECUCAO-ESTRUTURADO.json",
                     ".pre-commit-config.yaml", ".secrets.baseline"):
        return True
    if path.suffix in EXCLUDE_SUFFIX:
        return True
    if any(path.name.startswith(pref) for pref in EXCLUDE_PREFIX):
        return True
    if "relatorios" in partes or "reports" in partes:
        # docs/livros e docs/relatorios ficam fora do pacote de usuário
        if "docs" in partes and partes[partes.index("docs") + 1:partes.index("docs") + 2] in (
            ("relatorios",), ("reports",), ("livros",),
        ):
            return True
    if len(partes) >= 2 and partes[0] == "docs" and partes[1] in ("relatorios", "reports", "livros"):
        return True
    return False


def empacotar(outdir: Path) -> Path:
    outdir.mkdir(parents=True, exist_ok=True)
    nome = "ecossistema-aidd-usuario.zip"
    alvo = outdir / nome

    with zipfile.ZipFile(alvo, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        contagem = 0
        itens = list(INCLUDE_FILES)
        for d in INCLUDE_DIRS:
            base = ROOT / d
            if base.is_file():
                itens.append(d)
            elif base.is_dir():
                for p in base.rglob("*"):
                    if p.is_file() and not _deve_pular(p):
                        itens.append(str(p.relative_to(ROOT)))
        for item in sorted(set(itens)):
            path = ROOT / item
            if not path.is_file() or _deve_pular(path):
                continue
            zf.write(path, arcname=f"ecossistema-aidd-usuario/{item}")
            contagem += 1
    print(f"[OK] Pacote usuario: {alvo} ({contagem} arquivos)")
    return alvo


def main() -> int:
    ap = argparse.ArgumentParser(description="Package core enxuto (perfil usuario)")
    ap.add_argument("--outdir", default="dist", help="Diretorio de saida")
    ap.add_argument("--perfil", default="usuario", choices=["usuario"], help="Perfil de distribuicao")
    args = ap.parse_args()
    empacotar(ROOT / args.outdir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
