import json


def test_get_entregas_retorna_seeds(app):
    entregas = app.get_entregas({})
    assert len(entregas) == 2
    codigos = {e["codigo_rastreio"] for e in entregas}
    assert {"BR-LOG-9821", "BR-LOG-4310"}.issubset(codigos)


def test_post_salvar_entrega_gera_codigo_rastreio_unico(app):
    resultado = app.post_salvar_entrega({
        "destinatario": "BioTech Farmacêutica",
        "cidade_destino": "Ribeirão Preto/SP",
        "valor_frete": 9200.0,
        "peso_kg": 16000.0,
    })

    assert resultado["sucesso"] is True
    assert resultado["codigo_rastreio"].startswith("BR-LOG-")

    entregas = app.get_entregas({})
    nova = next(e for e in entregas if e["codigo_rastreio"] == resultado["codigo_rastreio"])
    assert nova["status"] == "pendente"
    assert nova["destinatario"] == "BioTech Farmacêutica"
    assert len(entregas) == 3


def test_post_finalizar_entrega_marca_status_entregue(app):
    resultado = app.post_finalizar_entrega({"id": 2})
    assert resultado == {"sucesso": True, "status": "entregue"}

    entrega = next(e for e in app.get_entregas({}) if e["id"] == 2)
    assert entrega["status"] == "entregue"


def test_finalizar_entrega_lanca_frete_no_financeiro_cross_domain(app, db_conn):
    app.post_finalizar_entrega({"id": 2})  # BR-LOG-4310, valor_frete=14200.0

    lancamento = db_conn.execute(
        "SELECT * FROM fretes_financeiro WHERE descricao LIKE 'Frete Liquidado: BR-LOG-4310%'"
    ).fetchone()
    assert lancamento is not None
    assert lancamento["tipo"] == "receita"
    assert lancamento["valor"] == 14200.0
    assert lancamento["status"] == "pago"
    assert lancamento["categoria"] == "Fretes"

    log_auditoria = db_conn.execute(
        "SELECT * FROM logs_auditoria WHERE evento = 'entrega_liquidada'"
    ).fetchone()
    assert log_auditoria is not None
    assert log_auditoria["modulo"] == "financeiro"
    payload = json.loads(log_auditoria["payload_json"])
    assert payload["codigo_rastreio"] == "BR-LOG-4310"


def test_finalizar_entrega_inexistente_nao_lanca_financeiro(app, db_conn):
    resultado = app.post_finalizar_entrega({"id": 99999})
    assert resultado == {"sucesso": True, "status": "entregue"}

    total_fretes = db_conn.execute("SELECT COUNT(*) FROM fretes_financeiro").fetchone()[0]
    assert total_fretes == 3  # apenas os 3 seeds, nenhum lançamento cross-domain novo


def test_post_excluir_entrega_remove_do_banco(app):
    resultado = app.post_excluir_entrega({"id": 1})
    assert resultado == {"sucesso": True, "id": 1}

    entregas = app.get_entregas({})
    assert all(e["id"] != 1 for e in entregas)
    assert len(entregas) == 1
