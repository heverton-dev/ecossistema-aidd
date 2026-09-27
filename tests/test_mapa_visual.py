# -*- coding: utf-8 -*-
"""
Mapas visuais (scripts/mapa_visual.py), piloto: mapa dos guardas.

Prova que o gerador morde: molde e gerador desencontrados reprovam; selos saem
do catálogo (fora do commit, sem prova, versões, lei); texto do catálogo é
escapado; --check reprova arquivo desatualizado. O último teste roda de verdade
contra o catálogo do repositório.
"""
import json
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


def _cat_encaixes():
    etapas = [
        {"etapa": "etapa_01_forge", "descricao": "Etapa 1.", "chamadas_cli": [["forge", "init"]],
         "chamadas_por_fluxo": {}, "atalhos_internos": [], "chama_alguma_ferramenta": True},
        {"etapa": "etapa_03_engine", "descricao": "Etapa 3.", "chamadas_cli": [["factory", "curate"]],
         "chamadas_por_fluxo": {"open": [["factory", "curate"]]}, "atalhos_internos": ["tools/x"],
         "chama_alguma_ferramenta": True},
        {"etapa": "etapa_07_auditoria", "descricao": "Etapa 7.", "chamadas_cli": [], "chamadas_por_fluxo": {},
         "atalhos_internos": [], "chama_alguma_ferramenta": False},
    ]
    return {"receita_triade": {"etapas": etapas},
            "encaixes": [{"etapa": "etapa_01_forge", "chamada": "ecossistema.py forge init", "encaixa": True, "problemas": []},
                         {"etapa": "etapa_03_engine", "chamada": "ecossistema.py factory curate", "encaixa": False,
                          "problemas": ["flags inexistentes: --dir"]}],
            "contratos": [{"id": "handoff-a", "titulo": "A", "usado_por": ["scripts/x.py"]}],
            "achados": {"etapas_sem_ferramenta": ["etapa_07_auditoria"],
                        "etapas_com_atalho_interno": {"etapa_03_engine": ["tools/x"]}}}


def test_encaixes_quebra_e_fachada_saem_do_catalogo():
    valores = mv.valores_encaixes(_cat_encaixes())
    assert 'chip falha">quebra' in valores["RECEITA"] and "só open" in valores["RECEITA"]
    assert "flags inexistentes: --dir" in valores["QUEBRADOS"]
    assert "7 · auditoria" in valores["SEM_FERRAMENTA"] and "tools/x" in valores["ATALHOS"]
    assert "Não chama nenhuma ferramenta." in valores["RECEITA"] and "handoff-a" in valores["CONTRATOS"]


def test_encaixes_marcador_desencontrado_reprova(tmp_path, monkeypatch):
    (tmp_path / "encaixes.html").write_text("{{TOTAIS}} {{RECEITA}} {{SOBROU}}", encoding="utf-8")
    (tmp_path / "base.css").write_text("", encoding="utf-8")
    monkeypatch.setattr(mv, "MOLDES", tmp_path)
    with pytest.raises(ValueError, match="SOBROU"):
        mv.montar("encaixes", _cat_encaixes(), "m.html", fragmento=True)


@pytest.mark.parametrize("tipo", ["encaixes", "ferramentas", "comandos", "conexoes", "leis"])
def test_mapa_roda_de_verdade_no_repositorio(tmp_path, tipo):
    saida = tmp_path / "mapa.html"
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "mapa_visual.py"), tipo,
                           "--saida", str(saida), "--fragmento"],
                          cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    texto = saida.read_text(encoding="utf-8")
    assert texto.startswith(f"<title>{mv.TITULOS[tipo]}</title>") and "{{" not in texto
    assert texto.count('<article class="item"') > 0


def _cat_ferramentas():
    return {"ferramentas": [
        {"id": "aidd-a", "descricao": "Faz A.", "chamada": "python ecossistema.py a", "comandos": ["audit", "run"],
         "gates_proprios": ["tools/aidd-a/gates/G_A.py"], "mcps_proprios": [], "arquivos_py": 3},
        {"id": "aidd-b", "descricao": "", "chamada": "python ecossistema.py b", "comandos": ["audit"],
         "gates_proprios": [], "mcps_proprios": ["tools/aidd-b/mcps/m/server.py"], "arquivos_py": 1}],
        "achados": {"verbos_cli_repetidos": {"audit": ["aidd-a", "aidd-b"]},
                    "tarefas_com_varias_donas": {"barrar-segredos": {"donas": ["aidd-a", "aidd-b"], "arquivos": []}},
                    "arquivos_identicos_entre_donas": [{"donas": "aidd-a + aidd-b", "arquivos": 4}]}}


def test_ferramentas_repeticoes_saem_do_catalogo():
    valores = mv.valores_ferramentas(_cat_ferramentas())
    assert "audit: aidd-a, aidd-b" in valores["VERBOS"] and "barrar-segredos" in valores["DONAS"]
    assert "aidd-a + aidd-b: 4" in valores["IDENTICOS"]
    assert 'chip aviso">repetido' in valores["LISTA"] and "sem descrição no README" in valores["LISTA"]
    assert "1 MCPs" in valores["LISTA"]


def test_ferramentas_marcador_desencontrado_reprova(tmp_path, monkeypatch):
    (tmp_path / "ferramentas.html").write_text("{{TOTAIS}} {{LISTA}} {{VELHO}}", encoding="utf-8")
    (tmp_path / "base.css").write_text("", encoding="utf-8")
    monkeypatch.setattr(mv, "MOLDES", tmp_path)
    with pytest.raises(ValueError, match="VELHO"):
        mv.montar("ferramentas", _cat_ferramentas(), "m.html", fragmento=True)


def _cat_comandos():
    return {"comandos_slash": [
        {"id": "pure", "caminho": "c/pure.md", "descricao": "Fluxo 01.", "skill": "aidd-pure", "skill_existe": True},
        {"id": "livro", "caminho": "c/livro.md", "descricao": "", "skill": "aidd-velho", "skill_existe": False},
        {"id": "planner", "caminho": "c/planner.md", "descricao": "Intake.", "skill": "", "skill_existe": False}]}


def test_comandos_quebrados_e_sem_skill_saem_do_catalogo():
    valores = mv.valores_comandos(_cat_comandos())
    assert "/livro → aidd-velho" in valores["QUEBRADOS"] and "/planner" in valores["SEM_SKILL"]
    assert 'chip falha">não existe' in valores["LISTA"] and 'chip ok">existe' in valores["LISTA"]


def test_comandos_marcador_desencontrado_reprova(tmp_path, monkeypatch):
    (tmp_path / "comandos.html").write_text("{{TOTAIS}} {{LISTA}} {{QUEBRADOS}} {{EXTRA}}", encoding="utf-8")
    (tmp_path / "base.css").write_text("", encoding="utf-8")
    monkeypatch.setattr(mv, "MOLDES", tmp_path)
    with pytest.raises(ValueError, match="EXTRA"):
        mv.montar("comandos", _cat_comandos(), "m.html", fragmento=True)


def _cat_conexoes(internos=True, hooks=True):
    return {"mcps": {"registrados_mcp_json": ["context7", "github"],
                     "internos_das_ferramentas": [{"id": "docker-mcp", "ferramenta": "aidd-ops",
                                                   "caminho": "tools/aidd-ops/mcps/docker-mcp/server.py",
                                                   "registrado_em_config": False}] if internos else []},
            "hooks": [{"evento": "PreToolUse", "matcher": "Task|Agent", "script": ".claude/hooks/x.py"}] if hooks else []}


def test_conexoes_listas_saem_do_catalogo():
    valores = mv.valores_conexoes(_cat_conexoes())
    assert "context7" in valores["REGISTRADOS"] and "vai com o app gerado" in valores["INTERNOS"]
    assert "PreToolUse" in valores["HOOKS"] and "Task|Agent" in valores["HOOKS"]
    vazio = mv.valores_conexoes(_cat_conexoes(internos=False, hooks=False))
    assert "Nenhum hoje." in vazio["INTERNOS"] and "Nenhum hoje." in vazio["HOOKS"]


def test_conexoes_marcador_desencontrado_reprova(tmp_path, monkeypatch):
    (tmp_path / "conexoes.html").write_text("{{TOTAIS}} {{HOOKS}} {{FALTA}}", encoding="utf-8")
    (tmp_path / "base.css").write_text("", encoding="utf-8")
    monkeypatch.setattr(mv, "MOLDES", tmp_path)
    with pytest.raises(ValueError, match="FALTA"):
        mv.montar("conexoes", _cat_conexoes(), "m.html", fragmento=True)


def test_indice_marca_todos_os_mapas_previstos_como_concluidos():
    cat = json.loads(mv.CATALOGO.read_text(encoding="utf-8"))
    pendentes = [t for t, _, _ in mv.MAPAS_PREVISTOS if mv.status_mapa(t, cat) != "concluido"]
    assert not pendentes, f"mapas pendentes ou desatualizados: {pendentes}"


def _cat_leis():
    return {"leis": [
        {"numero": 1, "titulo": "Determinism First", "sem_gate": False, "portoes": [
            {"gate": "G_OK", "forca": "provado", "visivel": True},
            {"gate": "G_CEGO", "forca": "provado", "visivel": False},
            {"gate": "G_SUMIU", "forca": "provado", "visivel": True}]},
        {"numero": 2, "titulo": "Convencao", "sem_gate": True, "portoes": []}],
        "gates": [_gate("G_OK"), _gate("G_CEGO", no_pre_commit=False, prova_que_morde=False), _gate("G_SOLTO")]}


def test_leis_prova_fraca_sai_do_catalogo():
    valores = mv.valores_leis(_cat_leis())
    assert "Lei #1: G_CEGO" in valores["INVISIVEIS"] and "Lei #1: G_CEGO" in valores["FORA_COMMIT"]
    assert "Lei #1: G_CEGO" in valores["SEM_PROVA"] and "G_SOLTO" in valores["SEM_LEI"]
    assert 'chip ok">prova válida' in valores["LISTA"] and "guarda não existe" in valores["LISTA"]
    assert "sem gate — cumprimento por convenção" in valores["LISTA"]


def test_leis_marcador_desencontrado_reprova(tmp_path, monkeypatch):
    (tmp_path / "leis.html").write_text("{{TOTAIS}} {{LISTA}} {{OUTRO}}", encoding="utf-8")
    (tmp_path / "base.css").write_text("", encoding="utf-8")
    monkeypatch.setattr(mv, "MOLDES", tmp_path)
    with pytest.raises(ValueError, match="OUTRO"):
        mv.montar("leis", _cat_leis(), "m.html", fragmento=True)
