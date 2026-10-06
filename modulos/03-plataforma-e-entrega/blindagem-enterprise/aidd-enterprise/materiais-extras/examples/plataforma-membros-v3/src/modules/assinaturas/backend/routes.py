def registrar_rotas(registry, service):
    @registry.get("/api/planos", summary="Lista os planos de assinatura disponíveis", tags=["Assinaturas"])
    def get_planos(params):
        return service.listar_planos()

    @registry.post("/api/assinar", summary="Ativa assinatura de um plano (Dispara Webhook n8n)", tags=["Assinaturas"])
    def post_assinar(data):
        return service.assinar_plano(int(data.get("usuario_id", 0)), data.get("plano_slug", "pro"))
