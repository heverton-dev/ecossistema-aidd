# -*- coding: utf-8 -*-
"""
Ticket 6 (skills-pocock ciclo-01, D12): contrato do texto do aidd-retro.

Rótulo honesto: prova que a regra está escrita na skill, não que o agente a segue
(prova de comportamento = Ticket 13).
"""
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "componentes" / "compartilhado" / "skills" / "aidd-retro" / "SKILL.md"

CATEGORIAS = {
    "navegação": r"^- \*\*Navigation:\*\*",
    "checagem automática": r"^- \*\*Automated checks:\*\*",
    "padrão de código": r"^- \*\*Coding standards:\*\*",
    "AGENTS.md": r"^- \*\*AGENTS\.md[^*]*:\*\*",
    "custo de ferramenta": r"^- \*\*Tool economy:\*\*",
    "no-op": r"^- \*\*No-ops:\*\*",
    "acesso a informação": r"^- \*\*Information access:\*\*",
}


def _texto() -> str:
    assert SKILL.is_file(), f"skill ausente: {SKILL}"
    return SKILL.read_text(encoding="utf-8")


def test_frontmatter():
    m = re.match(r"---\n(.*?)\n---\n", _texto(), re.DOTALL)
    assert m, "frontmatter ausente"
    fm = yaml.safe_load(m.group(1))
    assert fm.get("name") == "aidd-retro"
    assert fm.get("description")


def test_le_log_da_sessao_com_padrao_atual():
    texto = _texto()
    assert re.search(r"session log", texto, re.IGNORECASE)
    assert re.search(r"default[^\n]*current session", texto, re.IGNORECASE)


def test_sete_categorias():
    texto = _texto()
    faltando = [k for k, pad in CATEGORIAS.items() if not re.search(pad, texto, re.MULTILINE)]
    assert not faltando, f"categorias ausentes: {faltando}"


def test_classificacao_mecanico_e_julgamento():
    texto = _texto()
    assert re.search(r"mechanical[^\n]*gates/", texto, re.IGNORECASE)
    assert re.search(r"judg(e)?ment[^\n]*review rule", texto, re.IGNORECASE)


def test_ordem_de_gravidade():
    assert re.search(r"order of severity|severity order", _texto(), re.IGNORECASE)


def test_ponteiro_escrita_e_encaminhamento_melhoria():
    texto = _texto()
    assert "aidd-escrita-agentes" in texto
    assert "aidd-melhoria" in texto


def test_so_propoe_nunca_aplica():
    texto = _texto()
    assert re.search(r"propose only", texto, re.IGNORECASE)
    assert re.search(r"approv", texto, re.IGNORECASE)


def test_credita_upstream():
    texto = _texto()
    assert "mattpocock/skills" in texto
    assert "MIT" in texto
