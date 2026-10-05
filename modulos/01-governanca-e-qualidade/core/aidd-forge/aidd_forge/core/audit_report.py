"""Geradores de relatorio de auditoria: JSON, Markdown e HTML.

Cada funcao recebe um `AuditReport` e retorna uma string formatada.
O JSON segue o schema dos relatorios existentes em docs/relatorios/.
O HTML usa template embutido (str.format, zero dependencias externas).
"""

from __future__ import annotations

import json
from pathlib import Path

from aidd_forge.core.audit_engine import AuditReport

TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


def to_json(report: AuditReport) -> str:
    """Serializa o AuditReport como JSON seguindo o schema dos relatorios."""
    data = {
        "metadata": {
            "titulo": "Auditoria de Conformidade de Governanca (forge audit)",
            "data": report.timestamp,
            "autor": "aidd-forge",
            "versao": "1.0.0",
            "status_geral": _status_geral(report),
            "taxa_conformidade": f"{report.compliance_rate:.1f}%",
            "projeto": str(report.project_path),
        },
        "kpis": {
            "total_itens": report.total,
            "conformes": report.passed,
            "nao_conformes": report.failed,
            "avisos": report.warned,
            "ignorados": report.skipped,
            "auto_fixaveis": report.fixable_count,
        },
        "itens": [_item_to_dict(item) for item in report.items],
    }
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def to_markdown(report: AuditReport) -> str:
    """Gera relatorio em Markdown seguindo o estilo dos relatorios existentes."""
    lines: list[str] = []
    lines.append("# Relatorio de Auditoria de Conformidade (forge audit)\n")
    lines.append(f"> **Status:** {_status_geral(report)}")
    lines.append(f"> **Data:** {report.timestamp}")
    lines.append(f"> **Projeto:** `{report.project_path}`")
    lines.append(f"> **Taxa de Conformidade:** {report.compliance_rate:.1f}%")
    lines.append("")

    # KPIs
    lines.append("## KPIs\n")
    lines.append(f"| Metrica | Valor |")
    lines.append(f"| :--- | :---: |")
    lines.append(f"| Total de Itens | {report.total} |")
    lines.append(f"| Conformes (PASS) | {report.passed} |")
    lines.append(f"| Nao Conformes (FAIL) | {report.failed} |")
    lines.append(f"| Avisos (WARN) | {report.warned} |")
    lines.append(f"| Ignorados (SKIP) | {report.skipped} |")
    lines.append(f"| Auto-fixaveis | {report.fixable_count} |")
    lines.append("")

    # Tabela de itens
    lines.append("## Detalhamento dos Itens\n")
    lines.append("| ID | Categoria | Requisito | Status | Impacto | Detalhes |")
    lines.append("| :---: | :--- | :--- | :---: | :---: | :--- |")
    for item in report.items:
        status_badge = _status_badge(item.status)
        lines.append(
            f"| {item.id} | {item.category} | {item.requirement} "
            f"| {status_badge} | {item.impact} | {item.details} |"
        )
    lines.append("")

    # Itens fixaveis
    fixable = report.fixable_items
    if fixable:
        lines.append("## Itens Auto-fixaveis (forge conform)\n")
        for item in fixable:
            lines.append(f"- **{item.id}** ({item.category}): {item.requirement}")
        lines.append("")

    return "\n".join(lines)


def to_html(report: AuditReport) -> str:
    """Gera relatorio HTML a partir do template embutido."""
    template_path = TEMPLATE_DIR / "audit_report.html"
    if not template_path.exists():
        return _fallback_html(report)

    template = template_path.read_text(encoding="utf-8")
    items_html = _render_items_html(report)
    fixable_html = _render_fixable_html(report)

    gauge_class = "good" if report.compliance_rate >= 80 else ("warn" if report.compliance_rate >= 50 else "bad")

    return template.format(
        titulo="Auditoria de Conformidade de Governanca (forge audit)",
        data=report.timestamp,
        projeto=report.project_path,
        status_geral=_status_geral(report),
        taxa_conformidade=f"{report.compliance_rate:.1f}",
        taxa_width=f"{report.compliance_rate:.0f}",
        gauge_class=gauge_class,
        total=report.total,
        passed=report.passed,
        failed=report.failed,
        warned=report.warned,
        skipped=report.skipped,
        fixable_count=report.fixable_count,
        items_html=items_html,
        fixable_html=fixable_html,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _status_geral(report: AuditReport) -> str:
    if report.compliance_rate >= 80:
        return "CONFORME"
    if report.compliance_rate >= 50:
        return "PARCIALMENTE_CONFORME"
    return "NAO_CONFORME"


def _status_badge(status: str) -> str:
    badges = {
        "PASS": "PASS",
        "FAIL": "FAIL",
        "WARN": "WARN",
        "SKIP": "SKIP",
    }
    return badges.get(status, status)


def _item_to_dict(item: object) -> dict:
    return {
        "id": item.id,
        "categoria": item.category,
        "requisito": item.requirement,
        "status": item.status,
        "detalhes": item.details,
        "impacto": item.impact,
        "fixavel": item.fixable,
    }


def _render_items_html(report: AuditReport) -> str:
    rows: list[str] = []
    for item in report.items:
        row_class = {
            "PASS": "row-pass",
            "FAIL": "row-fail",
            "WARN": "row-warn",
            "SKIP": "row-skip",
        }.get(item.status, "")
        rows.append(
            f'<tr class="{row_class}">'
            f"<td>{item.id}</td>"
            f"<td>{item.category}</td>"
            f"<td>{item.requirement}</td>"
            f'<td><span class="badge badge-{item.status.lower()}">{item.status}</span></td>'
            f"<td>{item.impact}</td>"
            f"<td>{item.details}</td>"
            f"</tr>"
        )
    return "\n".join(rows)


def _render_fixable_html(report: AuditReport) -> str:
    fixable = report.fixable_items
    if not fixable:
        return "<p>Nenhum item auto-fixavel detectado.</p>"
    items = "\n".join(
        f"<li><strong>{i.id}</strong> ({i.category}): {i.requirement}</li>"
        for i in fixable
    )
    return f"<ul>{items}</ul>"


def _fallback_html(report: AuditReport) -> str:
    """Fallback caso o template HTML nao seja encontrado."""
    return (
        "<!doctype html><html><body>"
        f"<h1>forge audit - {report.project_path}</h1>"
        f"<p>Status: {_status_geral(report)} | "
        f"Conformidade: {report.compliance_rate:.1f}%</p>"
        "<p>(template HTML nao encontrado, usando fallback)</p>"
        "</body></html>"
    )
