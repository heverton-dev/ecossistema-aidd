# -*- coding: utf-8 -*-
"""
Ticket 8 (skills-pocock ciclo-01, D15): contrato do texto do aidd-entrega.

Rótulo honesto: prova que a regra está escrita na skill, não que o agente a segue
(prova de comportamento = Ticket 13).
"""
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "componentes" / "compartilhado" / "skills" / "aidd-entrega" / "SKILL.md"

SECOES = ("Resumo", "Evidência (antes/depois)", "Dá para desfazer?", "O que pode quebrar")


def _texto() -> str:
    assert SKILL.is_file(), f"skill ausente: {SKILL}"
    return SKILL.read_text(encoding="utf-8")


def _modelo() -> str:
    m = re.search(r"```markdown\n(.*?)```", _texto(), re.DOTALL)
    assert m, "SKILL.md sem bloco ```markdown com o modelo"
    return m.group(1)


def test_frontmatter():
    m = re.match(r"---\n(.*?)\n---\n", _texto(), re.DOTALL)
    assert m, "frontmatter ausente"
    fm = yaml.safe_load(m.group(1))
    assert fm.get("name") == "aidd-entrega"
    assert fm.get("description")


def test_modelo_tem_as_quatro_secoes_em_ordem():
    modelo = _modelo()
    posicoes = []
    for s in SECOES:
        m = re.search(rf"^## {re.escape(s)}$", modelo, re.MULTILINE)
        assert m, f"modelo sem seção '## {s}'"
        posicoes.append(m.start())
    assert posicoes == sorted(posicoes), "seções fora de ordem"


def test_evidencia_antes_e_depois_com_exit_code():
    modelo = _modelo()
    assert re.search(r"\*\*Antes:\*\*", modelo)
    assert re.search(r"\*\*Depois:\*\*", modelo)
    assert re.search(r"exit", modelo, re.IGNORECASE)


def test_exit_code_real_sem_pipe():
    texto = _texto()
    assert re.search(r"redirect[^\n]*file", texto, re.IGNORECASE)
    assert re.search(r"never[^\n]*pipe|pipe[^\n]*(hides|masks)", texto, re.IGNORECASE)


def test_onde_usar():
    texto = _texto()
    for alvo in ("commit", "PR", "RELATORIO-CONSTRUTOR.md", "ticket"):
        assert alvo in texto, f"uso em {alvo} ausente"


def test_checkbox_exige_evidencia_no_mesmo_documento():
    assert re.search(r"\[x\][^\n]*evidence[^\n]*same document", _texto(), re.IGNORECASE)


def test_creditos():
    texto = _texto()
    assert "mattpocock/skills" in texto
    assert re.search(r"humanlayer", texto, re.IGNORECASE)
    assert "show-me" in texto
    assert "MIT" in texto
