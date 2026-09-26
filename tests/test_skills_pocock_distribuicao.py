# -*- coding: utf-8 -*-
"""
Ticket 12 (skills-pocock ciclo-01, D15): distribuição das skills do ciclo.

Passo vermelho trocado com aprovação do usuário (25/09/2026): o hook de commit já
sincroniza os harnesses a cada commit, então `components verify` não reprova mais
antes do sync. A divergência real que sobra é a cópia do forge
(tools/aidd-forge/aidd_forge/templates/skills/), que nenhum gate compara por conteúdo.
"""
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CANONICO = ROOT / "componentes" / "compartilhado" / "skills"
FORGE = ROOT / "tools" / "aidd-forge" / "aidd_forge" / "templates" / "skills"
REFERENCIA = ROOT / "docs" / "protocolos" / "AGENTS-REFERENCIA-COMPLETA.md"
AGENTS = ROOT / "AGENTS.md"

SKILLS_DO_CICLO = (
    "aidd-diagnose", "aidd-tickets", "aidd-grill", "aidd-grill-docs", "aidd-tdd",
    "aidd-escrita-agentes", "aidd-retro", "aidd-reexplica", "aidd-entrega",
    "aidd-wizard", "aidd-planos",
)
SKILLS_NOVAS = ("aidd-escrita-agentes", "aidd-retro", "aidd-reexplica", "aidd-entrega", "aidd-wizard")


def _skills_no_forge():
    return sorted(p.name for p in FORGE.iterdir() if (p / "SKILL.md").is_file() and (CANONICO / p.name).is_dir())


@pytest.mark.parametrize("skill", _skills_no_forge())
def test_copia_do_forge_igual_a_fonte(skill):
    forge = (FORGE / skill / "SKILL.md").read_bytes().replace(b"\r\n", b"\n")
    fonte = (CANONICO / skill / "SKILL.md").read_bytes().replace(b"\r\n", b"\n")
    assert forge == fonte, f"cópia do forge de {skill} diverge de componentes/compartilhado"


def test_referencia_lista_todas_as_skills_do_ciclo():
    texto = REFERENCIA.read_text(encoding="utf-8")
    faltando = [s for s in SKILLS_DO_CICLO if f"**/{s}:**" not in texto]
    assert not faltando, f"skills ausentes da referência: {faltando}"


def test_descricoes_antigas_removidas():
    for arq in (REFERENCIA, AGENTS):
        texto = arq.read_text(encoding="utf-8")
        assert "Red-Green-Refactor" not in texto, f"{arq.name} ainda descreve aidd-tdd como Red-Green-Refactor"
        assert not re.search(r"hip[oó]tese [uú]nica", texto, re.IGNORECASE), f"{arq.name} ainda cita hipótese única"
        assert "ordem estrita de dependência" not in texto, f"{arq.name} ainda cita ordem fixa de tickets"


def test_agents_lista_skills_novas():
    texto = AGENTS.read_text(encoding="utf-8")
    faltando = [s for s in SKILLS_NOVAS if f"`/{s}`" not in texto]
    assert not faltando, f"AGENTS.md sem as skills novas: {faltando}"


def test_components_verify_exit_0(tmp_path):
    saida = tmp_path / "verify.txt"
    with saida.open("w", encoding="utf-8") as f:
        r = subprocess.run([sys.executable, str(ROOT / "ecossistema.py"), "components", "verify"],
                           cwd=str(ROOT), stdout=f, stderr=subprocess.STDOUT, timeout=300)
    assert r.returncode == 0, saida.read_text(encoding="utf-8", errors="replace")[-2000:]
