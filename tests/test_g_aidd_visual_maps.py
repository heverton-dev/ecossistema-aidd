# -*- coding: utf-8 -*-
"""
aidd-visual-maps ciclo-01, Ticket 15 (D13): portão G_aidd_visual_maps no pre-commit.

Antes, os desvios que o ciclo corrigiu (catálogo velho, mapa com lixo, HTML órfão, inglês
no mapa não técnico, contagem digitada no molde, link faltando no manual, manifesto
divergente) só eram pegos por testes soltos. Agora um portão só junta as conferências e
reprova cada um, com um motivo por linha. Cada cenário quebra uma cópia do repositório
já em dia (`visual-maps gerar`) e restaura depois.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_mapas import commitar, copiar_repo, rodar  # noqa: E402

GATE = "modulos/04-nucleo-compartilhado/gates/G_aidd_visual_maps.py"
CLI = "componentes/compartilhado/skills/aidd-visual-maps/scripts/cli.py"
MAPAS = Path("docs/mapas-visuais")


import shutil


@pytest.fixture(scope="module")
def repo(tmp_path_factory, repo_mapas_gerado_sessao):
    destino = tmp_path_factory.mktemp("repo_gate_vmaps") / "repo"
    shutil.copytree(repo_mapas_gerado_sessao, destino)
    return destino



def _script_novo(raiz: Path):
    (raiz / "scripts" / "peca_nova_do_gate.py").write_text('"""Peça que o catálogo não conhece."""\n', encoding="utf-8")


def _lixo_no_mapa(raiz: Path):
    (raiz / MAPAS / "mapa-01-leis.html").write_text("<html>lixo</html>\n", encoding="utf-8")


def _orfao(raiz: Path):
    (raiz / MAPAS / "sobra-sem-dono.html").write_text("<html></html>\n", encoding="utf-8")


def _ingles(raiz: Path):
    arquivo = raiz / MAPAS / "nao-tecnicos" / "mapa-05-skills.html"
    arquivo.write_text(arquivo.read_text(encoding="utf-8") + "<p>Use when the user asks.</p>\n", encoding="utf-8")


def _contagem(raiz: Path):
    arquivo = raiz / MAPAS / "moldes" / "leis.html"
    arquivo.write_text(arquivo.read_text(encoding="utf-8") + "<p>as 13 leis</p>\n", encoding="utf-8")


def _link_manual(raiz: Path):
    arquivo = raiz / MAPAS / "manual-montagem-aidd.html"
    texto = arquivo.read_text(encoding="utf-8")
    assert 'href="mapa-10-scripts.html"' in texto
    arquivo.write_text(texto.replace('href="mapa-10-scripts.html"', 'href="#"'), encoding="utf-8")


def _manifesto(raiz: Path):
    arquivo = raiz / MAPAS / "MANIFESTO-MAPAS.json"
    dados = json.loads(arquivo.read_text(encoding="utf-8"))
    dados["hash_catalogo"] = "0" * 64
    arquivo.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


CENARIOS = {
    "catalogo_velho": (_script_novo, "catálogo desatualizado"),
    "lixo_no_mapa": (_lixo_no_mapa, "mapa-01-leis.html"),
    "html_orfao": (_orfao, "órfão: sobra-sem-dono.html"),
    "ingles_no_nao_tecnico": (_ingles, "inglês"),
    "contagem_digitada": (_contagem, "contagem digitada"),
    "link_faltando_no_manual": (_link_manual, "manual sem link para mapa-10-scripts.html"),
    "manifesto_divergente": (_manifesto, "hash_catalogo"),
}


def test_repositorio_em_dia_aprova(repo):
    proc = rodar(repo, GATE)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "APROVADO" in proc.stdout


@pytest.mark.parametrize("cenario", sorted(CENARIOS))
def test_gate_reprova_cada_desvio(repo, cenario):
    quebrar, motivo = CENARIOS[cenario]
    antes = {p: p.read_bytes() for p in [*(repo / MAPAS).rglob("*"), *(repo / "scripts").glob("*.py")] if p.is_file()}
    quebrar(repo)
    try:
        proc = rodar(repo, GATE)
        assert proc.returncode == 1, proc.stdout + proc.stderr
        assert "REPROVADO" in proc.stdout and motivo in proc.stdout, proc.stdout
    finally:
        for p in [*(repo / MAPAS).rglob("*"), *(repo / "scripts").glob("*.py")]:
            if p.is_file() and p not in antes:
                p.unlink()
        for p, dados in antes.items():
            p.write_bytes(dados)
    assert rodar(repo, GATE).returncode == 0
