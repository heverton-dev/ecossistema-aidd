# -*- coding: utf-8 -*-
"""
aidd-visual-maps ciclo-01, Ticket 14 (D15): manifesto dos mapas e handoff ao livro.

Antes, o fim do pipeline não deixava registro do que foi entregue: nenhum arquivo dizia
com qual catálogo cada mapa foi gerado, nem passava as partes do livro ao aidd-textbook
(a compilação era passo manual). Agora `visual-maps gerar` termina chamando o build do
aidd-textbook e grava docs/mapas-visuais/MANIFESTO-MAPAS.json (sem data/hora), e o
`visual-maps check` confere o hash de cada arquivo contra ele.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_mapas import commitar, copiar_repo, rodar  # noqa: E402

CLI = "componentes/compartilhado/skills/aidd-visual-maps/scripts/cli.py"
MANIFESTO = "docs/mapas-visuais/MANIFESTO-MAPAS.json"
CATALOGO = "docs/auditoria/mapa-pecas/catalogo-pecas.json"
LIVRO = "docs/livros/mapas-aidd"
CONFERIR = ("import sys; sys.path.insert(0, 'componentes/compartilhado/skills/aidd-visual-maps/scripts');"
            "import handoff; print('\\n'.join(handoff.conferir_manifesto()))")


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def repo(tmp_path_factory):
    raiz = copiar_repo(tmp_path_factory.mktemp("repo_manifesto"))
    commitar(raiz, ".", mensagem="fixture")
    proc = rodar(raiz, CLI, "gerar", env={"AIDD_MEDICOES_DIR": str(raiz.parent / "medicoes")})
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return raiz


def test_manifesto_registra_catalogo_mapas_e_livro(repo):
    texto = (repo / MANIFESTO).read_text(encoding="utf-8")
    assert not re.search(r"\d{4}-\d{2}-\d{2}|\d{2}:\d{2}:\d{2}", texto), "manifesto não pode ter data/hora"
    manifesto = json.loads(texto)
    assert manifesto["hash_catalogo"] == _sha(repo / CATALOGO)

    mapas = manifesto["mapas"]
    assert {m["versao"] for m in mapas} == {"tecnica", "nao-tecnica"}
    assert any(m["arquivo"].endswith("mapa-00-indice.html") for m in mapas)
    for m in mapas:
        assert {"arquivo", "versao", "sha256", "status"} <= set(m)
        assert m["sha256"] == _sha(repo / m["arquivo"]), m["arquivo"]
        assert m["status"] == "concluido", m

    handoff = manifesto["handoff_livro"]
    assert handoff["skill"] == "aidd-textbook" and handoff["pasta"] == LIVRO
    partes = json.loads((repo / LIVRO / "livro.json").read_text(encoding="utf-8"))["partes"]
    assert [Path(p["arquivo"]).name for p in handoff["partes"]] == partes
    for p in handoff["partes"]:
        assert p["sha256"] == _sha(repo / p["arquivo"])
    assert handoff["build"]["exit_code"] == 0, handoff["build"]
    assert handoff["build"]["sha256"] == _sha(repo / handoff["build"]["pdf"])


def test_check_confere_manifesto_e_morde_byte_trocado(repo):
    ok = rodar(repo, CLI, "check")
    assert ok.returncode == 0, ok.stdout + ok.stderr
    assert rodar(repo, "-c", CONFERIR).stdout.strip() == ""

    pdf = repo / json.loads((repo / MANIFESTO).read_text(encoding="utf-8"))["handoff_livro"]["build"]["pdf"]
    original_pdf = pdf.read_bytes()
    pdf.write_bytes(original_pdf[:-1] + bytes([original_pdf[-1] ^ 1]))
    try:
        assert pdf.name in rodar(repo, "-c", CONFERIR).stdout
        reprovado = rodar(repo, CLI, "check")
        assert reprovado.returncode == 1 and "MANIFESTO" in reprovado.stdout, reprovado.stdout
    finally:
        pdf.write_bytes(original_pdf)

    mapa = repo / "docs" / "mapas-visuais" / "mapa-01-leis.html"
    original = mapa.read_bytes()
    mapa.write_bytes(original[:-2] + bytes([original[-2] ^ 1]) + original[-1:])
    try:
        assert "mapa-01-leis.html" in rodar(repo, "-c", CONFERIR).stdout
        assert rodar(repo, CLI, "check").returncode == 1
    finally:
        mapa.write_bytes(original)
