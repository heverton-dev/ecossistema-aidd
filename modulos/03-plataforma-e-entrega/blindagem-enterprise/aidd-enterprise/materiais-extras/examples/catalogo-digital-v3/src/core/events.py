from collections import defaultdict
from typing import Callable, Any

class EventBus:
    def __init__(self):
        self._listeners = defaultdict(list)

    def on(self, event_name: str, handler: Callable[[Any], None]):
        self._listeners[event_name].append(handler)

    def emit(self, event_name: str, data: Any = None):
        for handler in self._listeners.get(event_name, []):
            try:
                handler(data)
            except Exception as e:
                print(f"[EVENT_ERROR] Erro no listener do evento '{event_name}': {e}")
