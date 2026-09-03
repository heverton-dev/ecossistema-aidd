import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from core.database import Database
from core.events import EventBus

def test_arquitetura_modular_crm_vendas_omnichannel(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'test_crm-vendas-omnichannel.db'}")
    events = EventBus()
    eventos_capturados = []
    events.on("evento_teste", lambda d: eventos_capturados.append(d))
    events.emit("evento_teste", {"status": "OK"})
    assert len(eventos_capturados) == 1
    assert eventos_capturados[0]["status"] == "OK"
