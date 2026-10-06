import time
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 5, timeout: int = 60):
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self._failures = 0
        self._state = CircuitState.CLOSED
        self._opened_at = None

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.time() - self._opened_at >= self.timeout:
                self._state = CircuitState.HALF_OPEN
        return self._state

    def call(self, fn, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            raise RuntimeError(f"CircuitBreaker '{self.name}' OPEN — fast fail.")
        try:
            result = fn(*args, **kwargs)
            self._failures = 0
            self._state = CircuitState.CLOSED
            return result
        except Exception as e:
            self._failures += 1
            if self._failures >= self.failure_threshold:
                self._state = CircuitState.OPEN
                self._opened_at = time.time()
            raise
