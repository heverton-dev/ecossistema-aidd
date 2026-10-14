# -*- coding: utf-8 -*-
"""Ticket 9-A: tipografia, raios e espaçamentos vêm da Visual Direction, não de uma tabela por app.

A imagem do Mobbin não informa fonte, raio nem espaçamento. A spec passa a poder declarar `fonte`,
`raio` e `densidade` (opcionais); o que ela declarar vale, o que faltar fica declarado como convenção.
"""

from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core_planner import intake
from src.core_planner.design_system import gerar_design_system, tokens_da_direcao

BASE = {"tom": "sóbrio", "cor_primaria": "#0F766E", "referencias": ["Linear"], "publico": "atendentes"}


def test_sem_itens_opcionais_nada_e_derivado_e_tudo_fica_como_convencao():
    t = tokens_da_direcao(BASE)
    assert t["declarado_na_spec"] == []
    assert "tipografia" not in t and "raios_borda" not in t and "espacamentos" not in t
    assert set(t["convencao"]) == {"fonte", "raio", "densidade"}


def test_fonte_da_spec_vira_a_familia_sans_com_reserva():
    t = tokens_da_direcao({**BASE, "fonte": "Inter"})
    assert t["tipografia"]["font_sans"] == '"Inter", system-ui, sans-serif'
    assert "fonte" in t["declarado_na_spec"] and "fonte" not in t["convencao"]


@pytest.mark.parametrize("raio,btn,card", [("reto", "2px", "4px"), ("suave", "6px", "8px"), ("arredondado", "12px", "16px")])
def test_raio_da_spec_define_botao_e_card(raio, btn, card):
    t = tokens_da_direcao({**BASE, "raio": raio})
    assert t["raios_borda"] == {"btn": btn, "card": card, "pill": "9999px"}


@pytest.mark.parametrize("densidade,padding,secoes,elementos", [
    ("compacta", "16px", "24px", "8px"), ("confortavel", "24px", "32px", "16px"), ("ampla", "32px", "48px", "24px")])
def test_densidade_da_spec_define_os_espacamentos(densidade, padding, secoes, elementos):
    t = tokens_da_direcao({**BASE, "densidade": densidade})
    assert t["espacamentos"] == {"grid_base": "4px", "padding_container": padding,
                                 "gap_secoes": secoes, "gap_elementos": elementos}


def test_design_system_carrega_os_tokens_da_direcao():
    ds = gerar_design_system("App", "app", "descricao longa o bastante", "comercio",
                             direcao_visual={**BASE, "fonte": "Inter", "raio": "reto", "densidade": "compacta"})
    assert ds["tokens_da_direcao"]["tipografia"]["font_sans"].startswith('"Inter"')
    assert ds["tokens_da_direcao"]["raios_borda"]["btn"] == "2px"
    assert ds["tokens_da_direcao"]["espacamentos"]["padding_container"] == "16px"


def _spec(pasta, extras):
    destino = pasta / ".aidd" / "intake"
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "spec.md").write_text(
        "## 1. Context\ntexto\n\n### Visual Direction\n- tom: sóbrio\n- cor_primaria: #0F766E\n"
        "- referencias: Linear\n- publico: atendentes\n" + extras, encoding="utf-8")


def test_ler_direcao_visual_le_os_itens_opcionais(tmp_path):
    _spec(tmp_path, "- fonte: Inter\n- raio: reto\n- densidade: ampla\n")
    v = intake.ler_direcao_visual(str(tmp_path))
    assert (v["fonte"], v["raio"], v["densidade"]) == ("Inter", "reto", "ampla")


def test_ler_direcao_visual_sem_opcionais_nao_inventa_chaves(tmp_path):
    _spec(tmp_path, "")
    v = intake.ler_direcao_visual(str(tmp_path))
    assert not {"fonte", "raio", "densidade"} & set(v)


@pytest.mark.parametrize("extras,trecho", [
    ("- raio: quadrado\n", "raio"),
    ("- densidade: apertada\n", "densidade"),
    ("- fonte: Inter; DROP\n", "fonte"),
])
def test_valores_opcionais_invalidos_reprovam_a_verificacao(tmp_path, extras, trecho):
    _spec(tmp_path, extras)
    erros = intake.erros_do_bloco_visual(intake.caminhos(str(tmp_path))["spec"].read_text(encoding="utf-8"))
    assert any(trecho in e for e in erros)
