def registrar_rotas(registry, service):
    @registry.get("/api/produtos", summary="Lista catálogo de produtos com filtros (Compatível com n8n)", tags=["Produtos"])
    def get_produtos(params):
        cat = params.get("categoria", [None])[0]
        busca = params.get("busca", [None])[0]
        admin = params.get("admin", ["0"])[0] == "1"
        return service.listar(cat, busca, apenas_ativos=not admin)

    @registry.post("/api/admin/salvar-produto", summary="Cria ou edita produto (Compatível com n8n webhook)", tags=["Produtos"])
    def post_salvar(data):
        return service.salvar(data)

    @registry.post("/api/admin/deletar-produto", summary="Exclui produto pelo ID", tags=["Produtos"])
    def post_del(data):
        return service.deletar(int(data.get("id", 0)))
