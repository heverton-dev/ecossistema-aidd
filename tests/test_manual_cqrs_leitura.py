# -*- coding: utf-8 -*-
"""
Testes para o Manual Canônico de Leitura Otimizada e CQRS para Fatias Verticais.
Valida a presença e completude do protocolo docs/protocolos/PADRAO-CONSULTAS-LEITURA-CQRS.md.
"""
from pathlib import Path
import re
import pytest

ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = ROOT / "docs" / "protocolos" / "PADRAO-CONSULTAS-LEITURA-CQRS.md"


def test_arquivo_manual_cqrs_existe():
    """Garante que o manual canônico de CQRS existe."""
    assert DOC_PATH.is_file(), f"Arquivo canônico ausente: {DOC_PATH}"


def test_secoes_essenciais_cqrs():
    """Valida que as diretrizes fundamentais de separação comando vs consulta estão presentes."""
    assert DOC_PATH.is_file(), f"Arquivo canônico ausente: {DOC_PATH}"
    conteudo = DOC_PATH.read_text(encoding="utf-8")

    secoes = [
        ("Segregação Comando vs Consulta", r"Comando|Command.*Consulta|Query"),
        ("Leitura Direta SQL", r"SQL|SQLite WAL"),
        ("Projeção em DTO", r"DTO|Schema|Projeção"),
        ("Proibição de Agregados na Leitura", r"sem carregar agregados|sem entidade|overhead"),
        ("Integração VSA", r"VSA|Vertical Slice Architecture|Fatias Verticais"),
    ]

    faltando = []
    for nome, padrao in secoes:
        if not re.search(padrao, conteudo, re.IGNORECASE):
            faltando.append(nome)

    assert not faltando, f"Seções essenciais ausentes no manual de CQRS: {faltando}"


def test_exemplos_python_e_sqlite_wal():
    """Valida presença de exemplo de query direta em Python com SQLite WAL."""
    assert DOC_PATH.is_file(), f"Arquivo canônico ausente: {DOC_PATH}"
    conteudo = DOC_PATH.read_text(encoding="utf-8")

    assert "```python" in conteudo, "Exemplo em Python ausente"
    assert "sqlite3" in conteudo or "WAL" in conteudo, "Referência a SQLite WAL ausente no código"
    assert "```typescript" in conteudo or "```ts" in conteudo or "interface" in conteudo, "Contrato frontend de projeção ausente"


def test_sem_placeholders_ou_stubs_cqrs():
    """Garante ausência de stubs no manual de CQRS."""
    assert DOC_PATH.is_file(), f"Arquivo canônico ausente: {DOC_PATH}"
    conteudo = DOC_PATH.read_text(encoding="utf-8")

    for proibido in [r"\bTODO\b", r"\bFIXME\b", r"\bTBD\b"]:
        assert not re.search(proibido, conteudo), f"Placeholder {proibido} encontrado no manual"
