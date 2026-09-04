from core.openapi import RouteRegistry

registry = RouteRegistry()

def registrar_rotas(service):
    @registry.get("/api/afiliados", summary="Lista todos os itens do modulo afiliados")
    def listar(params):
        return service.listar()

    @registry.post("/api/afiliados", summary="Cria um novo item no modulo afiliados")
    def criar(data):
        return service.criar(data.get("titulo", ""), data.get("dados", {}))

    @registry.post("/api/afiliados/deletar", summary="Remove um item do modulo afiliados")
    def deletar(data):
        return service.deletar(int(data.get("id", 0)))
