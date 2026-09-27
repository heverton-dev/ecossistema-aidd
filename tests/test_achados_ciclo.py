# -*- coding: utf-8 -*-
"""
ACHADOS.json do ciclo-01 (scripts/achados_ciclo.py): base do fluxo /melhoria.

Prova que o gerador morde: achado sem evidência, com id repetido ou em aberto sem
pedido de melhoria reprova; os achados medidos saem do catálogo; --check reprova
arquivo desatualizado; o arquivo do repositório está em dia.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import achados_ciclo as ac  # noqa: E402

VALIDO = {"id": "VER-900", "titulo": "t", "gravidade": "alta", "estado": "aberto", "mapa": "encaixes",
          "evidencia": ["arquivo.py:1"], "pedido_melhoria": "Corrigir x."}


def _verificados(tmp_path, monkeypatch, *itens):
    arq = tmp_path / "verificados.json"
    arq.write_text(json.dumps({"achados": list(itens)}), encoding="utf-8")
    monkeypatch.setattr(ac, "VERIFICADOS", arq)


def test_repositorio_em_dia():
    assert ac.main(["--check"]) == 0


def test_achado_sem_evidencia_reprova(tmp_path, monkeypatch):
    _verificados(tmp_path, monkeypatch, {**VALIDO, "evidencia": []})
    assert ac.main(["--saida", str(tmp_path / "a.json")]) == 1


def test_id_repetido_reprova(tmp_path, monkeypatch):
    _verificados(tmp_path, monkeypatch, VALIDO, dict(VALIDO))
    assert ac.main(["--saida", str(tmp_path / "a.json")]) == 1


def test_aberto_sem_pedido_de_melhoria_reprova(tmp_path, monkeypatch):
    _verificados(tmp_path, monkeypatch, {**VALIDO, "pedido_melhoria": ""})
    assert ac.main(["--saida", str(tmp_path / "a.json")]) == 1


def test_check_reprova_arquivo_desatualizado(tmp_path):
    velho = tmp_path / "a.json"
    velho.write_text("{}", encoding="utf-8")
    assert ac.main(["--saida", str(velho), "--check"]) == 1


def test_medidos_saem_do_catalogo():
    cat = {"achados": {"etapas_sem_ferramenta": ["etapa_07_auditoria"], "etapas_com_atalho_interno": {},
                       "gates_mesmo_nome_codigo_diferente": [], "tarefas_com_varias_donas": {},
                       "arquivos_identicos_entre_donas": [], "verbos_cli_repetidos": {}},
           "encaixes": [{"etapa": "etapa_03_engine", "chamada": "ecossistema.py bridge scan --dir <var>",
                         "encaixa": False, "problemas": ["flags inexistentes: --dir"]}],
           "leis": [], "gates": []}
    ids = {i["id"]: i for i in ac.medidos(cat)}
    assert "CAT-etapa-sem-ferramenta-etapa-07-auditoria" in ids
    quebra = next(i for i in ids.values() if i["mapa"] == "encaixes" and "bridge" in i["titulo"])
    assert quebra["gravidade"] == "alta" and "flags inexistentes: --dir" in quebra["evidencia"][0]
    assert all(i["pedido_melhoria"] for i in ids.values())
