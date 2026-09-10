import json, hashlib, time
from typing import List, Dict, Any

class CRDTSet:
    """Grow-Only Set CRDT: registros criados offline são acumulados e fundidos sem conflito."""
    def __init__(self, node_id: str):
        self.node_id = node_id
        self._items: Dict[str, dict] = {}

    def add(self, record: dict) -> str:
        key = hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()[:16]
        if key not in self._items:
            self._items[key] = {**record, "_crdt_key": key, "_node": self.node_id, "_ts": time.time()}
        return key

    def merge(self, other: "CRDTSet") -> "CRDTSet":
        """Merge de dois nós: união determinística sem conflitos."""
        merged = CRDTSet(self.node_id)
        merged._items = {**self._items, **other._items}
        return merged

    def to_list(self) -> List[dict]:
        return sorted(self._items.values(), key=lambda x: x["_ts"])

    def pending_sync(self, synced_keys: List[str]) -> List[dict]:
        """Retorna registros ainda não sincronizados com o servidor."""
        return [v for k, v in self._items.items() if k not in synced_keys]
