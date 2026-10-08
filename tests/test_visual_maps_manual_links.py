# -*- coding: utf-8 -*-
"""
aidd-visual-maps ciclo-01, Ticket 8 (D9): o manual de montagem liga todos os mapas.

Achado N1 do laudo: o manual não tinha link para mapa-10-scripts.html, e a SKILL dizia
"The assembly manual links every map". A lista esperada vem de MAPAS_PREVISTOS + índice
(links_faltando_no_manual), então os mapas novos do Ticket 5 também são exigidos, no
manual técnico e no par não técnico.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
MAPAS = ROOT / "docs" / "mapas-visuais"
sys.path.insert(0, str(ROOT / "scripts"))

import mapa_visual as mv  # noqa: E402


@pytest.mark.parametrize("manual", ["manual-montagem-aidd.html", "nao-tecnicos/manual-montagem-aidd.html"])
def test_manual_tem_link_para_cada_mapa_previsto_e_o_indice(manual):
    faltando = mv.links_faltando_no_manual((MAPAS / manual).read_text(encoding="utf-8"))
    assert not faltando, f"{manual} sem link para: {faltando}"


def test_detector_acusa_link_apagado():
    texto = (MAPAS / "manual-montagem-aidd.html").read_text(encoding="utf-8")
    alvo = mv.arquivo_mapa("scripts")
    sem_link = texto.replace(f'href="{alvo}"', 'href="#"')
    assert mv.links_faltando_no_manual(sem_link) == [alvo]
    esperados = {mv.arquivo_mapa("indice"), *(mv.arquivo_mapa(t) for t, _, _ in mv.MAPAS_PREVISTOS)}
    assert set(mv.links_faltando_no_manual("")) == esperados
