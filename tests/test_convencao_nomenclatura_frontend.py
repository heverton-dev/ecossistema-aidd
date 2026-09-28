# -*- coding: utf-8 -*-
"""
Testes para a Convenção de Nomenclatura de Arquivos Frontend na Stack Ouro.
Valida que docs/protocolos/PADRAO-OURO-STACK-TECNOLOGICA.md inclui a seção de nomenclatura de sufixos.
"""
from pathlib import Path
import re
import pytest

ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = ROOT / "docs" / "protocolos" / "PADRAO-OURO-STACK-TECNOLOGICA.md"


def test_secao_nomenclatura_frontend_existe():
    """Garante que a convenção de sufixos de arquivo frontend está documentada."""
    assert DOC_PATH.is_file(), f"Arquivo canônico ausente: {DOC_PATH}"
    conteudo = DOC_PATH.read_text(encoding="utf-8")

    sufixos_obrigatorios = [
        (".component.tsx", r"\.component\.tsx"),
        (".page.tsx", r"\.page\.tsx"),
        (".context.tsx", r"\.context\.tsx"),
        (".hook.ts", r"\.hook\.ts"),
        (".schema.ts", r"\.schema\.ts"),
    ]

    faltando = []
    for nome, padrao in sufixos_obrigatorios:
        if not re.search(padrao, conteudo):
            faltando.append(nome)

    assert not faltando, f"Sufixos obrigatórios de frontend ausentes no protocolo: {faltando}"
