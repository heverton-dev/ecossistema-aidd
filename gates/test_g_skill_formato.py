# -*- coding: utf-8 -*-
"""
Testes do gate G_SKILL_FORMATO (CONVENCAO-AUTORIA-SKILLS.md, secoes 5.1, 5.2 e 5.3).

Cada violacao e montada numa arvore sintetica isolada (tmp_path) e o gate real
roda via subprocess: tem de reprovar (exit 1) e citar o codigo da violacao.
A skill correta aprova (exit 0); o modo --aviso imprime e sai com exit 0.
"""

import json
import os
import subprocess
import sys

import pytest

GATE_DIR = os.path.dirname(os.path.abspath(__file__))
GATE_PATH = os.path.join(GATE_DIR, "G_SKILL_FORMATO.py")

DESCRICAO_BOA = "Builds the parts catalog. Use when the user asks for an inventory or \"mapa de pecas\"."


def _escrever_skill(raiz, pasta, name=None, description=DESCRICAO_BOA, linhas_corpo=10):
    d = os.path.join(raiz, "componentes", "compartilhado", "skills", pasta)
    os.makedirs(d, exist_ok=True)
    corpo = "\n".join(f"Step {i}." for i in range(linhas_corpo))
    with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write(f"---\nname: {name or pasta}\ndescription: {description}\n---\n\n{corpo}\n")


def _escrever_dependencias(raiz, skills):
    os.makedirs(os.path.join(raiz, "gates"), exist_ok=True)
    with open(os.path.join(raiz, "gates", "dependencias_externas.json"), "w", encoding="utf-8") as f:
        json.dump({"skills": skills}, f)


def _rodar(raiz, *extra):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, GATE_PATH, "--raiz", str(raiz), *extra],
        capture_output=True, text=True, encoding="utf-8", errors="replace", env=env,
    )


def test_skill_correta_aprova_exit_0(tmp_path):
    _escrever_dependencias(tmp_path, {})
    _escrever_skill(tmp_path, "aidd-catalog")
    res = _rodar(tmp_path)
    assert res.returncode == 0, res.stdout
    assert "[OK]" in res.stdout


@pytest.mark.parametrize("pasta,kwargs,codigo", [
    ("aidd-catalog", {"name": "aidd-outro-nome"}, "NOME_DIFERENTE_DA_PASTA"),
    ("aidd_Catalog", {}, "NOME_FORA_DO_PADRAO"),
    ("aidd--catalog", {}, "NOME_FORA_DO_PADRAO"),
    ("aidd-forge-runner", {}, "SUFIXO_RUNNER"),
    ("aidd-catalog", {"description": "Builds the parts catalog for the ecosystem."}, "SEM_USE_WHEN"),
    ("aidd-catalog", {"linhas_corpo": 451}, "CORPO_ACIMA_DE_450"),
    ("catalog", {}, "SEM_PREFIXO_AIDD"),
])
def test_reprova_skill_fora_do_formato_exit_1(tmp_path, pasta, kwargs, codigo):
    _escrever_dependencias(tmp_path, {})
    _escrever_skill(tmp_path, pasta, **kwargs)
    res = _rodar(tmp_path)
    assert res.returncode == 1, res.stdout
    assert codigo in res.stdout


def test_reprova_skill_sem_frontmatter_exit_1(tmp_path):
    _escrever_dependencias(tmp_path, {})
    d = tmp_path / "componentes" / "compartilhado" / "skills" / "aidd-catalog"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text("# no frontmatter\n", encoding="utf-8")
    res = _rodar(tmp_path)
    assert res.returncode == 1, res.stdout
    assert "SEM_FRONTMATTER" in res.stdout


def test_reprova_frontmatter_yaml_invalido_exit_1(tmp_path):
    _escrever_dependencias(tmp_path, {})
    _escrever_skill(tmp_path, "aidd-pure", description="Runs Flow 01 (Slash: /pure). Use when the user types /pure.")
    res = _rodar(tmp_path)
    assert res.returncode == 1, res.stdout
    assert "FRONTMATTER_YAML_INVALIDO" in res.stdout


def test_corpo_com_450_linhas_ainda_aprova(tmp_path):
    _escrever_dependencias(tmp_path, {})
    _escrever_skill(tmp_path, "aidd-catalog", linhas_corpo=440)
    assert _rodar(tmp_path).returncode == 0


def test_skill_de_terceiro_declarada_dispensa_prefixo_aidd(tmp_path):
    _escrever_dependencias(tmp_path, {"wrangler": {"gitignore": ["*/skills/wrangler/"]}})
    _escrever_skill(tmp_path, "wrangler")
    res = _rodar(tmp_path)
    assert res.returncode == 0, res.stdout


def test_skill_de_ferramenta_tambem_e_auditada(tmp_path):
    _escrever_dependencias(tmp_path, {})
    d = tmp_path / "componentes" / "aidd-forge" / "skills" / "forge-helper"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(f"---\nname: forge-helper\ndescription: {DESCRICAO_BOA}\n---\nx\n", encoding="utf-8")
    res = _rodar(tmp_path)
    assert res.returncode == 1
    assert "SEM_PREFIXO_AIDD" in res.stdout


def test_modo_aviso_imprime_violacao_e_sai_0(tmp_path):
    _escrever_dependencias(tmp_path, {})
    _escrever_skill(tmp_path, "aidd-forge-runner")
    res = _rodar(tmp_path, "--aviso")
    assert res.returncode == 0
    assert "SUFIXO_RUNNER" in res.stdout
    assert "AVISO" in res.stdout


def test_repositorio_real_aprova_em_modo_bloqueante():
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    res = subprocess.run([sys.executable, GATE_PATH], capture_output=True, text=True,
                         encoding="utf-8", errors="replace", env=env)
    assert res.returncode == 0, res.stdout
