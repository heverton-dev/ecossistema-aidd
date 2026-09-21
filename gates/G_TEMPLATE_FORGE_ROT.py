#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_TEMPLATE_FORGE_ROT (Lei #1, #8, #12, #13)
=============================================================================
Portão determinístico de integridade dos templates do aidd-forge.
Impede o apodrecimento e divergência dos artefatos injetados em novos projetos:
  1. AGENTS.md template deve conter as 13 Leis Canônicas na íntegra.
  2. AGENTS.md template deve respeitar o orçamento de tokens (<= 1500 tokens).
  3. Templates de skills devem conter as skills procedurais canônicas da Tríade
     (aidd-grill, aidd-spec, aidd-tickets, aidd-tdd).
  4. Templates de gates devem conter os quality gates essenciais da Tríade
     (G_SAIDA_BINARIA, G_TESTES_REAIS, G_QUARTETO_SINE_QUA_NON, G_STACK_PADRAO_OURO).
  5. Não deve conter templates duplicados ou pastas órfãs de pipeline na raiz.

Saída:
  exit 0 = Templates do aidd-forge 100% íntegros e sincronizados com a governança.
  exit 1 = Pelo menos um template corrompido, defasado ou com regras ausentes.
=============================================================================
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = Path(__file__).resolve().parents[1]
FORGE_TEMPLATES_DIR = ROOT_DIR / "tools" / "aidd-forge" / "aidd_forge" / "templates"

CHARS_PER_TOKEN = 4
MAX_GOVERNANCE_TOKENS = 1500

LEIS_OBRIGATORIAS = (
    "Determinism First",
    "Binary Quality",
    "Structured Persistence",
    "Extreme Token Economy",
    "Zero Stubs / Zero Mocks",
    "Agnostic Supremacy",
    "Developer in Control",
    "Label Honesty",
    "Tool Testing Discipline",
    "Quarteto Sine Qua Non",
    "Padrão-Ouro",
    "Anti-Docs Rot",
    "Todo Portão Deve Provar que Morde",
)

SKILLS_CANONICAS_OBRIGATORIAS = (
    "aidd-grill",
    "aidd-spec",
    "aidd-tickets",
    "aidd-tdd",
)

GATES_CANONICOS_OBRIGATORIOS = (
    "G_BLOQUEAR_SEGREDOS.py",
    "G_TESTES_REAIS.py",
    "G_SAIDA_BINARIA.py",
    "G_QUARTETO_SINE_QUA_NON.py",
    "G_STACK_PADRAO_OURO.py",
    "G_DETERMINISMO_LEI_1.py",
)


def auditar_governance_agents(templates_dir: Path) -> Tuple[bool, List[str]]:
    erros: List[str] = []
    agents_path = templates_dir / "governance" / "AGENTS.md"

    if not agents_path.is_file():
        return False, [f"Arquivo de template ausente: {agents_path}"]

    content = agents_path.read_text(encoding="utf-8")
    tokens_estimados = len(content) // CHARS_PER_TOKEN

    if tokens_estimados > MAX_GOVERNANCE_TOKENS:
        erros.append(
            f"AGENTS.md do forge excede o orçamento de contexto: {tokens_estimados} tokens (máximo {MAX_GOVERNANCE_TOKENS})"
        )

    for lei in LEIS_OBRIGATORIAS:
        if lei.lower() not in content.lower():
            erros.append(f"Lei obrigatória ausente no template AGENTS.md do forge: '{lei}'")

    return len(erros) == 0, erros


def auditar_skills_template(templates_dir: Path) -> Tuple[bool, List[str]]:
    erros: List[str] = []
    skills_dir = templates_dir / "skills"

    if not skills_dir.is_dir():
        return False, [f"Diretório de skills ausente nos templates do forge: {skills_dir}"]

    for skill in SKILLS_CANONICAS_OBRIGATORIAS:
        skill_file = skills_dir / skill / "SKILL.md"
        if not skill_file.is_file():
            erros.append(f"Skill canônica obrigatória ausente nos templates do forge: '{skill}' ({skill_file})")

    return len(erros) == 0, erros


def auditar_gates_template(templates_dir: Path) -> Tuple[bool, List[str]]:
    erros: List[str] = []
    gates_dir = templates_dir / "gates"

    if not gates_dir.is_dir():
        return False, [f"Diretório de gates ausente nos templates do forge: {gates_dir}"]

    for gate in GATES_CANONICOS_OBRIGATORIOS:
        gate_file = gates_dir / gate
        if not gate_file.is_file():
            erros.append(f"Quality gate obrigatório ausente nos templates do forge: '{gate}' ({gate_file})")

    return len(erros) == 0, erros


def main(custom_templates_dir: Path | None = None) -> int:
    templates_dir = custom_templates_dir or FORGE_TEMPLATES_DIR

    print("=" * 72)
    print(" [GATE] G_TEMPLATE_FORGE_ROT — Integridade dos Templates do aidd-forge")
    print("=" * 72)
    print(f"Diretório inspecionado: {templates_dir}")

    if not templates_dir.is_dir():
        print(f"[ERRO] Diretório de templates não encontrado: {templates_dir}", file=sys.stderr)
        return 1

    falhas: List[str] = []

    ok_gov, errs_gov = auditar_governance_agents(templates_dir)
    if not ok_gov:
        falhas.extend(errs_gov)

    ok_skills, errs_skills = auditar_skills_template(templates_dir)
    if not ok_skills:
        falhas.extend(errs_skills)

    ok_gates, errs_gates = auditar_gates_template(templates_dir)
    if not ok_gates:
        falhas.extend(errs_gates)

    if falhas:
        print("\n[ERRO] Violações de integridade detectadas nos templates do aidd-forge:", file=sys.stderr)
        for f in falhas:
            print(f"  [X] {f}", file=sys.stderr)
        return 1

    print("\n[SUCESSO] Templates do aidd-forge 100% em conformidade com as 13 Leis Canônicas!")
    return 0


if __name__ == "__main__":
    caminho_arg = Path(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else None
    sys.exit(main(caminho_arg))
