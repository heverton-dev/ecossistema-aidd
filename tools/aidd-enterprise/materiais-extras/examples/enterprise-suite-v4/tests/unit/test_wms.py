def test_get_estoque_retorna_seeds(app):
    itens = app.get_estoque({})
    assert len(itens) == 3
    skus = {i["sku"] for i in itens}
    assert {"SKU-LOG-101", "SKU-LOG-202", "SKU-LOG-303"}.issubset(skus)


def test_post_salvar_estoque_normaliza_sku_e_posicao(app):
    resultado = app.post_salvar_estoque({
        "sku": "sku-log-205",
        "descricao": "Cabos de Cobre 50mm",
        "posicao_palete": "rua-b-08",
        "quantidade": 120,
        "valor_unitario": 450.0,
    })
    assert resultado == {"sucesso": True, "sku": "SKU-LOG-205"}

    itens = app.get_estoque({})
    novo = next(i for i in itens if i["sku"] == "SKU-LOG-205")
    assert novo["posicao_palete"] == "RUA-B-08"
    assert novo["quantidade"] == 120
    assert len(itens) == 4


def test_post_ajustar_estoque_atualiza_quantidade_e_posicao(app):
    resultado = app.post_ajustar_estoque({"id": 1, "quantidade": 500, "posicao_palete": "rua-a-05"})
    assert resultado == {"sucesso": True, "id": 1}

    item = next(i for i in app.get_estoque({}) if i["id"] == 1)
    assert item["quantidade"] == 500
    assert item["posicao_palete"] == "RUA-A-05"


def test_post_ajustar_estoque_sem_nova_posicao_mantem_a_atual(app):
    original = next(i for i in app.get_estoque({}) if i["id"] == 2)
    app.post_ajustar_estoque({"id": 2, "quantidade": 999})

    item = next(i for i in app.get_estoque({}) if i["id"] == 2)
    assert item["quantidade"] == 999
    assert item["posicao_palete"] == original["posicao_palete"]


def test_post_excluir_estoque_remove_item(app):
    resultado = app.post_excluir_estoque({"id": 3})
    assert resultado == {"sucesso": True, "id": 3}

    itens = app.get_estoque({})
    assert all(i["id"] != 3 for i in itens)
    assert len(itens) == 2
