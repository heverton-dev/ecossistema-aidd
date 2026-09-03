class EventBus:
    def __init__(self):
        self._subscribers = {}

    def on(self, event_name: str, handler):
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append(handler)

    def emit(self, event_name: str, data: dict):
        if event_name in self._subscribers:
            for handler in self._subscribers[event_name]:
                try:
                    handler(data)
                except Exception as e:
                    print(f"[EventBus Error] Event: {event_name}, Error: {e}")
