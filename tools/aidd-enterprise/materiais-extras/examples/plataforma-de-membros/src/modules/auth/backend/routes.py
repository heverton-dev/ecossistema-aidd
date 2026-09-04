def registrar_rotas(registry, service):
    @registry.post("/api/login", summary="Autenticação de aluno/assinante", tags=["Autenticação"])
    def post_login(data):
        return service.autenticar(data.get("email", ""), data.get("senha", ""))

    @registry.post("/api/cadastro", summary="Cadastro de novo aluno (Dispara Webhook n8n)", tags=["Autenticação"])
    def post_cadastro(data):
        return service.cadastrar(data.get("nome", ""), data.get("email", ""), data.get("senha", ""))
