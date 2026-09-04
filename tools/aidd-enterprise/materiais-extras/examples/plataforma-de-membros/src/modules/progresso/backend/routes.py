def registrar_rotas(registry, service):
    @registry.post("/api/progresso", summary="Marca/desmarca conclusão de aula (Dispara Webhook n8n)", tags=["Progresso"])
    def post_progresso(data):
        return service.alternar_progresso(int(data.get("usuario_id", 0)), int(data.get("aula_id", 0)))
