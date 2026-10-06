import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from core.database import Database
from core.events import EventBus
from modules.auth.backend.services import AuthService
from modules.auth.backend.models import init_schema as init_auth
from modules.assinaturas.backend.services import AssinaturasService
from modules.assinaturas.backend.models import init_schema as init_ass
from modules.cursos.backend.services import CursosService
from modules.cursos.backend.models import init_schema as init_cur
from modules.progresso.backend.services import ProgressoService
from modules.progresso.backend.models import init_schema as init_prog

def test_vertical_slices_plataforma(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'test_platform.db'}")
    with db.get_connection() as conn:
        init_auth(conn)
        init_ass(conn)
        init_cur(conn)
        init_prog(conn)

    events = EventBus()
    eventos = []
    events.on("usuario_cadastrado", lambda d: eventos.append(("cadastrado", d)))
    events.on("assinatura_ativada", lambda d: eventos.append(("assinado", d)))

    auth = AuthService(db, events)
    ass = AssinaturasService(db, events)
    cursos = CursosService(db, events)
    prog = ProgressoService(db, events)

    ass.seed_planos()
    cursos.seed_iniciais()

    # 1. Cadastro
    cad = auth.cadastrar("Assinante VIP", "vip@teste.com", "senha123")
    assert cad["sucesso"] is True
    uid = cad["usuario_id"]
    assert len(eventos) == 1

    # 2. Listar planos & Assinar
    planos = ass.listar_planos()
    assert len(planos) == 2
    res_ass = ass.assinar_plano(uid, "pro")
    assert res_ass["sucesso"] is True
    assert len(eventos) == 2

    # 3. Matricula em curso
    mat = cursos.matricular(uid, 1)
    assert mat["sucesso"] is True

    # 4. Progresso de aula
    p = prog.alternar_progresso(uid, 1)
    assert p["concluida"] is True
