# -*- coding: utf-8 -*-
"""
Ticket 4 (skills-pocock ciclo-01, D8): contrato do texto do aidd-tdd.

Rótulo honesto: prova que a regra está escrita na skill, não que o agente a segue
(prova de comportamento = Ticket 13).
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "componentes" / "compartilhado" / "skills" / "aidd-tdd" / "SKILL.md"


def _texto() -> str:
    return SKILL.read_text(encoding="utf-8")


def test_refactor_fora_do_ciclo():
    texto = _texto()
    assert not re.search(r"^#+\s*3\.\s*Refactor", texto, re.MULTILINE | re.IGNORECASE)
    assert "Red-Green-Refactor" not in texto
    assert re.search(r"refactor[^\n]*review", texto, re.IGNORECASE)


def test_seams_combinados_antes_do_primeiro_teste():
    texto = _texto()
    m_seams = re.search(r"^#+[^\n]*seams", texto, re.MULTILINE | re.IGNORECASE)
    m_red = re.search(r"^#+[^\n]*\bRed\b", texto, re.MULTILINE)
    assert m_seams and m_red, "seção de seams ou de Red ausente"
    assert m_seams.start() < m_red.start(), "seams precisa vir antes do Red"
    assert re.search(r"confirm[^\n]*user|user[^\n]*(confirm|agree)", texto, re.IGNORECASE)


def test_anti_padroes():
    texto = _texto()
    assert re.search(r"^#+[^\n]*anti-patterns", texto, re.MULTILINE | re.IGNORECASE)
    assert re.search(r"tautolog", texto, re.IGNORECASE)
    assert re.search(r"implementation-coupled|coupled to (the )?implementation", texto, re.IGNORECASE)
    assert re.search(r"horizontal slic", texto, re.IGNORECASE)
    assert re.search(r"independent source", texto, re.IGNORECASE)


def test_um_teste_uma_implementacao():
    assert re.search(r"one test[^\n]*one implementation", _texto(), re.IGNORECASE)


def test_zero_stubs_e_runners_mantidos():
    texto = _texto()
    assert "Zero Stubs" in texto
    for runner in ("pytest", "vitest", "go test", "cargo test"):
        assert runner in texto, f"runner {runner} sumiu"
