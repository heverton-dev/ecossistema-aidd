"""Orquestrador de auditoria de conformidade de governanca.

Executa todos os checkers de `audit_checks.py` sobre um projeto alvo e
agrega os resultados num `AuditReport` estruturado. Deterministico, zero LLM.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from aidd_forge.core.audit_checks import ALL_CHECKS, AuditItem


@dataclass
class AuditReport:
    """Resultado agregado de uma auditoria de conformidade."""

    project_path: Path
    items: list[AuditItem] = field(default_factory=list)
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    @property
    def total(self) -> int:
        return len(self.items)

    @property
    def passed(self) -> int:
        return sum(1 for i in self.items if i.status == "PASS")

    @property
    def failed(self) -> int:
        return sum(1 for i in self.items if i.status == "FAIL")

    @property
    def warned(self) -> int:
        return sum(1 for i in self.items if i.status == "WARN")

    @property
    def skipped(self) -> int:
        return sum(1 for i in self.items if i.status == "SKIP")

    @property
    def compliance_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return (self.passed / self.total) * 100.0

    @property
    def fixable_count(self) -> int:
        return sum(
            1 for i in self.items
            if i.fixable and i.status != "PASS"
        )

    @property
    def fixable_items(self) -> list[AuditItem]:
        return [
            i for i in self.items
            if i.fixable and i.status != "PASS"
        ]


class AuditEngine:
    """Executa a auditoria completa de conformidade sobre um projeto."""

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path).resolve()

    def run(self) -> AuditReport:
        """Executa todos os checks e retorna o relatorio."""
        report = AuditReport(project_path=self.project_path)

        for check_fn in ALL_CHECKS:
            try:
                item = check_fn(self.project_path)
                report.items.append(item)
            except Exception as exc:
                report.items.append(AuditItem(
                    id="ERR",
                    category="System",
                    requirement=f"Check {check_fn.__name__} did not raise",
                    status="FAIL",
                    details=f"checker raised: {exc}",
                    impact="HIGH",
                    fixable=False,
                ))

        return report
