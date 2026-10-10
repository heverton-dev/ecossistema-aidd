# -*- coding: utf-8 -*-
"""
TDD para reconhecimento de LAUDO-REVISADO.md e DIAGNOSTICO.md no ciclo-03 de modularizacao-vsa (Item 7 pós-c03):
Garante que o catálogo reconhece as 4 fases do ciclo-03 e não gera o achado CAT-ciclo-modularizacao-vsa-ciclo-03 como aberto.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from catalogo_pecas import coletar_oficina  # noqa: E402
import achados_ciclo as ac  # noqa: E402


def test_catalogo_reconhece_fases_do_ciclo_modularizacao_vsa_ciclo_03():
    oficina = coletar_oficina()
    ciclo3 = next((c for c in oficina["ciclos"] if c["alvo"] == "modularizacao-vsa" and c["ciclo"] == "ciclo-03"), None)
    assert ciclo3 is not None, "Ciclo modularizacao-vsa/ciclo-03 não encontrado na oficina"
    assert ciclo3["fases"]["laudo_revisado"] is True, "laudo_revisado não foi reconhecido para LAUDO-REVISADO.md"
    assert ciclo3["fases"]["laudo_inicial"] is True, "laudo_inicial não foi reconhecido para DIAGNOSTICO.md"
    assert all(ciclo3["fases"].values()), f"Fases incompletas no ciclo-03: {ciclo3['fases']}"


def test_achados_ciclo_nao_gera_achado_aberto_para_modularizacao_vsa_ciclo_03():
    oficina = coletar_oficina()
    cat_minimo = {"achados": {}, "encaixes": [], "leis": [], "gates": [], "oficina": oficina}
    itens = [item for item in ac.medidos(cat_minimo) if "modularizacao-vsa-ciclo-03" in item["id"]]
    assert not itens, f"CAT-ciclo-modularizacao-vsa-ciclo-03 ainda consta em aberto: {itens}"
