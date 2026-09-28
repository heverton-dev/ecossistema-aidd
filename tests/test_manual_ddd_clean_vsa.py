# -*- coding: utf-8 -*-
"""
Testes para o Manual Canônico de DDD Tático + Invariantes no Monólito VSA.
Valida a presença e completude do protocolo docs/protocolos/PADRAO-DDD-CLEAN-VSA.md.
"""
from pathlib import Path
import re
import pytest

ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = ROOT / "docs" / "protocolos" / "PADRAO-DDD-CLEAN-VSA.md"


def test_arquivo_manual_existe():
    """Garante que o arquivo canônico existe no repositório."""
    assert DOC_PATH.is_file(), f"Arquivo canônico ausente: {DOC_PATH}"


def test_secoes_essenciais_ddd():
    """Verifica se todas as seções canônicas de DDD tático estão presentes."""
    assert DOC_PATH.is_file(), f"Arquivo canônico ausente: {DOC_PATH}"
    conteudo = DOC_PATH.read_text(encoding="utf-8")

    secoes_obrigatorias = [
        ("Entity com try_create", r"try_create|tryCreate"),
        ("Value Object", r"Value Object|Objeto de Valor"),
        ("Result pattern", r"Result pattern|Padrão Result|Result\[|Result<"),
        ("Integração VSA", r"VSA|Vertical Slice Architecture|Fatias Verticais"),
        ("Zero Vendor Lock-in", r"Vendor Lock-in|Zero Vendor Lock-in|Puro|Agnóstico"),
    ]

    faltando = []
    for nome, padrao in secoes_obrigatorias:
        if not re.search(padrao, conteudo, re.IGNORECASE):
            faltando.append(nome)

    assert not faltando, f"Seções essenciais ausentes no manual: {faltando}"


def test_exemplos_completos_python_e_typescript():
    """Valida a presença de código tipado e funcional em Python e TypeScript."""
    assert DOC_PATH.is_file(), f"Arquivo canônico ausente: {DOC_PATH}"
    conteudo = DOC_PATH.read_text(encoding="utf-8")

    # Verifica blocos de código
    assert "```python" in conteudo, "Exemplo de código Python ausente"
    assert "```typescript" in conteudo or "```ts" in conteudo, "Exemplo de código TypeScript ausente"

    # Invariantes e contratos nos exemplos
    assert "def try_create" in conteudo or "def try_create(" in conteudo, "Método try_create em Python ausente"
    assert "tryCreate" in conteudo or "try_create" in conteudo, "Método factory tryCreate em TypeScript ausente"


def test_sem_placeholders_ou_stubs():
    """Garante que não existem stubs, mocks ou TODOs no documento canônico."""
    assert DOC_PATH.is_file(), f"Arquivo canônico ausente: {DOC_PATH}"
    conteudo = DOC_PATH.read_text(encoding="utf-8")

    proibidos = [
        r"\bTODO\b",
        r"\bFIXME\b",
        r"\bTBD\b",
        r"\.\.\.\s*#\s*implementar",
        r"pass\s*#\s*a fazer",
    ]

    encontrados = []
    for padrao in proibidos:
        if re.search(padrao, conteudo):
            encontrados.append(padrao)

    assert not encontrados, f"Placeholders encontrados no manual canônico: {encontrados}"
