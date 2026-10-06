def registrar_rotas(registry, service):
    @registry.get("/api/config", summary="Obtém configurações da loja", tags=["Configuração"])
    def get_config(params):
        return service.obter()

    @registry.post("/api/login-admin", summary="Autenticação de administrador", tags=["Configuração"])
    def post_login(data):
        return service.autenticar_admin(data.get("email", ""), data.get("senha", ""))
