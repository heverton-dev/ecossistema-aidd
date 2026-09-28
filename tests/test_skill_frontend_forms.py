# -*- coding: utf-8 -*-
"""
Testes para a Skill Canônica aidd-frontend-forms.
Valida conformidade com a CONVENCAO-AUTORIA-SKILLS.md.
"""
from pathlib import Path
import re
import pytest

ROOT = Path(__file__).resolve().parent.parent
SKILL_PATH = ROOT / "componentes" / "compartilhado" / "skills" / "aidd-frontend-forms" / "SKILL.md"


def test_arquivo_skill_frontend_forms_existe():
    """Garante que a skill canônica existe no catálogo compartilhado."""
    assert SKILL_PATH.is_file(), f"Skill ausente: {SKILL_PATH}"


def test_frontmatter_valido():
    """Valida frontmatter YAML com name e description 'Use when...'."""
    assert SKILL_PATH.is_file(), f"Skill ausente: {SKILL_PATH}"
    texto = SKILL_PATH.read_text(encoding="utf-8")

    assert texto.startswith("---\n"), "Frontmatter deve iniciar com '---'"
    partes = texto.split("---\n", 2)
    assert len(partes) >= 3, "Frontmatter YAML malformado"
    yaml_header = partes[1]

    assert "name: aidd-frontend-forms" in yaml_header, "Nome da skill deve ser aidd-frontend-forms"
    assert re.search(r"description:\s*['\"]?Use when", yaml_header, re.IGNORECASE), "Description deve iniciar com 'Use when...'"


def test_conteudo_conciso_ingles_e_regras():
    """Valida concisão (< 150 linhas) e tecnologias cobertas (Next.js, Zod, React Hook Form)."""
    assert SKILL_PATH.is_file(), f"Skill ausente: {SKILL_PATH}"
    linhas = SKILL_PATH.read_text(encoding="utf-8").splitlines()
    assert len(linhas) < 150, f"Skill muito longa ({len(linhas)} linhas, máx 150)"

    conteudo = "\n".join(linhas)
    assert "zod" in conteudo.lower(), "Referência a Zod ausente"
    assert "react-hook-form" in conteudo.lower() or "hook form" in conteudo.lower(), "Referência a React Hook Form ausente"
    assert "next" in conteudo.lower(), "Referência a Next.js ausente"
