# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — GERADOR DETERMINISTICO DO LIVRO (pandoc + typst)
=============================================================================
Concatena as partes em docs/livros/partes/ na ordem canonica, gera o Markdown
unico e compila o PDF corporativo via pandoc --pdf-engine=typst com o template
docs/livros/livro-aidd.typst.

Uso:
  python docs/livros/build_livro.py
  python docs/livros/build_livro.py --somente-md
  python docs/livros/build_livro.py --png   # renderiza paginas em PNG p/ inspecao

Exit: 0 = sucesso, 1 = falha real (nao mascara erro do pandoc/typst).
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

DIR_LIVROS = Path(__file__).resolve().parent
DIR_PARTES = DIR_LIVROS / "partes"
TEMPLATE = DIR_LIVROS / "livro-aidd.typst"

ORDEM_PARTES = (
    "00-frontmatter.md",
    "01-macro.md",
    "02-fluxos.md",
    "03-ferramentas-a.md",
    "04-ferramentas-b.md",
    "05-transversais.md",
    "06-apendices.md",
)

NOME_BASE = "21-09-2026_LIVRO-ECOSSISTEMA-AIDD"


def verificar_ferramentas() -> bool:
    """Confere que pandoc e typst existem no PATH antes de tentar gerar."""
    faltando = [b for b in ("pandoc", "typst") if shutil.which(b) is None]
    if faltando:
        print(f"[ERRO] Binarios ausentes no PATH: {', '.join(faltando)}")
        return False
    return True


def montar_markdown() -> Path:
    """Concatena as partes na ordem canonica e grava o Markdown unico."""
    partes = []
    for nome in ORDEM_PARTES:
        caminho = DIR_PARTES / nome
        if not caminho.is_file():
            raise FileNotFoundError(f"Parte ausente: {caminho}")
        partes.append(caminho.read_text(encoding="utf-8").rstrip())

    destino = DIR_LIVROS / f"{NOME_BASE}.md"
    destino.write_text("\n\n".join(partes) + "\n", encoding="utf-8")
    return destino


def compilar_pdf(markdown: Path) -> int:
    """Compila o PDF via pandoc + typst. Retorna o exit code real do pandoc."""
    pdf = DIR_LIVROS / f"{NOME_BASE}.pdf"
    cmd = [
        "pandoc", str(markdown),
        "--from", "markdown+raw_attribute+pipe_tables+yaml_metadata_block",
        "--pdf-engine", "typst",
        "--template", str(TEMPLATE),
        "--columns", "72",
        "-o", str(pdf),
    ]
    resultado = subprocess.run(cmd, capture_output=True, text=True)
    if resultado.returncode != 0:
        print("[ERRO] pandoc/typst falhou:")
        print(resultado.stderr[-4000:])
        return resultado.returncode
    print(f"[OK] PDF gerado: {pdf}  ({pdf.stat().st_size / 1024:.1f} KB)")
    return 0


def renderizar_png(markdown: Path) -> int:
    """Gera .typ intermediario e renderiza paginas em PNG para inspecao visual."""
    typ = DIR_LIVROS / f"{NOME_BASE}.typ"
    cmd_typ = [
        "pandoc", str(markdown),
        "--from", "markdown+raw_attribute+pipe_tables+yaml_metadata_block",
        "-t", "typst", "-s",
        "--template", str(TEMPLATE),
        "--columns", "72",
        "-o", str(typ),
    ]
    res = subprocess.run(cmd_typ, capture_output=True, text=True)
    if res.returncode != 0:
        print(res.stderr[-3000:])
        return res.returncode

    saida_png = DIR_LIVROS / "preview"
    saida_png.mkdir(exist_ok=True)
    res = subprocess.run(
        ["typst", "compile", "--format", "png", "--ppi", "90",
         str(typ), str(saida_png / "pagina{n}.png")],
        capture_output=True, text=True,
    )
    if res.returncode != 0:
        print(res.stderr[-3000:])
        return res.returncode
    print(f"[OK] PNGs em {saida_png}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera o livro do Ecossistema AIDD")
    parser.add_argument("--somente-md", action="store_true", help="Só concatena o Markdown")
    parser.add_argument("--png", action="store_true", help="Renderiza páginas em PNG")
    args = parser.parse_args()

    if not verificar_ferramentas():
        return 1

    markdown = montar_markdown()
    linhas = len(markdown.read_text(encoding="utf-8").splitlines())
    print(f"[OK] Markdown montado: {markdown} ({linhas} linhas)")

    if args.somente_md:
        return 0
    if args.png:
        return renderizar_png(markdown)
    return compilar_pdf(markdown)


if __name__ == "__main__":
    sys.exit(main())
