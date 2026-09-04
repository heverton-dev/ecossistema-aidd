import threading

class EventBus:
    def __init__(self):
        self._listeners = {}

    def on(self, event_name: str, handler):
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        self._listeners[event_name].append(handler)

    def emit(self, event_name: str, data: dict):
        if event_name in self._listeners:
            for h in self._listeners[event_name]:
                threading.Thread(target=h, args=(data,), daemon=True).start()
