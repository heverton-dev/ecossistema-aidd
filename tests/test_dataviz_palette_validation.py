# -*- coding: utf-8 -*-
"""
Testes para a skill canônica de dataviz (meus-prompts: Ticket 2, D8).
Cobre: existência e formato do skill aidd-dataviz, migração do
validate_palette.py para componentes/compartilhado/skills/aidd-dataviz/scripts/
e comportamento determinístico (exit 0/1/2) do validador de paletas.
"""
from pathlib import Path
import re
import subprocess
import sys

import yaml

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "componentes" / "compartilhado" / "skills" / "aidd-dataviz"
SKILL_MD = SKILL_DIR / "SKILL.md"
SCRIPT = SKILL_DIR / "scripts" / "validate_palette.py"
GATE = ROOT / "gates" / "G_SKILL_FORMATO.py"

# Fixtures verificadas contra o validador: exit 0 / 1 / 2 respectivamente.
CATEGORICAL_OK = "#2a78d6,#eb6834,#1baf7a,#eda100,#e87ba4,#008300,#4a3aa7,#e34948"
CATEGORICAL_FAIL = "#808080,#909090"          # abaixo do chroma floor + faixa
ORDINAL_OK = "#123456,#2a78d6,#7fb2f0"         # rampa monocromática válida
ORDINAL_FAIL = "#2a78d6,#eb6834,#1baf7a"       # não-monocromática e fora de ordem


def _run(args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, timeout=120,
    )


def test_script_migrado_existe():
    """O validate_palette.py deve existir no diretório canônico compartilhado."""
    assert SCRIPT.is_file(), f"Script ausente: {SCRIPT}"


def test_skill_md_canonico():
    """SKILL.md deve ter frontmatter canônico (name == pasta, description com 'Use when')."""
    assert SKILL_MD.is_file(), f"SKILL.md ausente: {SKILL_MD}"
    texto = SKILL_MD.read_text(encoding="utf-8")
    assert texto.startswith("---\n"), "Frontmatter deve iniciar com '---'"
    partes = texto.split("---\n", 2)
    assert len(partes) >= 3, "Frontmatter YAML malformado em aidd-dataviz"
    fm = yaml.safe_load(partes[1])
    assert isinstance(fm, dict), "Frontmatter deve ser dicionário YAML"
    assert fm.get("name") == "aidd-dataviz", f"name esperado 'aidd-dataviz', recebido {fm.get('name')!r}"
    assert "use when" in str(fm.get("description", "")).lower(), "description deve conter 'Use when...'"


def test_zero_lockin_proprietario():
    """Skill portada não pode carregar licença proprietária de terceiro (Lei #6)."""
    texto = SKILL_MD.read_text(encoding="utf-8").lower()
    assert "license: proprietary" not in texto
    assert "proprietary. license.txt" not in texto


def test_gate_skill_formato_audita_aidd_dataviz():
    """G_SKILL_FORMATO deve auditar a nova skill (contagem inclui-a) e sair com exit 0."""
    r = subprocess.run(
        [sys.executable, str(GATE), "--raiz", str(ROOT)],
        capture_output=True, text=True, timeout=120,
    )
    assert r.returncode == 0, f"G_SKILL_FORMATO reprovou:\n{r.stdout}\n{r.stderr}"
    m = re.search(r"Auditando (\d+) skill", r.stdout)
    assert m, f"contagem de skills ausente na saída do gate:\n{r.stdout}"
    # Contagem real em vez de número fixo: a renomeação dos construtores (fronteiras-ferramentas,
    # Ticket 4) juntou skills e derrubou o antigo ">= 46" sem a aidd-dataviz sair da varredura.
    skills = sorted(ROOT.glob("componentes/*/skills/*/SKILL.md"))
    assert any(s.parent.name == "aidd-dataviz" for s in skills), "aidd-dataviz sumiu de componentes/"
    assert int(m.group(1)) == len(skills), (
        f"gate auditou {m.group(1)} de {len(skills)} skills em componentes/*/skills/"
    )


def test_categorica_valida_exit_0():
    """Paleta categórica de referência deve passar em todas as checagens (exit 0)."""
    r = _run([CATEGORICAL_OK, "--mode", "light"])
    assert r.returncode == 0, f"exit {r.returncode}:\n{r.stdout}\n{r.stderr}"
    assert "ALL CHECKS PASS" in r.stdout


def test_categorica_invalida_exit_1():
    """Paleta cinza (chroma floor violado) deve reprovar com exit 1."""
    r = _run([CATEGORICAL_FAIL, "--mode", "light"])
    assert r.returncode == 1, f"exit {r.returncode}:\n{r.stdout}\n{r.stderr}"
    assert "FAILED" in r.stdout
    assert "Chroma floor" in r.stdout


def test_ordinal_valida_exit_0():
    """Rampa ordinal monocromática válida deve passar com --ordinal (exit 0)."""
    r = _run([ORDINAL_OK, "--mode", "light", "--ordinal"])
    assert r.returncode == 0, f"exit {r.returncode}:\n{r.stdout}\n{r.stderr}"
    assert "ALL CHECKS PASS" in r.stdout


def test_ordinal_invalida_exit_1():
    """Paleta categórica com --ordinal deve reprovar (não é rampa de um matiz)."""
    r = _run([ORDINAL_FAIL, "--mode", "light", "--ordinal"])
    assert r.returncode == 1, f"exit {r.returncode}:\n{r.stdout}\n{r.stderr}"
    assert "Single hue" in r.stdout


def test_hex_invalido_exit_2():
    """Entrada malformada deve sair com exit 2 (erro de uso), nunca falhar aberto."""
    r = _run(["#zzzzzz"])
    assert r.returncode == 2, f"exit {r.returncode}:\n{r.stdout}\n{r.stderr}"
    assert "invalid hex" in r.stderr


def test_palette_vazia_exit_2():
    """Lista de paleta vazia deve sair com exit 2 (usage no stderr)."""
    r = _run([""])
    assert r.returncode == 2, f"exit {r.returncode}:\n{r.stdout}\n{r.stderr}"


def test_saida_deterministica():
    """Duas execuções idênticas devem produzir bytes idênticos (Lei #1)."""
    a = _run([CATEGORICAL_OK, "--mode", "light"])
    b = _run([CATEGORICAL_OK, "--mode", "light"])
    assert a.returncode == b.returncode
    assert a.stdout == b.stdout, "saída não determinística entre execuções"
