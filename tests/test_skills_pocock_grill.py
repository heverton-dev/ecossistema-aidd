# -*- coding: utf-8 -*-
"""
Ticket 3 (skills-pocock ciclo-01, D2): contrato do texto do aidd-grill e aidd-grill-docs.

Rótulo honesto: prova que a regra está escrita na skill, não que o agente a segue
(prova de comportamento = Ticket 13).
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "componentes" / "compartilhado" / "skills"
GRILL = SKILLS / "aidd-grill" / "SKILL.md"
GRILL_DOCS = SKILLS / "aidd-grill-docs" / "SKILL.md"


def _grill() -> str:
    return GRILL.read_text(encoding="utf-8")


def _grill_docs() -> str:
    return GRILL_DOCS.read_text(encoding="utf-8")


def test_sem_uma_pergunta_por_vez():
    assert not re.search(r"one question at a time", _grill(), re.IGNORECASE)


def test_rodadas_numeradas_com_fronteira():
    texto = _grill()
    assert re.search(r"\brounds?\b", texto, re.IGNORECASE)
    assert re.search(r"number(ed)? (each |the )?questions?|questions? (are )?numbered", texto, re.IGNORECASE)
    assert re.search(r"frontier", texto, re.IGNORECASE)


def test_resposta_recomendada_por_pergunta():
    assert re.search(r"recommended answer", _grill(), re.IGNORECASE)


def test_fatos_do_agente_decisoes_do_usuario():
    texto = _grill()
    assert re.search(r"facts[^\n]*agent", texto, re.IGNORECASE)
    assert re.search(r"decisions[^\n]*user", texto, re.IGNORECASE)


def test_fim_com_fronteira_vazia_e_confirmacao():
    assert re.search(r"frontier[^\n]*empty[^\n]*user confirms", _grill(), re.IGNORECASE)


def test_modo_nao_interativo_mantido():
    assert "### Consolidated Assumptions" in _grill()


def test_grill_docs_le_context_e_adr():
    texto = _grill_docs()
    assert "CONTEXT.md" in texto
    assert "docs/adr/" in texto


def test_grill_docs_atualiza_glossario():
    assert re.search(r"glossary", _grill_docs(), re.IGNORECASE)
