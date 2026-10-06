def test_get_fretes_retorna_seeds(app):
    lancamentos = app.get_fretes({})
    assert len(lancamentos) == 3
    tipos = {l["tipo"] for l in lancamentos}
    assert tipos == {"receita", "despesa"}


def test_post_salvar_frete_insere_pendente(app):
    resultado = app.post_salvar_frete({
        "tipo": "despesa",
        "descricao": "Abastecimento Frota Diesel S10",
        "categoria": "Combustível",
        "valor": 3200.0,
        "data_vencimento": "2026-09-15",
    })
    assert resultado == {"sucesso": True}

    lancamentos = app.get_fretes({})
    novo = next(l for l in lancamentos if l["descricao"] == "Abastecimento Frota Diesel S10")
    assert novo["status"] == "pendente"
    assert novo["valor"] == 3200.0
    assert len(lancamentos) == 4


def test_post_alternar_status_frete_alterna_pago_pendente(app):
    criado = app.post_salvar_frete({
        "tipo": "despesa", "descricao": "Pedágio Rota SP-PR", "categoria": "Pedágios",
        "valor": 680.0, "data_vencimento": "2026-09-20",
    })
    assert criado["sucesso"] is True
    lancamento = next(l for l in app.get_fretes({}) if l["status"] == "pendente")

    resultado = app.post_alternar_status_frete({"id": lancamento["id"]})
    assert resultado == {"sucesso": True, "status": "pago"}

    resultado2 = app.post_alternar_status_frete({"id": lancamento["id"]})
    assert resultado2 == {"sucesso": True, "status": "pendente"}


def test_post_alternar_status_frete_id_inexistente(app):
    resultado = app.post_alternar_status_frete({"id": 99999})
    assert resultado == {"sucesso": False, "erro": "Lançamento não encontrado"}


def test_post_excluir_frete_remove_lancamento(app):
    lancamento = app.get_fretes({})[0]
    resultado = app.post_excluir_frete({"id": lancamento["id"]})
    assert resultado == {"sucesso": True, "id": lancamento["id"]}

    lancamentos = app.get_fretes({})
    assert all(l["id"] != lancamento["id"] for l in lancamentos)
    assert len(lancamentos) == 2
