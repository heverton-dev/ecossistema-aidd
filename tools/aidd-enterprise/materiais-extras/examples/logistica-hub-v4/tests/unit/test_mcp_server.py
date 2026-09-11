def test_initialize_retorna_metadados_do_servidor(app):
    resposta = app.mcp_engine.handle_json_rpc({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    assert resposta["result"]["serverInfo"]["name"] == "logistica-hub-mcp"
    assert resposta["result"]["protocolVersion"] == "2024-11-05"


def test_tools_list_expoe_ferramentas_das_5_verticais(app):
    resposta = app.mcp_engine.handle_json_rpc({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    nomes = {t["name"] for t in resposta["result"]["tools"]}
    assert "frotas_listar_veiculos" in nomes
    assert "entregas_criar_remessa" in nomes
    assert "wms_consultar_estoque" in nomes
    assert "financeiro_lancar_movimentacao" in nomes
    assert "suporte_abrir_incidente" in nomes


def test_tools_call_frotas_listar_veiculos_retorna_seeds(app):
    resposta = app.mcp_engine.handle_json_rpc({
        "jsonrpc": "2.0", "id": 3, "method": "tools/call",
        "params": {"name": "frotas_listar_veiculos", "arguments": {}}
    })
    texto = resposta["result"]["content"][0]["text"]
    assert "BRA2E19" in texto


def test_tools_call_entregas_criar_remessa_grava_no_banco(app, db_conn):
    resposta = app.mcp_engine.handle_json_rpc({
        "jsonrpc": "2.0", "id": 4, "method": "tools/call",
        "params": {
            "name": "entregas_criar_remessa",
            "arguments": {
                "destinatario": "Cliente MCP", "cidade_destino": "São Paulo/SP",
                "valor_frete": 1000.0, "peso_kg": 500.0
            }
        }
    })
    assert "Remessa criada" in resposta["result"]["content"][0]["text"]

    total = db_conn.execute(
        "SELECT COUNT(*) FROM entregas WHERE destinatario = 'Cliente MCP'"
    ).fetchone()[0]
    assert total == 1


def test_tools_call_entregas_atualizar_status_entregue_fatura_frete(app, db_conn):
    entrega = db_conn.execute("SELECT id, codigo_rastreio, valor_frete FROM entregas WHERE id = 1").fetchone()

    app.mcp_engine.handle_json_rpc({
        "jsonrpc": "2.0", "id": 5, "method": "tools/call",
        "params": {
            "name": "entregas_atualizar_status",
            "arguments": {"entrega_id": entrega["id"], "novo_status": "entregue"}
        }
    })

    lancamento = db_conn.execute(
        "SELECT * FROM fretes_financeiro WHERE descricao LIKE ?",
        (f"%{entrega['codigo_rastreio']}%",)
    ).fetchone()
    assert lancamento is not None
    assert lancamento["valor"] == entrega["valor_frete"]
    assert lancamento["status"] == "pago"


def test_tools_call_frotas_alternar_status_id_inexistente_retorna_erro(app):
    resposta = app.mcp_engine.handle_json_rpc({
        "jsonrpc": "2.0", "id": 6, "method": "tools/call",
        "params": {"name": "frotas_alternar_status", "arguments": {"id": 99999}}
    })
    assert resposta["result"]["isError"] is True


def test_tools_call_ferramenta_desconhecida_retorna_erro(app):
    resposta = app.mcp_engine.handle_json_rpc({
        "jsonrpc": "2.0", "id": 7, "method": "tools/call",
        "params": {"name": "ferramenta_que_nao_existe", "arguments": {}}
    })
    assert resposta["result"]["isError"] is True


def test_metodo_rpc_desconhecido_retorna_erro_jsonrpc(app):
    resposta = app.mcp_engine.handle_json_rpc({"jsonrpc": "2.0", "id": 8, "method": "metodo/invalido"})
    assert resposta["error"]["code"] == -32601
