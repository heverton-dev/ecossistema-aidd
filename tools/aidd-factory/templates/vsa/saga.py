import uuid, json
from dataclasses import dataclass, field
from typing import Callable, List

@dataclass
class SagaStep:
    name: str
    execute: Callable
    compensate: Callable

class SagaOrchestrator:
    def __init__(self, steps: List[SagaStep]):
        self.steps = steps
        self.executed: List[SagaStep] = []
        self.saga_id = str(uuid.uuid4())

    def run(self, context: dict) -> dict:
        for step in self.steps:
            try:
                context = step.execute(context) or context
                self.executed.append(step)
            except Exception as exc:
                context['saga_error'] = str(exc)
                context['saga_id'] = self.saga_id
                for s in reversed(self.executed):
                    try:
                        s.compensate(context)
                    except Exception:
                        pass
                raise RuntimeError(f"Saga '{step.name}' falhou. Compensações executadas. saga_id={self.saga_id}") from exc
        context['saga_id'] = self.saga_id
        return context
