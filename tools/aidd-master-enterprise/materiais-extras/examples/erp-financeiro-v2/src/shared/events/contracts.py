import time, uuid
from typing import Any, Dict

def criar_envelope_evento(tipo_evento: str, dados: Dict[str, Any], modulo_origem: str = "shared") -> Dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": tipo_evento,
        "source_module": modulo_origem,
        "timestamp": int(time.time()),
        "payload": dados
    }
