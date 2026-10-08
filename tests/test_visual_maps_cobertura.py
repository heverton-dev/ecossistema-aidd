# -*- coding: utf-8 -*-
"""
aidd-visual-maps ciclo-01, Ticket 5 (D5): mapas de pipelines, módulos VSA e agentes.

Achado F4 do laudo: o ecossistema não tinha mapa dos pipelines (Tríade 01/02/03,
melhoria -> plan -> orchestrate, aidd-ingest, aidd-audit-4f, aidd-evolution), das
áreas e fatias de modulos/ nem dos templates de agentes. Os três tipos entram no fim
de MAPAS_PREVISTOS (sem renumerar os existentes) e o catálogo ganha as três chaves,
derivadas do código (nenhuma lista digitada).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import catalogo_pecas as cp  # noqa: E402
import mapa_visual as mv  # noqa: E402

NOVOS = ("pipelines", "modulos", "agentes")


def test_tres_tipos_novos_no_fim_sem_renumerar():
    tipos = [t for t, _, _ in mv.MAPAS_PREVISTOS]
    assert tipos[-3:] == list(NOVOS)
    assert mv.arquivo_mapa("leis") == "mapa-01-leis.html" and mv.arquivo_mapa("lente15d") == "mapa-12-lente15d.html"
    assert [mv.arquivo_mapa(t) for t in NOVOS] == ["mapa-13-pipelines.html", "mapa-14-modulos.html", "mapa-15-agentes.html"]
    for tipo in NOVOS:
        assert tipo in mv.GERADORES and tipo in mv.TITULOS
        assert (mv.MOLDES / f"{tipo}.html").is_file()
        assert (ROOT / "docs" / "mapas-visuais" / "moldes-nao-tecnicos" / f"{tipo}.html").is_file()


def test_pipelines_saem_da_receita_e_das_skills():
    pipelines = {p["id"]: p for p in cp.coletar_pipelines(cp.coletar_receita())}
    for fluxo in ("triade-pure", "triade-open", "triade-freedom"):
        assert len(pipelines[fluxo]["etapas"]) == len(cp.coletar_receita()["etapas"])
    cadeia = pipelines["melhoria -> plan -> orchestrate"]
    assert [e["peca"] for e in cadeia["etapas"]] == ["aidd-improvement", "aidd-plan", "aidd-orchestrate"]
    for skill in ("aidd-ingest", "aidd-audit-4f", "aidd-evolution"):
        assert pipelines[skill]["etapas"], skill
    assert [e["titulo"] for e in pipelines["aidd-ingest"]["etapas"]][0].startswith("Triage")


def test_modulos_listam_as_areas_e_fatias():
    modulos = {m["id"]: m for m in cp.coletar_modulos()}
    areas = sorted(p.name for p in (ROOT / "modulos").iterdir() if p.is_dir() and not p.name.startswith(("_", ".")))
    assert sorted(modulos) == areas
    fatias = {f["id"] for f in modulos["02-triade-motores"]["fatias"]}
    assert {"fluxo-01-pure", "fluxo-02-open", "fluxo-03-freedom"} <= fatias
    pure = next(f for f in modulos["02-triade-motores"]["fatias"] if f["id"] == "fluxo-01-pure")
    assert "aidd-pure" in pure["ferramentas"]


def test_agentes_agrupam_copias_identicas_por_conteudo():
    agentes = {a["id"]: a for a in cp.coletar_agentes()}
    arquiteto = agentes["agent_architect"]
    donas = {c["caminho"].split("/")[2] for c in arquiteto["copias"]}
    assert donas == {"blindagem-enterprise", "fatiamento-master"}
    assert arquiteto["versoes_distintas"] == 1


def test_catalogo_real_tem_as_tres_chaves_e_os_mapas_existem():
    cat = json.loads(mv.CATALOGO.read_text(encoding="utf-8"))
    for chave in NOVOS:
        assert cat.get(chave), chave
        assert cat["totais"][chave] == len(cat[chave])
        assert (mv.MAPAS / mv.arquivo_mapa(chave)).is_file()
    assert "agent_architect" in (mv.MAPAS / mv.arquivo_mapa("agentes")).read_text(encoding="utf-8")
