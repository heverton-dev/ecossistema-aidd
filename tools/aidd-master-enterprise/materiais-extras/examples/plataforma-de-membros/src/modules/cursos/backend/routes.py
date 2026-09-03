def registrar_rotas(registry, service):
    @registry.get("/api/cursos", summary="Lista cursos disponíveis", tags=["Cursos"])
    def get_cursos(params):
        uid = int(params.get("usuario_id", [""])[0]) if params.get("usuario_id", [""])[0].isdigit() else None
        return service.listar(uid)

    @registry.get("/api/aulas", summary="Lista aulas de um curso", tags=["Cursos"])
    def get_aulas(params):
        cid = int(params.get("curso_id", [0])[0])
        uid = int(params.get("usuario_id", [""])[0]) if params.get("usuario_id", [""])[0].isdigit() else None
        return service.obter_aulas(cid, uid)

    @registry.post("/api/matricular", summary="Matricula aluno em um curso", tags=["Cursos"])
    def post_matricular(data):
        return service.matricular(int(data.get("usuario_id", 0)), int(data.get("curso_id", 0)))
