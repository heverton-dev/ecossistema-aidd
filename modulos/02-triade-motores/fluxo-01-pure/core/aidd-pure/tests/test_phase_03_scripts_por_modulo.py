# -*- coding: utf-8 -*-
"""
Ticket 11-A (ETAPA_11): o design determinístico da Fase 3 deve derivar os
scripts dos módulos do Planner (um conjunto por contexto delimitado), em vez
de usar sempre o mesmo esqueleto fixo.
"""

import json


def _handoff(tmp_path, modulos):
    caminho = tmp_path / "HANDOFF_PLANNER_ENGINE.json"
    caminho.write_text(json.dumps({"modulos_funcionais": modulos}), encoding="utf-8")
    return caminho


def _nomes(designer_03, tmp_path, modulos):
    designer = designer_03.DesignerFase3(tmp_path / ".aidd" / "cache")
    plano = _handoff(tmp_path, modulos)
    resultado = designer._gerar_design_deterministico_handoff(plano, "ideia")
    return [s["nome"] for s in resultado["engenheiro_scripts"]["scripts"]]


def test_duas_specs_diferentes_geram_nomes_de_script_diferentes(designer_03, tmp_path):
    a = _nomes(designer_03, tmp_path / "a", [{"slug": "pedidos"}, {"slug": "clientes"}])
    b = _nomes(designer_03, tmp_path / "b", [{"slug": "estoque"}])
    assert a != b
    assert "servicos_pedidos.py" in a and "servicos_clientes.py" in a
    assert "servicos_estoque.py" in b and "servicos_pedidos.py" not in b


def test_cada_modulo_recebe_validador_servico_e_persistencia(designer_03, tmp_path):
    nomes = _nomes(designer_03, tmp_path, [{"slug": "ordens-servico"}])
    for prefixo in ("validadores", "servicos", "persistencia"):
        assert f"{prefixo}_ordens_servico.py" in nomes
    assert nomes.count("quarteto_studios.py") == 1


def test_sem_modulos_mantem_o_esqueleto_antigo(designer_03, tmp_path):
    nomes = _nomes(designer_03, tmp_path, [])
    assert nomes == ["validadores.py", "servicos_dominio.py",
                     "persistencia_sqlite.py", "quarteto_studios.py"]


def test_nomes_de_modulo_hostis_viram_identificadores_seguros(designer_03, tmp_path):
    nomes = _nomes(designer_03, tmp_path, [{"slug": "../../etc"}, {"nome": "Atendimento ao Cliente"}])
    for nome in nomes:
        assert "/" not in nome and ".." not in nome.replace(".py", "")
        assert nome[:-3].isidentifier(), nome
    assert len(set(nomes)) == len(nomes)


def test_modulos_duplicados_nao_colidem(designer_03, tmp_path):
    nomes = _nomes(designer_03, tmp_path, [{"slug": "pedidos"}, {"slug": "pedidos"}])
    assert len(set(nomes)) == len(nomes)
