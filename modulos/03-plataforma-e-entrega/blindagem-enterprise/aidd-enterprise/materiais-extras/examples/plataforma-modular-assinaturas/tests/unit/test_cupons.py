import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from core.database import Database
from core.events import EventBus
from modules.cupons.services import CuponsService
from modules.cupons.models import init_schema

def test_modulo_cupons(tmp_path):
    db_file = str(tmp_path / "test_cupons.db")
    db = Database(db_file)
    with db.get_connection() as conn:
        init_schema(conn)
        
    events = EventBus()
    eventos_recebidos = []
    events.on("cupons_criado", lambda d: eventos_recebidos.append(d))

    service = CuponsService(db, events)
    
    # Criar
    res = service.criar("Item Teste Cupons", {"valor": 100})
    assert res["sucesso"] is True
    assert len(eventos_recebidos) == 1
    
    # Listar
    itens = service.listar()
    assert len(itens) == 1
    assert itens[0]["titulo"] == "Item Teste Cupons"
    
    # Deletar
    del_res = service.deletar(res["id"])
    assert del_res["sucesso"] is True
    assert len(service.listar()) == 0
