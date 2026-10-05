"""Orquestrador de correcoes de conformidade (forge conform).

Le o resultado de um AuditReport, filtra itens fixaveis, e aplica os
fixers correspondentes com backup e rollback. Deterministico, zero LLM.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from aidd_forge.core.audit_engine import AuditEngine, AuditReport
from aidd_forge.core.conform_fixers import ConformFix, FIXER_MAP


@dataclass
class ConformReport:
    """Resultado agregado de uma execucao de correcao de conformidade."""

    fixes: list[ConformFix] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)  # audit_item_ids nao fixaveis

    @property
    def total_fixes(self) -> int:
        return len(self.fixes)

    @property
    def successful_fixes(self) -> int:
        return sum(1 for f in self.fixes if f.success)

    @property
    def failed_fixes(self) -> int:
        return sum(1 for f in self.fixes if not f.success)

    @property
    def all_files_touched(self) -> list[str]:
        files: list[str] = []
        for fix in self.fixes:
            files.extend(fix.files_touched)
        return sorted(set(files))

    def summary(self) -> str:
        """Resumo em texto plano para output no CLI."""
        lines: list[str] = []
        lines.append(f"[forge conform] audit items fixable: {self.total_fixes}")
        lines.append(f"[forge conform] successful: {self.successful_fixes}")
        if self.failed_fixes:
            lines.append(f"[forge conform] failed: {self.failed_fixes}")
        if self.skipped:
            lines.append(f"[forge conform] skipped (not auto-fixable): {len(self.skipped)}")
        if self.all_files_touched:
            lines.append(f"[forge conform] files touched: {', '.join(self.all_files_touched)}")

        for fix in self.fixes:
            status = "OK" if fix.success else "FAIL"
            lines.append(f"  [{status}] {fix.audit_item_id}: {fix.description}")
            if fix.error:
                lines.append(f"         error: {fix.error}")

        return "\n".join(lines)


class ConformEngine:
    """Executa correcoes de conformidade sobre um projeto."""

    def __init__(self, project_path: Path, audit_report: AuditReport | None = None):
        self.project_path = Path(project_path).resolve()
        self._audit_report = audit_report

    def run(
        self,
        dry_run: bool = False,
        item_filter: list[int] | None = None,
    ) -> ConformReport:
        """Executa as correcoes.

        Args:
            dry_run: Se True, apenas reporta o que seria feito sem escrever.
            item_filter: Se fornecido, aplica fix apenas nos IDs deste item.
        """
        if self._audit_report is None:
            self._audit_report = AuditEngine(self.project_path).run()

        report = ConformReport()

        for item in self._audit_report.items:
            if item.status == "PASS":
                continue

            if item.id not in FIXER_MAP:
                report.skipped.append(item.id)
                continue

            if item_filter is not None:
                try:
                    item_num = int(item.id.replace("G", ""))
                except ValueError:
                    report.skipped.append(item.id)
                    continue
                if item_num not in item_filter:
                    report.skipped.append(item.id)
                    continue

            if not item.fixable:
                report.skipped.append(item.id)
                continue

            if dry_run:
                report.fixes.append(ConformFix(
                    audit_item_id=item.id,
                    description=f"[DRY-RUN] Would fix: {item.requirement}",
                    files_touched=[],
                    success=True,
                ))
                continue

            fixer = FIXER_MAP[item.id]
            try:
                fix = fixer(self.project_path)
                report.fixes.append(fix)
            except Exception as exc:
                report.fixes.append(ConformFix(
                    audit_item_id=item.id,
                    description=f"Fixer raised exception: {exc}",
                    files_touched=[],
                    success=False,
                    error=str(exc),
                ))

        return report
