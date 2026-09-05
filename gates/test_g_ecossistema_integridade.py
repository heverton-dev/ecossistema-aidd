# -*- coding: utf-8 -*-
"""
Testes do gate G_ECOSSISTEMA_INTEGRIDADE — valida comportamento do gate
executando-o contra arvores sinteticas isoladas via subprocess.
"""

import os
import shutil

from _gate_test_utils import rodar_gate

GATE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "G_ECOSSISTEMA_INTEGRIDADE.py"
)
CLI_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "ecossistema.py"
)

TOOLS_REQUIRED = [
    "aidd-forge",
    "aidd-generator",
    "aidd-master",
    "aidd-enterprise"
]

SKILLS_REQUIRED = [
    "aidd-forge-runner",
    "aidd-generator-runner",
    "aidd-master-runner",
    "aidd-enterprise-runner"
]

COMMANDS_REQUIRED = [
    "forge.md",
    "generate.md",
    "master.md",
    "enterprise.md"
]


def _montar_arvore_valida(root_dir):
    """Cria uma arvore sintetica 100% compativel com G_ECOSSISTEMA_INTEGRIDADE."""
    # 1. Governanca raiz
    with open(os.path.join(root_dir, "AGENTS.md"), "w", encoding="utf-8") as f:
        f.write("# AGENTS.md\n")
    with open(os.path.join(root_dir, ".gitignore"), "w", encoding="utf-8") as f:
        f.write(".venv\n")

    # 2. Ferramentas em tools/
    for tool in TOOLS_REQUIRED:
        tdir = os.path.join(root_dir, "tools", tool)
        os.makedirs(tdir, exist_ok=True)
        with open(os.path.join(tdir, "README.md"), "w", encoding="utf-8") as f:
            f.write(f"# {tool}\n")

    # 3. Skills com frontmatter YAML valido
    for skill in SKILLS_REQUIRED:
        sdir = os.path.join(root_dir, "skills", skill)
        os.makedirs(sdir, exist_ok=True)
        with open(os.path.join(sdir, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write(f"---\nname: {skill}\ndescription: Test skill\n---\n# Content\n")

    # 4. Slash commands em .agent e .claude
    for harness in [".agent/commands", ".claude/commands"]:
        hdir = os.path.join(root_dir, harness)
        os.makedirs(hdir, exist_ok=True)
        for cmd in COMMANDS_REQUIRED:
            with open(os.path.join(hdir, cmd), "w", encoding="utf-8") as f:
                f.write(f"# Command {cmd}\n")

    # 5. Pasta gates com o proprio gate copiado + ecossistema.py
    gdir = os.path.join(root_dir, "gates")
    os.makedirs(gdir, exist_ok=True)
    gate_copy = os.path.join(gdir, "G_ECOSSISTEMA_INTEGRIDADE.py")
    shutil.copyfile(GATE_PATH, gate_copy)

    cli_copy = os.path.join(root_dir, "ecossistema.py")
    if os.path.exists(CLI_PATH):
        shutil.copyfile(CLI_PATH, cli_copy)
    else:
        with open(cli_copy, "w", encoding="utf-8") as f:
            f.write("# cli stub\n")

    return gate_copy


def test_arvore_valida_aprova(tmp_path):
    gate_path = _montar_arvore_valida(tmp_path)
    res = rodar_gate(gate_path, tmp_path)
    assert res.returncode == 0
    assert "Quality Gate G_ECOSSISTEMA_INTEGRIDADE APROVADO (100% OK)!" in res.stdout


def test_falha_se_readme_ausente_em_tool(tmp_path):
    gate_path = _montar_arvore_valida(tmp_path)
    os.remove(tmp_path / "tools" / "aidd-forge" / "README.md")

    res = rodar_gate(gate_path, tmp_path)
    assert res.returncode == 1
    assert "README.md ausente em tools/aidd-forge" in res.stdout


def test_falha_se_git_acidental_dentro_de_tool(tmp_path):
    gate_path = _montar_arvore_valida(tmp_path)
    os.makedirs(tmp_path / "tools" / "aidd-forge" / ".git", exist_ok=True)

    res = rodar_gate(gate_path, tmp_path)
    assert res.returncode == 1
    assert "Diretório .git encontrado indevidamente dentro de tools/aidd-forge!" in res.stdout


def test_falha_se_skill_sem_yaml_frontmatter(tmp_path):
    gate_path = _montar_arvore_valida(tmp_path)
    skill_file = tmp_path / "skills" / "aidd-forge-runner" / "SKILL.md"
    skill_file.write_text("# Sem frontmatter\nApenas markdown normal.", encoding="utf-8")

    res = rodar_gate(gate_path, tmp_path)
    assert res.returncode == 1
    assert "Frontmatter YAML inválido ou ausente em" in res.stdout


def test_falha_se_slash_command_ausente(tmp_path):
    gate_path = _montar_arvore_valida(tmp_path)
    os.remove(tmp_path / ".agent" / "commands" / "forge.md")

    res = rodar_gate(gate_path, tmp_path)
    assert res.returncode == 1
    assert "forge.md não encontrado" in res.stdout


def test_falha_se_agents_md_ausente(tmp_path):
    gate_path = _montar_arvore_valida(tmp_path)
    os.remove(tmp_path / "AGENTS.md")

    res = rodar_gate(gate_path, tmp_path)
    assert res.returncode == 1
    assert "Arquivo AGENTS.md não encontrado na raiz." in res.stdout
