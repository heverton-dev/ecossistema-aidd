# -*- coding: utf-8 -*-
"""
Ticket 19 (ciclo-03, D12): subgrafos com os nomes do padrão §7.5 e regra de consulta no AGENTS.md raiz.

Padrão (docs/padroes/ARQUITETURA-MODULARIZACAO-VSA-ECOSSISTEMA.md §7): aidd-nucleo, modulo-governanca,
triade-fluxo-pure, triade-fluxo-open, triade-fluxo-freedom, modulo-plataforma-ops.
Decisão do usuário (08/10): plataforma = modulos/03-plataforma-e-entrega inteiro; scripts/ fica no grafo do repo.
"""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "componentes" / "compartilhado" / "src-core"))

from subgrafos_federados import DOMINIOS_VSA, SubgrafoFederadoVSA  # noqa: E402

PADRAO = {
    "aidd-nucleo": "modulos/04-nucleo-compartilhado",
    "modulo-governanca": "modulos/01-governanca-e-qualidade",
    "triade-fluxo-pure": "modulos/02-triade-motores/fluxo-01-pure",
    "triade-fluxo-open": "modulos/02-triade-motores/fluxo-02-open",
    "triade-fluxo-freedom": "modulos/02-triade-motores/fluxo-03-freedom",
    "modulo-plataforma-ops": "modulos/03-plataforma-e-entrega",
}


def test_dominios_vsa_sao_exatamente_os_seis_do_padrao():
    assert DOMINIOS_VSA == PADRAO


def test_nomes_do_padrao_estao_no_documento_de_arquitetura():
    texto = (RAIZ / "docs/padroes/ARQUITETURA-MODULARIZACAO-VSA-ECOSSISTEMA.md").read_text(encoding="utf-8")
    for nome in PADRAO:
        assert f"`{nome}`" in texto


def test_cada_dominio_aponta_para_pasta_existente():
    for pasta in PADRAO.values():
        assert (RAIZ / pasta).is_dir(), pasta


def test_plataforma_cobre_enterprise_master_e_ops_e_scripts_fica_global():
    fed = SubgrafoFederadoVSA(raiz_repo=str(RAIZ))
    for fatia in ("blindagem-enterprise", "fatiamento-master", "operacoes-ops"):
        assert fed.obter_dominio_de_caminho(f"modulos/03-plataforma-e-entrega/{fatia}/x.py") == "modulo-plataforma-ops"
    assert fed.obter_dominio_de_caminho("scripts/micro_gates.py") == "global"


def test_agents_raiz_manda_consultar_primeiro_o_subgrafo_da_fatia():
    texto = (RAIZ / "AGENTS.md").read_text(encoding="utf-8")
    assert "Query the slice subgraph first" in texto
    for nome in PADRAO:
        assert f"`vsa-{nome}`" in texto, f"AGENTS.md raiz sem o subgrafo vsa-{nome}"


def test_index_subgraphs_sai_1_quando_um_subgrafo_falha(monkeypatch):
    """Saída binária honesta: imprimir FALHA e sair 0 esconde subgrafo não reindexado."""
    from scripts import cli_modularizacao_vsa

    monkeypatch.setattr(SubgrafoFederadoVSA, "indexar_todos", lambda self, modo="fast": {
        "aidd-nucleo": {"sucesso": True},
        "modulo-governanca": {"sucesso": False, "erro": "binario ausente"},
    })
    assert cli_modularizacao_vsa.comando_index_subgraphs(RAIZ) == 1
    monkeypatch.setattr(SubgrafoFederadoVSA, "indexar_todos", lambda self, modo="fast": {
        "aidd-nucleo": {"sucesso": True},
    })
    assert cli_modularizacao_vsa.comando_index_subgraphs(RAIZ) == 0
