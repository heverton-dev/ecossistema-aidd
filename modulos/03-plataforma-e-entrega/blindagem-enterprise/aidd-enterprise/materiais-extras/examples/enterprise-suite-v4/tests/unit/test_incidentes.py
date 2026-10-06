import pytest


def test_get_incidentes_vazio_por_padrao(app):
    assert app.get_incidentes({}) == []


@pytest.mark.parametrize("prioridade,sla_esperado", [
    ("P1", 2),
    ("P2", 4),
    ("P3", 24),
])
def test_post_salvar_incidente_mapeia_sla_por_prioridade(app, prioridade, sla_esperado):
    resultado = app.post_salvar_incidente({
        "titulo": "Falha no Sistema de Freio Pneumático",
        "veiculo_placa": "bra2e19",
        "prioridade": prioridade,
    })
    assert resultado["sucesso"] is True
    assert resultado["protocolo"].startswith("INC-")

    incidente = app.get_incidentes({})[0]
    assert incidente["prioridade"] == prioridade
    assert incidente["sla_horas"] == sla_esperado
    assert incidente["veiculo_placa"] == "BRA2E19"
    assert incidente["status"] == "aberto"


def test_post_resolver_incidente_marca_resolvido(app):
    criado = app.post_salvar_incidente({
        "titulo": "Troca de Pneu Rota SP",
        "veiculo_placa": "KLP9A88",
        "prioridade": "P3",
    })
    incidente_id = app.get_incidentes({})[0]["id"]

    resultado = app.post_resolver_incidente({"id": incidente_id})
    assert resultado == {"sucesso": True, "status": "resolvido"}

    incidente = app.get_incidentes({})[0]
    assert incidente["status"] == "resolvido"


def test_post_excluir_incidente_remove_do_historico(app):
    app.post_salvar_incidente({
        "titulo": "Pane Elétrica",
        "veiculo_placa": "RFT4C22",
        "prioridade": "P2",
    })
    incidente_id = app.get_incidentes({})[0]["id"]

    resultado = app.post_excluir_incidente({"id": incidente_id})
    assert resultado == {"sucesso": True, "id": incidente_id}
    assert app.get_incidentes({}) == []
