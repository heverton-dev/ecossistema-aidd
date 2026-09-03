def registrar_rotas(registry, service):
    @registry.post("/api/checkout-whatsapp", summary="Gera link de WhatsApp e grava pedido (Dispara Webhook n8n)", tags=["Pedidos"])
    def post_checkout(data):
        return service.checkout_whatsapp(data.get("itens", []), data.get("cliente_nome", "Cliente"))
