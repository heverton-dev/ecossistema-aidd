def test_get_veiculos_retorna_seeds(app):
    veiculos = app.get_veiculos({})
    assert len(veiculos) == 3
    placas = {v["placa"] for v in veiculos}
    assert {"BRA2E19", "KLP9A88", "RFT4C22"}.issubset(placas)


def test_post_salvar_veiculo_insere_e_normaliza_placa(app):
    resultado = app.post_salvar_veiculo({
        "placa": "xyz9b88",
        "modelo": "Mercedes-Benz Actros 2651",
        "motorista": "Fernando Dias",
        "capacidade_kg": 35000.0,
    })

    assert resultado == {"sucesso": True, "placa": "XYZ9B88"}

    veiculos = app.get_veiculos({})
    novo = next(v for v in veiculos if v["placa"] == "XYZ9B88")
    assert novo["motorista"] == "Fernando Dias"
    assert novo["status"] == "disponivel"
    assert len(veiculos) == 4


def test_post_alternar_veiculo_cicla_status(app):
    r1 = app.post_alternar_veiculo({"id": 1})
    assert r1 == {"sucesso": True, "status": "em_rota"}

    r2 = app.post_alternar_veiculo({"id": 1})
    assert r2 == {"sucesso": True, "status": "manutencao"}

    r3 = app.post_alternar_veiculo({"id": 1})
    assert r3 == {"sucesso": True, "status": "disponivel"}


def test_post_alternar_veiculo_id_inexistente(app):
    resultado = app.post_alternar_veiculo({"id": 99999})
    assert resultado == {"sucesso": False, "erro": "Veículo não encontrado"}


def test_alternar_para_manutencao_abre_incidente_sla_p1(app, db_conn):
    app.post_alternar_veiculo({"id": 1})  # disponivel -> em_rota
    app.post_alternar_veiculo({"id": 1})  # em_rota -> manutencao

    incidentes = db_conn.execute(
        "SELECT * FROM incidentes_sla WHERE veiculo_placa = 'BRA2E19'"
    ).fetchall()
    assert len(incidentes) == 1
    incidente = incidentes[0]
    assert incidente["prioridade"] == "P1"
    assert incidente["sla_horas"] == 2
    assert incidente["status"] == "aberto"
    assert "BRA2E19" in incidente["titulo"]


def test_post_excluir_veiculo_remove_do_banco(app):
    resultado = app.post_excluir_veiculo({"id": 2})
    assert resultado == {"sucesso": True, "id": 2}

    veiculos = app.get_veiculos({})
    assert all(v["id"] != 2 for v in veiculos)
    assert len(veiculos) == 2
