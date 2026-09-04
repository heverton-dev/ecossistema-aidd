from core.openapi import RouteRegistry

registry = RouteRegistry()

def registrar_rotas(service):
    @registry.get("/api/cupons", summary="Lista todos os itens do modulo cupons")
    def listar(params):
        return service.listar()

    @registry.post("/api/cupons", summary="Cria um novo item no modulo cupons")
    def criar(data):
        return service.criar(data.get("titulo", ""), data.get("dados", {}))

    @registry.post("/api/cupons/deletar", summary="Remove um item do modulo cupons")
    def deletar(data):
        return service.deletar(int(data.get("id", 0)))
