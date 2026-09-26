# -*- coding: utf-8 -*-
"""
Mapas visuais (scripts/mapa_visual.py), piloto: mapa dos guardas.

Prova que o gerador morde: molde e gerador desencontrados reprovam; selos saem
do catálogo (fora do commit, sem prova, versões, lei); texto do catálogo é
escapado; --check reprova arquivo desatualizado. O último teste roda de verdade
contra o catálogo do repositório.
"""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import mapa_visual as mv  # noqa: E402


def _gate(nome, papel="ecossistema", **extra):
    base = {"id": nome, "descricao": "confere algo", "copias": [{"caminho": f"gates/{nome}.py", "papel": papel}],
            "versoes_distintas": 1, "no_pre_commit": True, "prova_que_morde": True, "leis": []}
    return {**base, **extra}


def _catalogo(*gates, invisiveis=()):
    return {"gates": list(gates), "achados": {"declaracoes_de_lei_invisiveis_ao_meta_gate": list(invisiveis)}}


def test_marcador_sem_valor_reprova(tmp_path, monkeypatch):
    (tmp_path / "guardas.html").write_text("<p>{{TOTAIS}} {{NAO_EXISTE}}</p>", encoding="utf-8")
    (tmp_path / "base.css").write_text("", encoding="utf-8")
    monkeypatch.setattr(mv, "MOLDES", tmp_path)
    with pytest.raises(ValueError, match="NAO_EXISTE"):
        mv.montar("guardas", _catalogo(_gate("G_A")), "m.html", fragmento=True)


def test_selos_saem_do_catalogo():
    fora = _gate("G_FORA", no_pre_commit=False, prova_que_morde=False, leis=[4], versoes_distintas=3)
    html_item = mv._item(fora, "ecossistema")
    for selo in ("fora do commit", "sem prova", "Lei #4", "3 versões"):
        assert selo in html_item
    assert 'data-foracommit="1"' in html_item and 'data-versoes="1"' in html_item
    ferramenta = mv._item(_gate("G_TOOL", papel="ferramenta", no_pre_commit=False, prova_que_morde=None), "ferramenta")
    assert "fora do commit" not in ferramenta and "prova" not in ferramenta


def test_casa_meta_e_ordem_das_casas():
    assert mv._casa(_gate("G_PORTAO_PROVA_QUE_MORDE")) == "meta"
    misto = _gate("G_X", copias=[{"caminho": "tools/aidd-master/templates/gates/G_X.py", "papel": "entrega"},
                                 {"caminho": "tools/aidd-master/scripts/gates/G_X.py", "papel": "ferramenta"}])
    assert mv._casa(misto) == "ferramenta"


def test_texto_do_catalogo_e_escapado():
    item = mv._item(_gate("G_A", descricao='<script>alert("x")</script>'), "ecossistema")
    assert "<script>" not in item and "&lt;script&gt;" in item


def test_listas_de_achados_vazias_e_cheias():
    valores = mv.valores_guardas(_catalogo(_gate("G_A", no_pre_commit=False), invisiveis=["Lei #1: G_A"]))
    assert "G_A" in valores["FORA_COMMIT"] and "Lei #1: G_A" in valores["INVISIVEIS"]
    assert "Nenhum caso hoje." in valores["DIVERGENTES"]


def test_check_reprova_mapa_desatualizado(tmp_path):
    saida = tmp_path / "mapa.html"
    saida.write_text("velho", encoding="utf-8")
    assert mv.main(["guardas", "--saida", str(saida), "--check"]) == 1
    assert mv.main(["guardas", "--saida", str(saida)]) == 0
    assert mv.main(["guardas", "--saida", str(saida), "--check"]) == 0


def test_roda_de_verdade_no_repositorio(tmp_path):
    saida = tmp_path / "mapa.html"
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "mapa_visual.py"), "guardas",
                           "--saida", str(saida), "--fragmento"],
                          cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    texto = saida.read_text(encoding="utf-8")
    assert texto.startswith("<title>Mapa dos Guardas</title>") and "{{" not in texto
    assert texto.count('<article class="item"') > 50


def _cat_skills(*skills, terceiros=(), pares=()):
    return {"skills": list(skills), "skills_terceiros": list(terceiros),
            "achados": {"skills_mesma_descricao": [list(p) for p in pares]}}


def _skill(nome, linhas=40, descricao="Does X. Use when the user says \"x\".", terceiro=False):
    return {"id": nome, "descricao": descricao, "linhas": linhas, "terceiro": terceiro}


def test_skills_marcador_desencontrado_reprova(tmp_path, monkeypatch):
    (tmp_path / "skills.html").write_text("<p>{{TOTAIS}} {{LISTA}} {{MARCADOR_VELHO}}</p>", encoding="utf-8")
    (tmp_path / "base.css").write_text("", encoding="utf-8")
    monkeypatch.setattr(mv, "MOLDES", tmp_path)
    with pytest.raises(ValueError, match="MARCADOR_VELHO"):
        mv.montar("skills", _cat_skills(_skill("aidd-a")), "m.html", fragmento=True)


def test_skills_selos_e_listas_saem_do_catalogo():
    grande = _skill("aidd-grande", linhas=300, descricao="Does Y.")
    valores = mv.valores_skills(_cat_skills(_skill("aidd-a"), grande, _skill("wrangler", terceiro=True),
                                            terceiros=["wrangler"], pares=[("aidd-a", "a")]))
    assert "aidd-grande (300)" in valores["ACIMA_META"]
    assert "wrangler" in valores["TERCEIROS"] and "aidd-a = a" in valores["MESMA_DESCRICAO"]
    assert 'sem "Use when"' in valores["LISTA"] and 'data-acima="1"' in valores["LISTA"]
    assert "terceiros copiados para a fonte" in valores["TOTAIS"]


def test_skills_roda_de_verdade_no_repositorio(tmp_path):
    saida = tmp_path / "mapa.html"
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "mapa_visual.py"), "skills",
                           "--saida", str(saida), "--fragmento"],
                          cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    texto = saida.read_text(encoding="utf-8")
    assert texto.startswith("<title>Mapa das Skills</title>") and "{{" not in texto
    import json
    cat = json.loads((ROOT / "docs" / "auditoria" / "mapa-pecas" / "catalogo-pecas.json").read_text(encoding="utf-8"))
    assert texto.count('<article class="item"') == sum(1 for s in cat["skills"] if not s["terceiro"])
    assert "CONVENCAO-AUTORIA-SKILLS.md" in texto


def test_indice_status_sai_do_disco(tmp_path, monkeypatch):
    monkeypatch.setattr(mv, "MAPAS", tmp_path)
    monkeypatch.setattr(mv, "MAPAS_PREVISTOS", (
        ("skills", "Mapa das skills", "a"), ("guardas", "Mapa dos guardas", "b"), ("futuro", "Mapa futuro", "c")))
    cat = {**_cat_skills(_skill("aidd-a")), "gates": [_gate("G_A")],
           "achados": {"skills_mesma_descricao": [], "declaracoes_de_lei_invisiveis_ao_meta_gate": []}}
    (tmp_path / "mapa-skills.html").write_text(mv.montar("skills", cat, "manual-montagem-aidd.html", False),
                                               encoding="utf-8")
    (tmp_path / "mapa-guardas.html").write_text("velho", encoding="utf-8")
    assert mv.status_mapa("skills", cat) == "concluido"
    assert mv.status_mapa("guardas", cat) == "desatualizado"
    assert mv.status_mapa("futuro", cat) == "a-criar"
    valores = mv.valores_indice(cat)
    assert "de 3 mapas concluídos" in valores["TOTAIS"] and "ainda não existe" in valores["LISTA"]


def test_todo_mapa_previsto_tem_molde_se_tem_gerador():
    for tipo, _titulo, _para_que in mv.MAPAS_PREVISTOS:
        if tipo in mv.GERADORES:
            assert (mv.MOLDES / f"{tipo}.html").is_file(), tipo
            assert tipo in mv.TITULOS, tipo
