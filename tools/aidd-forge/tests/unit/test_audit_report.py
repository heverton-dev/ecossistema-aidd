"""Testes unitarios dos geradores de relatorio (audit_report.py)."""

import json
from pathlib import Path

import pytest

from aidd_forge.core.audit_engine import AuditEngine
from aidd_forge.core.audit_report import to_html, to_json, to_markdown


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@pytest.fixture
def report(tmp_path: Path):
    _write(tmp_path / "AGENTS.md", "# Rules\n")
    _write(tmp_path / ".gitignore", "node_modules/\n")
    engine = AuditEngine(tmp_path)
    return engine.run()


# --- JSON output -------------------------------------------------------------


def test_to_json_is_valid_json(report) -> None:
    output = to_json(report)
    data = json.loads(output)
    assert "metadata" in data
    assert "kpis" in data
    assert "itens" in data


def test_to_json_metadata_fields(report) -> None:
    output = to_json(report)
    data = json.loads(output)
    meta = data["metadata"]
    assert "titulo" in meta
    assert "data" in meta
    assert "taxa_conformidade" in meta


def test_to_json_kpis(report) -> None:
    output = to_json(report)
    data = json.loads(output)
    kpis = data["kpis"]
    assert kpis["total_itens"] == 15
    assert isinstance(kpis["conformes"], int)
    assert isinstance(kpis["nao_conformes"], int)


def test_to_json_items_count(report) -> None:
    output = to_json(report)
    data = json.loads(output)
    assert len(data["itens"]) == 15


# --- Markdown output ---------------------------------------------------------


def test_to_markdown_contains_header(report) -> None:
    output = to_markdown(report)
    assert "Auditoria de Conformidade" in output
    assert "forge audit" in output


def test_to_markdown_contains_kpi_table(report) -> None:
    output = to_markdown(report)
    assert "Total de Itens" in output
    assert "Conformes" in output


def test_to_markdown_contains_items_table(report) -> None:
    output = to_markdown(report)
    assert "G01" in output
    assert "G15" in output


# --- HTML output -------------------------------------------------------------


def test_to_html_is_valid_html(report) -> None:
    output = to_html(report)
    assert output.startswith("<!doctype html>")
    assert "</html>" in output


def test_to_html_contains_compliance_rate(report) -> None:
    output = to_html(report)
    assert f"{report.compliance_rate:.1f}%" in output


def test_to_html_contains_all_items(report) -> None:
    output = to_html(report)
    for item in report.items:
        assert item.id in output
