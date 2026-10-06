import hashlib
import hmac
import json


def test_get_webhooks_vazio_por_padrao(app):
    assert app.get_webhooks({}) == []


def test_post_criar_webhook_insere_registro(app):
    resultado = app.post_criar_webhook({
        "nome": "ERP Liquidação",
        "url": "https://webhook.exemplo.com/preview",
        "secret": "sec_hub_v4_secret",
        "eventos": '["*"]',
        "retry_count": 3,
    })
    assert resultado["sucesso"] is True
    assert "id" in resultado

    webhooks = app.get_webhooks({})
    assert len(webhooks) == 1
    assert webhooks[0]["nome"] == "ERP Liquidação"
    assert webhooks[0]["ativo"] == 1


def test_post_atualizar_webhook_altera_campos(app):
    criado = app.post_criar_webhook({"nome": "Original", "url": "https://a.exemplo.com"})
    wid = criado["id"]

    resultado = app.post_atualizar_webhook({
        "id": wid, "nome": "Renomeado", "url": "https://b.exemplo.com",
        "secret": "novo_secret", "eventos": '["frotas.*"]', "retry_count": 5,
    })
    assert resultado == {"sucesso": True}

    webhook = app.get_webhooks({})[0]
    assert webhook["nome"] == "Renomeado"
    assert webhook["url"] == "https://b.exemplo.com"
    assert webhook["retry_count"] == 5


def test_post_toggle_webhook_alterna_ativo(app):
    criado = app.post_criar_webhook({"nome": "X", "url": "https://x.exemplo.com"})
    wid = criado["id"]

    r1 = app.post_toggle_webhook({"id": wid})
    assert r1 == {"sucesso": True, "ativo": 0}

    r2 = app.post_toggle_webhook({"id": wid})
    assert r2 == {"sucesso": True, "ativo": 1}


def test_post_toggle_webhook_id_inexistente(app):
    resultado = app.post_toggle_webhook({"id": 99999})
    assert resultado == {"sucesso": False, "error": "Webhook não encontrado"}


def test_post_excluir_webhook_remove_registro(app):
    criado = app.post_criar_webhook({"nome": "Y", "url": "https://y.exemplo.com"})
    wid = criado["id"]

    resultado = app.post_excluir_webhook({"id": wid})
    assert resultado == {"sucesso": True, "id": wid}
    assert app.get_webhooks({}) == []


def test_post_testar_webhook_entrega_de_verdade_e_assina_hmac(app, webhook_receiver):
    url, recebidos = webhook_receiver

    resultado = app.post_testar_webhook({
        "url": url,
        "secret": "sec_demo",
        "evento": "cross_domain.entrega_to_financeiro",
        "payload": {"codigo_rastreio": "BR-LOG-9821", "valor_frete": 8500.0},
    })

    assert resultado["sucesso"] is True
    assert resultado["status_code"] == 200
    assert resultado["duracao_ms"] > 0
    assert resultado["signature"]

    assert len(recebidos) == 1
    corpo_recebido = json.loads(recebidos[0]["body"])
    assert corpo_recebido["event"] == "cross_domain.entrega_to_financeiro"
    assert corpo_recebido["data"]["codigo_rastreio"] == "BR-LOG-9821"

    assinatura_esperada = hmac.new(
        b"sec_demo", recebidos[0]["body"], hashlib.sha256
    ).hexdigest()
    assert recebidos[0]["headers"]["X-Webhook-Signature"] == assinatura_esperada
    assert resultado["signature"] == assinatura_esperada


def test_post_testar_webhook_sem_url_retorna_erro(app):
    resultado = app.post_testar_webhook({"evento": "x", "payload": {}})
    assert resultado == {"sucesso": False, "error": "URL de destino obrigatória"}


def test_post_testar_webhook_url_inalcancavel_registra_falha(app):
    resultado = app.post_testar_webhook({
        "url": "http://127.0.0.1:1/endpoint-inexistente",
        "evento": "teste.falha",
        "payload": {},
    })
    assert resultado["sucesso"] is False
    assert resultado["status_code"] is None

    logs = app.get_webhook_logs({})
    assert logs[0]["status"] in ("falha", "timeout")


def test_testar_disparo_registra_log_consultavel_por_status(app, webhook_receiver):
    url, _ = webhook_receiver
    app.post_testar_webhook({"url": url, "evento": "wms.item_adicionado", "payload": {"sku": "SKU-1"}})

    logs_sucesso = app.get_webhook_logs({"status": ["sucesso"]})
    assert len(logs_sucesso) == 1
    assert logs_sucesso[0]["evento"] == "wms.item_adicionado"

    logs_falha = app.get_webhook_logs({"status": ["falha"]})
    assert logs_falha == []


def test_post_reenviar_webhook_log_reenvia_payload_original(app, webhook_receiver):
    url, recebidos = webhook_receiver
    app.post_testar_webhook({"url": url, "evento": "suporte.incidente_aberto", "payload": {"protocolo": "INC-0001"}})
    log_id = app.get_webhook_logs({})[0]["id"]

    resultado = app.post_reenviar_webhook_log({"log_id": log_id})
    assert resultado["sucesso"] is True
    assert resultado["detalhes"]["sucesso"] is True

    assert len(recebidos) == 2
    for recebido in recebidos:
        corpo = json.loads(recebido["body"])
        assert corpo["data"]["protocolo"] == "INC-0001"


def test_post_reenviar_webhook_log_id_inexistente(app):
    resultado = app.post_reenviar_webhook_log({"log_id": 99999})
    assert resultado == {"sucesso": False, "error": "Log não encontrado"}


def test_get_webhook_eventos_e_catalog_expoem_catalogo_completo(app):
    eventos = app.get_webhook_eventos({})
    catalogo = app.get_webhook_catalog({})
    assert eventos == catalogo
    assert len(eventos) > 0
    nomes_evento = {e["event"] for e in eventos}
    assert "cross_domain.entrega_to_financeiro" in nomes_evento
    assert "frotas.manutencao_alerta" in nomes_evento
