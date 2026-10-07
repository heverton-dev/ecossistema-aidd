# -*- coding: utf-8 -*-
"""
Testes para as Skills Canônicas de Utilitários de Documentos (meus-prompts: Ticket 1).
Cobre: aidd-docx, aidd-pdf, aidd-pptx, aidd-xlsx.
Valida conformidade com CONVENCAO-AUTORIA-SKILLS.md, ausência de lock-in e qualidade binária.
"""
from pathlib import Path
import re
import subprocess
import sys
import yaml
import pytest

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "componentes" / "compartilhado" / "skills"
DOC_SKILLS = ["aidd-docx", "aidd-pdf", "aidd-pptx", "aidd-xlsx"]


@pytest.mark.parametrize("skill_name", DOC_SKILLS)
def test_arquivos_document_utility_skills_existem(skill_name):
    """Garante que as skills canônicas existem no catálogo compartilhado."""
    skill_md = SKILLS_DIR / skill_name / "SKILL.md"
    assert skill_md.is_file(), f"Skill ausente: {skill_md}"


@pytest.mark.parametrize("skill_name", DOC_SKILLS)
def test_frontmatter_document_utility_skills_valido(skill_name):
    """Valida frontmatter YAML com name canônico e description contendo 'Use when...'."""
    skill_md = SKILLS_DIR / skill_name / "SKILL.md"
    assert skill_md.is_file(), f"Skill ausente: {skill_md}"
    texto = skill_md.read_text(encoding="utf-8")

    assert texto.startswith("---\n"), f"Frontmatter de {skill_name} deve iniciar com '---'"
    partes = texto.split("---\n", 2)
    assert len(partes) >= 3, f"Frontmatter YAML malformado em {skill_name}"
    
    fm = yaml.safe_load(partes[1])
    assert isinstance(fm, dict), f"Frontmatter deve ser dicionário YAML em {skill_name}"
    assert fm.get("name") == skill_name, f"Nome da skill deve ser '{skill_name}', recebido '{fm.get('name')}'"
    assert "use when" in str(fm.get("description", "")).lower(), f"Description deve conter 'Use when...' em {skill_name}"


@pytest.mark.parametrize("skill_name", DOC_SKILLS)
def test_zero_lockin_proprietario_document_skills(skill_name):
    """Garante ausência de lock-in proprietário (sem licença proprietária e agnóstico de harness)."""
    skill_md = SKILLS_DIR / skill_name / "SKILL.md"
    assert skill_md.is_file(), f"Skill ausente: {skill_md}"
    texto = skill_md.read_text(encoding="utf-8")
    
    assert "license: proprietary" not in texto.lower(), f"Detectado lock-in de licença proprietária em {skill_name}"
    assert "proprietary. license.txt" not in texto.lower(), f"Detectado lock-in de termos proprietários em {skill_name}"


def test_conformidade_gate_skill_formato():
    """Valida que o gate determinístico G_SKILL_FORMATO passa com sucesso."""
    gate_script = ROOT / "modulos" / "04-nucleo-compartilhado" / "gates" / "G_SKILL_FORMATO.py"
    resultado = subprocess.run([sys.executable, str(gate_script), "--raiz", str(ROOT)], capture_output=True, text=True)
    assert resultado.returncode == 0, f"G_SKILL_FORMATO falhou:\n{resultado.stdout}\n{resultado.stderr}"
