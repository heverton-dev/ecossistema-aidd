# -*- coding: utf-8 -*-
"""
Ticket 7 (skills-pocock ciclo-01, D1): glossário CONTEXT.md, formato ADR e aidd-reexplica.

Rótulo honesto: prova que os artefatos existem com a estrutura combinada, não que
o agente os usa (prova de comportamento = Ticket 13). As ambiguidades ficam abertas
para o usuário decidir (HITL): o teste reprova se alguma vier marcada como decidida.
"""
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONTEXT = ROOT / "CONTEXT.md"
ADR = ROOT / "docs" / "adr" / "README.md"
REEXPLICA = ROOT / "componentes" / "compartilhado" / "skills" / "aidd-reexplica" / "SKILL.md"
AGENTS = ROOT / "AGENTS.md"

TERMOS = ["ciclo", "fase", "plano", "sessão", "ticket", "gate", "harness", "4F", "15-D", "worktree"]


def _ler(p: Path) -> str:
    assert p.is_file(), f"arquivo ausente: {p.relative_to(ROOT)}"
    return p.read_text(encoding="utf-8")


def _secao(texto: str, titulo: str) -> str:
    m = re.search(rf"^## {re.escape(titulo)}\n(.*?)(?=^## |\Z)", texto, re.MULTILINE | re.DOTALL)
    assert m, f"seção '## {titulo}' ausente"
    return m.group(1)


def test_context_tem_as_tres_secoes():
    texto = _ler(CONTEXT)
    for titulo in ("Linguagem", "Relações", "Ambiguidades sinalizadas"):
        _secao(texto, titulo)


def test_context_cobre_os_termos():
    texto = _ler(CONTEXT)
    linguagem = _secao(texto, "Linguagem")
    ambiguidades = _secao(texto, "Ambiguidades sinalizadas")
    faltando = [
        t for t in TERMOS
        if not re.search(rf"^- \*\*{re.escape(t)}\*\*", linguagem, re.IGNORECASE | re.MULTILINE)
        and not re.search(rf"^### {re.escape(t)}$", ambiguidades, re.IGNORECASE | re.MULTILINE)
    ]
    assert not faltando, f"termos ausentes: {faltando}"


def test_ambiguidades_ficam_abertas_para_o_usuario():
    amb = _secao(_ler(CONTEXT), "Ambiguidades sinalizadas")
    itens = re.findall(r"^### .+$", amb, re.MULTILINE)
    assert len(itens) >= 3, "esperado ao menos 3 ambiguidades sinalizadas"
    blocos = re.split(r"^### .+$", amb, flags=re.MULTILINE)[1:]
    for titulo, bloco in zip(itens, blocos):
        assert re.search(r"Status:\*\*\s*aberta", bloco, re.IGNORECASE), f"{titulo} sem 'Status: aberta'"
        assert not re.search(r"Status:\*\*\s*decidida", bloco, re.IGNORECASE), f"{titulo} decidida pelo agente"


def test_adr_readme_define_formato():
    texto = _ler(ADR)
    for campo in ("Status", "Contexto", "Decisão", "Consequências"):
        assert re.search(rf"^#+ {campo}", texto, re.MULTILINE), f"ADR sem seção {campo}"
    assert re.search(r"\d{4}-[a-z0-9-]+\.md", texto), "ADR sem regra de nome de arquivo"


def test_reexplica_aponta_para_context():
    texto = _ler(REEXPLICA)
    m = re.match(r"---\n(.*?)\n---\n", texto, re.DOTALL)
    assert m, "frontmatter ausente"
    fm = yaml.safe_load(m.group(1))
    assert fm.get("name") == "aidd-reexplica"
    assert fm.get("description")
    assert "CONTEXT.md" in texto
    assert re.search(r"last (assistant )?message", texto, re.IGNORECASE)
    assert re.search(r"PT-BR|Portuguese", texto)


def test_agents_tem_ponteiro_para_context():
    linhas = [l for l in _ler(AGENTS).splitlines() if "CONTEXT.md" in l]
    assert len(linhas) == 1, f"esperada 1 linha-ponteiro para CONTEXT.md em AGENTS.md, achadas {len(linhas)}"
