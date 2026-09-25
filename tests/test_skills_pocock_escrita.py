# -*- coding: utf-8 -*-
"""
Ticket 5 (skills-pocock ciclo-01, D1): contrato do texto do aidd-escrita-agentes.

Rótulo honesto: prova que a regra está escrita na skill, não que o agente a segue
(prova de comportamento = Ticket 13).
"""
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "componentes" / "compartilhado" / "skills" / "aidd-escrita-agentes" / "SKILL.md"


def _texto() -> str:
    assert SKILL.is_file(), f"skill ausente: {SKILL}"
    return SKILL.read_text(encoding="utf-8")


def _frontmatter() -> dict:
    m = re.match(r"---\n(.*?)\n---\n", _texto(), re.DOTALL)
    assert m, "frontmatter ausente"
    return yaml.safe_load(m.group(1))


def test_frontmatter_valido_com_gatilho():
    fm = _frontmatter()
    assert fm.get("name") == "aidd-escrita-agentes"
    desc = fm.get("description") or ""
    assert re.search(r"skill", desc, re.IGNORECASE)
    assert "AGENTS.md" in desc
    assert "CLAUDE.md" in desc


def test_cobre_conceitos_obrigatorios():
    texto = _texto()
    obrigatorios = {
        "ponteiro de contexto": r"context pointer",
        "no-op": r"no-op",
        "sedimento": r"sediment",
        "ordem negativa": r"negation",
        "fonte única": r"single source of truth",
        "critério de pronto": r"completion criterion",
    }
    faltando = [k for k, pad in obrigatorios.items() if not re.search(pad, texto, re.IGNORECASE)]
    assert not faltando, f"conceitos ausentes: {faltando}"


def test_credita_upstream_e_licenca():
    texto = _texto()
    assert "mattpocock/skills" in texto
    assert "MIT" in texto


def test_abaixo_de_150_linhas():
    assert len(_texto().splitlines()) < 150
