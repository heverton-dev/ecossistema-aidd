import os, pytest, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from services import PlataformaService

def test_fluxo_completo_plataforma(tmp_path):
    db_file = str(tmp_path / "test_plataforma.db")
    service = PlataformaService(db_file)
    service.seed_dados_iniciais()

    # 1. Cadastro
    cad = service.cadastrar_usuario("Heverton Peres", "heverton@teste.com", "senha123")
    assert cad["sucesso"] is True
    uid = cad["usuario_id"]

    # 2. Login
    login_ok = service.autenticar("heverton@teste.com", "senha123")
    assert login_ok["sucesso"] is True
    assert login_ok["usuario"]["nome"] == "Heverton Peres"

    # 3. Login com senha errada
    login_fail = service.autenticar("heverton@teste.com", "senha_errada")
    assert login_fail["sucesso"] is False

    # 4. Listar cursos
    cursos = service.listar_cursos(uid)
    assert len(cursos) == 3
    assert cursos[0]["matriculado"] is False

    # 5. Matrícula
    cid = cursos[0]["id"]
    mat = service.matricular(uid, cid)
    assert mat["sucesso"] is True

    # 6. Cursos pós-matrícula
    cursos_pos = service.listar_cursos(uid)
    assert cursos_pos[0]["matriculado"] is True

    # 7. Aulas e Progresso
    aulas = service.obter_aulas(cid, uid)
    assert len(aulas) > 0
    assert aulas[0]["concluida"] is False

    # Marcar aula como concluída
    prog = service.alternar_progresso_aula(uid, aulas[0]["id"])
    assert prog["concluida"] is True

    aulas_pos = service.obter_aulas(cid, uid)
    assert aulas_pos[0]["concluida"] is True
