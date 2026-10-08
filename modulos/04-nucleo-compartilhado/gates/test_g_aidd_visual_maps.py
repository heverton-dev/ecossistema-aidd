# -*- coding: utf-8 -*-
"""
Par de teste do Quality Gate G_aidd_visual_maps (Lei #13 - Portão Deve Provar que Morde).

O estado íntegro do repositório aprova; uma cópia com uma peça nova que o catálogo não
conhece reprova. Os demais desvios (mapa com lixo, órfão, inglês, contagem digitada,
link do manual, manifesto) estão em tests/test_g_aidd_visual_maps.py.
"""
import sys
from pathlib import Path

RAIZ = next(p.parent for p in Path(__file__).resolve().parents if p.name == "modulos")
GATE = Path("modulos") / "04-nucleo-compartilhado" / "gates" / "G_aidd_visual_maps.py"
sys.path.insert(0, str(RAIZ / "tests"))
from _repo_mapas import copiar_repo, rodar  # noqa: E402


def test_repositorio_real_aprova():
    proc = rodar(RAIZ, str(GATE))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "APROVADO" in proc.stdout


def test_gate_reprova_catalogo_desatualizado(tmp_path):
    raiz = copiar_repo(tmp_path / "repo")
    (raiz / "scripts" / "peca_nova_do_gate.py").write_text('"""Peça nova."""\n', encoding="utf-8")
    proc = rodar(raiz, str(GATE))
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "REPROVADO" in proc.stdout and "catálogo desatualizado" in proc.stdout
