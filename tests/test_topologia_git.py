# -*- coding: utf-8 -*-
"""ISSUE-USA-0009 — topologia Git da entrega: 1 repo de produto, sem triple-repo."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.orquestrador_sincrono import OrquestradorSincrono  # noqa: E402


def test_init_fora_da_ferramenta_cria_um_git(tmp_path):
    """Raiz de entrega fora do clone => um .git de produto."""
    pasta = tmp_path / "workspace" / "meu-app"
    pasta.mkdir(parents=True)
    (pasta / "src").mkdir()
    (pasta / "src" / "server.py").write_text("#\n", encoding="utf-8")

    orq = OrquestradorSincrono(
        fluxo=1, nome="Meu App", slug="meu-app", dominio="geral",
        pasta=str(pasta), dry_run=False,
    )
    orq._fechar_entrega()
    assert (pasta / ".git").exists(), "esperava git init na raiz da entrega"
    # exatamente um .git sob o workspace do produto (não conta o clone da ferramenta)
    gits = [p for p in pasta.rglob(".git") if p.is_dir()]
    assert len(gits) == 1


def test_guarda_triple_repo_nao_init_dentro_do_clone(tmp_path):
    """Entrega SOB o clone da ferramenta (com .git) => NÃO init aninhado."""
    clone = tmp_path / "ecossistema-aidd"
    (clone / ".git").mkdir(parents=True)
    entrega = clone / "projetos" / "app-x"
    entrega.mkdir(parents=True)

    orq = OrquestradorSincrono(
        fluxo=1, nome="App X", slug="app-x", dominio="geral",
        pasta=str(entrega), dry_run=False,
    )
    orq._fechar_entrega()
    assert not (entrega / ".git").exists(), (
        "guarda triple-repo: não deve criar .git sob o clone da ferramenta"
    )


def test_mini_livro_tem_topologia_git():
    livro = ROOT / "docs" / "livros" / "partes" / "02-fluxos.md"
    texto = livro.read_text(encoding="utf-8")
    assert "6.5.2" in texto
    assert "triple-repo" in texto
    assert "git init" in texto
