# -*- coding: utf-8 -*-
"""
aidd-visual-maps ciclo-01, Ticket 6 (D8): mapa não técnico em PT-BR e montagem sem cópia.

Achados F6/N6 do laudo: o mapa não técnico de skills repetia as descrições em inglês
das SKILL.md (124 frases-padrão "Use when"/"Builds"/"Runs"...) e o compilador não
técnico tinha a própria cópia da conferência de marcadores. Agora a descrição de cada
skill vem do comando slash (já em PT-BR) ou de moldes-nao-tecnicos/descricoes-pt.json;
sem nenhuma das duas é erro, nunca volta para o inglês. Os dois compiladores usam a
mesma aplicar_molde e o caminho do catálogo é declarado uma vez só.
"""
import inspect
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import compilar_mapas_nao_tecnicos as nt  # noqa: E402
import mapa_visual as mv  # noqa: E402

RE_INGLES = re.compile(r"Use when|Builds|Runs|Records|Use this")


def test_nenhuma_frase_padrao_em_ingles_nos_mapas_nao_tecnicos():
    achados = {p.name: len(RE_INGLES.findall(p.read_text(encoding="utf-8")))
               for p in sorted((ROOT / "docs" / "mapas-visuais" / "nao-tecnicos").glob("*.html"))}
    assert sum(achados.values()) == 0, {k: v for k, v in achados.items() if v}


def test_compiladores_usam_a_mesma_aplicar_molde():
    fonte_nt = inspect.getsource(nt.compilar_nao_tecnico)
    assert "aplicar_molde(" in fonte_nt and "re.findall" not in fonte_nt
    assert "aplicar_molde(" in inspect.getsource(mv.montar)
    assert "GERADORES" not in inspect.getsource(nt)


def _cat(comandos, skills):
    return {"comandos_slash": comandos, "skills": [{"id": s, "descricao": "Builds X. Use when Y.", "linhas": 10,
                                                    "terceiro": False} for s in skills]}


def test_descricao_vem_do_comando_de_mesmo_nome_e_depois_do_json(tmp_path, monkeypatch):
    arq = tmp_path / "descricoes-pt.json"
    arq.write_text(json.dumps({"aidd-b": "Faz B."}), encoding="utf-8")
    monkeypatch.setattr(nt, "DESCRICOES_PT", arq)
    comandos = [{"id": "apelido", "skill": "aidd-a", "descricao": "Apelido antigo."},
                {"id": "a", "skill": "aidd-a", "descricao": "Faz A."}]
    assert nt.descricoes_pt(_cat(comandos, ["aidd-a", "aidd-b"])) == {"aidd-a": "Faz A.", "aidd-b": "Faz B."}


def test_skill_sem_descricao_pt_reprova_listando_as_que_faltam(tmp_path, monkeypatch):
    arq = tmp_path / "descricoes-pt.json"
    arq.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(nt, "DESCRICOES_PT", arq)
    with pytest.raises(ValueError, match="aidd-sem-pt"):
        nt.descricoes_pt(_cat([], ["aidd-sem-pt"]))


def test_caminho_do_catalogo_declarado_uma_vez():
    arquivos = [*(ROOT / "scripts").glob("*.py"), ROOT / "modulos" / "04-nucleo-compartilhado" / "gates" / "G_mapa_pecas.py"]
    declaracoes = [f"{p.name}:{n}" for p in arquivos for n, linha in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
                   if re.search(r"[\"']catalogo-pecas\.json[\"']", linha)]
    assert len(declaracoes) == 1 and declaracoes[0].startswith("catalogo_pecas.py:"), declaracoes
    import catalogo_pecas as cp
    import livro_mapas as lm
    assert mv.CATALOGO == cp.SAIDA_PADRAO and lm.CATALOGO == cp.SAIDA_PADRAO
