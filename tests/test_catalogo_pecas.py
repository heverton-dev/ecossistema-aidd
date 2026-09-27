# -*- coding: utf-8 -*-
"""
mapa-pecas ciclo-01, passo 1: catálogo de peças (scripts/catalogo_pecas.py).

Prova que o catálogo morde: receita falsa com etapa sem ferramenta, atalho
interno e ramo por fluxo é detectada; chamada com flag inexistente ou
argumento posicional recusado vira encaixe quebrado; --check reprova arquivo
desatualizado. O teste final roda o script de verdade contra o repositório.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "catalogo_pecas.py"
sys.path.insert(0, str(ROOT / "scripts"))

import catalogo_pecas as cp  # noqa: E402

RECEITA_FALSA = '''
class O:
    def etapa_01_forge(self):
        """Etapa 1: fundação."""
        cmd = [sys.executable, "ecossistema.py", "forge", "init", str(self.pasta)]

    def etapa_03_engine(self):
        """Etapa 3: engine."""
        if self.fluxo == 1:
            cmd = [sys.executable, "ecossistema.py", "generate", "x"]
        elif self.fluxo == 2:
            cmd = [sys.executable, "ecossistema.py", "factory", "curate"]
        if self.modo == 3:
            cmd = [sys.executable, "ecossistema.py", "bridge", "scan"]
        script = ROOT_DIR / "tools" / "aidd-master" / "scripts" / "dispatch.py"
        if rc != 0:
            return False

    def etapa_06_ops(self):
        """Etapa 6: só confere arquivo."""
        return (self.pasta / "Dockerfile").exists()
'''


def _receita(tmp_path, monkeypatch):
    arq = tmp_path / "orquestrador_sincrono.py"
    arq.write_text(RECEITA_FALSA, encoding="utf-8")
    monkeypatch.setattr(cp, "ORQUESTRADOR", arq)
    monkeypatch.setattr(cp, "_rel", lambda p: p.name)
    return {e["etapa"]: e for e in cp.coletar_receita()["etapas"]}


def test_etapa_sem_ferramenta_e_detectada(tmp_path, monkeypatch):
    etapas = _receita(tmp_path, monkeypatch)
    assert etapas["etapa_06_ops"]["chama_alguma_ferramenta"] is False
    assert etapas["etapa_01_forge"]["chamadas_cli"] == [["forge", "init", "<var>"]]


def test_ramos_por_fluxo_ignoram_if_que_nao_e_fluxo(tmp_path, monkeypatch):
    etapa = _receita(tmp_path, monkeypatch)["etapa_03_engine"]
    assert etapa["chamadas_por_fluxo"] == {"pure": [["generate", "x"]], "open": [["factory", "curate"]]}


def test_atalho_interno_guarda_so_caminho_completo(tmp_path, monkeypatch):
    etapa = _receita(tmp_path, monkeypatch)["etapa_03_engine"]
    assert etapa["atalhos_internos"] == ["tools/aidd-master/scripts/dispatch.py"]


def _encaixe(monkeypatch, tokens, comandos, texto_help):
    monkeypatch.setattr(cp, "_help", lambda alvo: (0, texto_help))
    receita = {"etapas": [{"etapa": "e", "chamadas_cli": [tokens]}]}
    ferramentas = [{"chamada": f"python ecossistema.py {tokens[0]}", "comandos": comandos}]
    return cp.verificar_encaixes(receita, ferramentas)[0]


def test_flag_inexistente_quebra_encaixe(monkeypatch):
    r = _encaixe(monkeypatch, ["bridge", "scan", "--dir", "<var>"], ["scan"], "usage: scan project_dir")
    assert r["encaixa"] is False and "--dir" in r["problemas"][0]


def test_posicional_em_comando_unico_sem_argumento_quebra_encaixe(monkeypatch):
    r = _encaixe(monkeypatch, ["factory", "curate"], [], "Usage: pipeline_factory.py [OPTIONS]\n  --plano")
    assert r["encaixa"] is False


def test_chamada_correta_encaixa(monkeypatch):
    r = _encaixe(monkeypatch, ["generate", "x", "--pasta", "<var>"], [],
                 "Usage: pipeline_completo.py [OPTIONS] IDEIA\n  --pasta TEXT")
    assert r == {"etapa": "e", "chamada": "ecossistema.py generate x --pasta <var>",
                 "encaixa": True, "problemas": []}


def test_click_command_unico_nao_vira_subcomando():
    assert cp.RE_CLICK.findall('@click.command("factory")\n@cli.command("init", help="x")') == ["init"]


def test_check_reprova_arquivo_desatualizado(tmp_path, monkeypatch):
    monkeypatch.setattr(cp, "gerar", lambda com_encaixe=True: {"a": 1})
    saida = tmp_path / "catalogo.json"
    saida.write_text("{}", encoding="utf-8")
    assert cp.main(["--saida", str(saida), "--check", "--sem-encaixe"]) == 1
    assert cp.main(["--saida", str(saida), "--sem-encaixe"]) == 0
    assert cp.main(["--saida", str(saida), "--check", "--sem-encaixe"]) == 0


def test_roda_de_verdade_no_repositorio(tmp_path):
    saida = tmp_path / "catalogo.json"
    proc = subprocess.run([sys.executable, str(SCRIPT), "--saida", str(saida), "--sem-encaixe"],
                          cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    assert proc.returncode == 0, proc.stderr
    dados = json.loads(saida.read_text(encoding="utf-8"))
    ids = {f["id"] for f in dados["ferramentas"]}
    assert {"aidd-forge", "aidd-planner", "aidd-master", "aidd-ops"} <= ids
    assert dados["totais"]["skills"] > 0 and dados["totais"]["etapas_receita"] == 7


def _gate(tmp_path, nome, doc, bom=False):
    arq = tmp_path / f"{nome}.py"
    arq.write_text(("﻿" if bom else "") + f'"""\n{doc}\n"""\n', encoding="utf-8")
    return arq


def test_descricao_pula_banner_regua_e_bom(tmp_path):
    doc = "=====\nECOSSISTEMA AIDD — QUALITY GATE: G_X\n=====\nTitulo solto\n=====\nConfere a coisa\nem duas linhas.\n\nDetalhe."
    assert cp._descricao_gate(_gate(tmp_path, "G_X", doc, bom=True)) == "Confere a coisa em duas linhas."


def test_descricao_tira_prefixo_com_nome_e_junta_item_apos_dois_pontos(tmp_path):
    assert cp._descricao_gate(_gate(tmp_path, "G_Y", "GATE: G_Y — Pré-voo do pipeline.")) == "Pré-voo do pipeline."
    assert cp._descricao_gate(_gate(tmp_path, "G_Z", "Verifica:\n  - JSON valido\n  - outra")) == "Verifica: JSON valido"


def test_declaracao_com_comentario_e_invisivel_ao_meta_gate():
    leis_mod, _ = cp._meta_gates()
    agents = ("## 2. Inviolable Laws\n"
              "1. **Lei Um:** texto.\n"
              "   - Portão: gates/G_A.py (provado)\n"
              "   - Portão: gates/G_B.py (provado) — comentário depois\n"
              "## 3. Outra seção\n")
    mapa, invisiveis = cp._leis_por_gate(leis_mod, agents)
    assert mapa == {"G_A": [1], "G_B": [1]}
    assert invisiveis == ["Lei #1: G_B"]


def test_skill_de_terceiro_copiada_para_a_fonte_e_marcada(tmp_path, monkeypatch):
    for nome in ("aidd-proprio", "wrangler"):
        d = tmp_path / "skills" / nome
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(f"---\nname: {nome}\ndescription: x\n---\n", encoding="utf-8")
    monkeypatch.setattr(cp, "COMPARTILHADO", tmp_path)
    skills = {s["id"]: s["terceiro"] for s in cp.coletar_skills(["wrangler"])}
    assert skills == {"aidd-proprio": False, "wrangler": True}
    assert "wrangler" in cp.coletar_skills_terceiros()



def test_comando_slash_registra_a_skill_e_se_ela_existe(tmp_path, monkeypatch):
    (tmp_path / "comandos").mkdir()
    (tmp_path / "skills" / "aidd-pure").mkdir(parents=True)
    (tmp_path / "skills" / "aidd-pure" / "SKILL.md").write_text("---\nname: aidd-pure\n---\n", encoding="utf-8")
    (tmp_path / "comandos" / "pure.md").write_text("# /pure\n\nFluxo 01.\n\nExecuta a skill `aidd-pure`.\n", encoding="utf-8")
    (tmp_path / "comandos" / "velho.md").write_text("# /velho\n\nExecuta a skill `skills/aidd-velho`.\n", encoding="utf-8")
    (tmp_path / "comandos" / "solto.md").write_text("# /solto\n\nSem skill.\n", encoding="utf-8")
    monkeypatch.setattr(cp, "COMPARTILHADO", tmp_path)
    monkeypatch.setattr(cp, "RAIZ", tmp_path)
    por_id ={c["id"]: c for c in cp.coletar_comandos_slash()}
    assert (por_id["pure"]["skill"], por_id["pure"]["skill_existe"], por_id["pure"]["descricao"]) == ("aidd-pure", True, "Fluxo 01.")
    assert (por_id["velho"]["skill"], por_id["velho"]["skill_existe"]) == ("aidd-velho", False)
    assert por_id["solto"]["skill"] == ""


def test_leis_registram_declaracao_invisivel_ao_meta_gate(tmp_path, monkeypatch):
    agents = tmp_path / "AGENTS.md"
    agents.write_text(
        "## 2. Inviolable Laws\n\n"
        "1. **Primeira:** texto.\n"
        "   - Portão: gates/G_A.py (provado)\n"
        "   - Portão: gates/G_B.py (provado) — comentário\n"
        "2. **Segunda:** texto.\n"
        "   - Portão: sem gate — cumprimento por convenção (sem-gate)\n"
        "\n## 3. Outra seção\n", encoding="utf-8")
    monkeypatch.setattr(cp, "RAIZ", tmp_path)
    monkeypatch.setattr(cp, "_meta_gates", lambda: (_leis_mod(), None))
    leis = {lei["numero"]: lei for lei in cp.coletar_leis()}
    assert [(pt["gate"], pt["visivel"]) for pt in leis[1]["portoes"]] == [("G_A", True), ("G_B", False)]
    assert leis[2]["sem_gate"] is True and leis[2]["portoes"] == []


def _leis_mod():
    sys.path.insert(0, str(ROOT / "gates"))
    try:
        import G_LEI_DECLARA_PORTAO as leis
    finally:
        sys.path.pop(0)
    return leis


def test_classificar_dimensao_por_palavra_chave():
    assert cp.classificar_dimensao("FAILED: Not implemented. x") == "falha"
    assert cp.classificar_dimensao("IMPLEMENTADO PARCIALMENTE. x") == "parcial"
    assert cp.classificar_dimensao("Implementado. `iniciar` exige") == "ok"
    assert cp.classificar_dimensao("Objetivo de avaliar a base") == "descrito"



def test_script_citado_so_por_gerador_de_documentacao_continua_sem_chamador(tmp_path, monkeypatch):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "solto.py").write_text('"""Faz algo."""\n', encoding="utf-8")
    (tmp_path / "scripts" / "livro_mapas.py").write_text('"""Cita scripts/solto.py como texto."""\n', encoding="utf-8")
    (tmp_path / "scripts" / "usa.py").write_text('"""Usa."""\nimport solto\n', encoding="utf-8")
    monkeypatch.setattr(cp, "RAIZ", tmp_path)
    por_id = {s["id"]: s["chamado_por"] for s in cp.coletar_scripts()}
    assert por_id["solto"] == ["scripts"]
    (tmp_path / "scripts" / "usa.py").unlink()
    por_id = {s["id"]: s["chamado_por"] for s in cp.coletar_scripts()}
    assert por_id["solto"] == []
