#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
TESTES DE QUALIDADE: G_SKILL_ROT (ISSUE-0016 & Lei Canônica #13)
=============================================================================
Testa o Quality Gate G_SKILL_ROT assegurando estrita adesão à Lei #13:
O portão deve provar que reprova (exit 1) sob violação comprovada.

Casos cobertos:
  1. Reprovação comprovada quando script referenciado é renomeado/ausente.
  2. Reprovação do caso real de regressão: sandeco-token-reduce (ambiente .venv inalcançável).
  3. Reprovação quando caminho sob repo (docs/..., tools/...) não existe.
  4. Reprovação quando subcomando de CLI ecossistema.py é desconhecido.
  5. Reprovação quando link markdown aponta para arquivo inexistente.
  6. Reprovação quando skill órfã existe em mirror de harness sem fonte canônica.
  7. Execução real via subprocess assegurando returncode == 1 em falha.
  8. Aprovação (exit 0) de skill 100% conforme.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from gates.G_SKILL_ROT import (
    auditar_skills,
    auditar_orfaos_em_mirrors,
    resolver_referencia_estatica,
    extrair_referencias_skill_md,
    ReferenciaSkill,
    obter_subcomandos_ecossistema,
)

GATE_SCRIPT = os.path.join(ROOT_DIR, "gates", "G_SKILL_ROT.py")


def test_gate_aprova_estado_atual_do_repositorio():
    """Valida que todas as skills ativas do repositório estão 100% resolvíveis (exit 0)."""
    code, falhas, conformes, total = auditar_skills()
    assert code == 0
    assert len(falhas) == 0
    assert total >= 300
    orfaos = auditar_orfaos_em_mirrors()
    assert len(orfaos) == 0


def test_gate_reprova_quando_script_referenciado_e_renomeado():
    """
    Exigência estrita da Lei #13 / ISSUE-0016:
    Renomeia um script referenciado em uma skill, executa o gate e asserta exit 1.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        skill_dir = os.path.join(temp_dir, "minha-skill-teste")
        scripts_dir = os.path.join(skill_dir, "scripts")
        os.makedirs(scripts_dir, exist_ok=True)

        original_script = os.path.join(scripts_dir, "run_task.py")
        with open(original_script, "w", encoding="utf-8") as f:
            f.write("#!/usr/bin/env python3\nprint('ok')\n")

        skill_md = os.path.join(skill_dir, "SKILL.md")
        with open(skill_md, "w", encoding="utf-8") as f:
            f.write(
                "---\nname: minha-skill-teste\ndescription: Teste\n---\n\n"
                "# Minha Skill\n\n"
                "Para executar a tarefa:\n"
                "```bash\n"
                "python scripts/run_task.py\n"
                "```\n"
            )

        # 1. Antes de renomear, deve aprovar (exit 0)
        code, falhas, conformes, total = auditar_skills(temp_dir, ROOT_DIR)
        assert code == 0
        assert len(falhas) == 0

        # 2. Renomeia o script para simular rot/divergência
        renamed_script = os.path.join(scripts_dir, "run_task_renomeado.py")
        os.rename(original_script, renamed_script)

        # 3. Executa o gate e asserte estritamente exit 1
        code, falhas, conformes, total = auditar_skills(temp_dir, ROOT_DIR)
        assert code == 1
        assert len(falhas) >= 1
        assert any("run_task.py" in f["texto"] and "não existe" in f["motivo"] for f in falhas)


def test_gate_reprova_regression_fixture_sandeco():
    """
    Exigência da ISSUE-0016:
    O caso da skill sandeco-token-reduce (onde comandos instruem execução em
    .venv/Scripts/python.exe ou interpretador virtual isolado não versionado)
    deve ser estritamente bloqueado (exit 1).
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        sandeco_dir = os.path.join(temp_dir, "sandeco-token-reduce")
        os.makedirs(sandeco_dir, exist_ok=True)
        skill_md = os.path.join(sandeco_dir, "SKILL.md")
        with open(skill_md, "w", encoding="utf-8") as f:
            f.write(
                "---\nname: sandeco-token-reduce\ndescription: LLMLingua-2 compression\n---\n\n"
                "# sandeco-token-reduce\n\n"
                "O Python do venv esta em:\n"
                "- Windows: `<skill-dir>/.venv/Scripts/python.exe`\n"
                "- Unix: `<skill-dir>/.venv/bin/python`\n\n"
                "Para comprimir:\n"
                "```bash\n"
                "\"<venv-python>\" \"<skill-dir>/scripts/compress.py\" --rate 0.4\n"
                "```\n"
            )

        code, falhas, conformes, total = auditar_skills(temp_dir, ROOT_DIR)
        assert code == 1
        assert len(falhas) >= 1
        # Verifica se apontou erro nos caminhos do venv inexistente
        assert any(".venv" in f["texto"] for f in falhas)


def test_gate_reprova_caminho_inexistente_no_repositorio():
    """Bloqueia se uma skill referenciar arquivo inexistente em docs/ ou tools/."""
    with tempfile.TemporaryDirectory() as temp_dir:
        skill_dir = os.path.join(temp_dir, "skill-bad-path")
        os.makedirs(skill_dir, exist_ok=True)
        skill_md = os.path.join(skill_dir, "SKILL.md")
        with open(skill_md, "w", encoding="utf-8") as f:
            f.write(
                "---\nname: skill-bad-path\ndescription: Teste\n---\n\n"
                "Consulte o documento em `docs/planos/ARQUIVO_QUE_NUNCA_EXISTIU.md`.\n"
            )

        code, falhas, conformes, total = auditar_skills(temp_dir, ROOT_DIR)
        assert code == 1
        assert any("ARQUIVO_QUE_NUNCA_EXISTIU.md" in f["texto"] for f in falhas)


def test_gate_reprova_subcomando_ecossistema_inexistente():
    """Bloqueia se uma skill instruir um subcomando CLI que não existe em ecossistema.py."""
    with tempfile.TemporaryDirectory() as temp_dir:
        skill_dir = os.path.join(temp_dir, "skill-bad-cmd")
        os.makedirs(skill_dir, exist_ok=True)
        skill_md = os.path.join(skill_dir, "SKILL.md")
        with open(skill_md, "w", encoding="utf-8") as f:
            f.write(
                "---\nname: skill-bad-cmd\ndescription: Teste\n---\n\n"
                "Execute o comando:\n"
                "```bash\n"
                "python ecossistema.py subcomando-totalmente-inexistente --flag 1\n"
                "```\n"
            )

        code, falhas, conformes, total = auditar_skills(temp_dir, ROOT_DIR)
        assert code == 1
        assert any("subcomando-totalmente-inexistente" in f["texto"] for f in falhas)


def test_gate_reprova_link_markdown_quebrado():
    """Bloqueia links markdown apontando para arquivos locais inexistentes."""
    with tempfile.TemporaryDirectory() as temp_dir:
        skill_dir = os.path.join(temp_dir, "skill-broken-link")
        os.makedirs(skill_dir, exist_ok=True)
        skill_md = os.path.join(skill_dir, "SKILL.md")
        with open(skill_md, "w", encoding="utf-8") as f:
            f.write(
                "---\nname: skill-broken-link\ndescription: Teste\n---\n\n"
                "Leia o [Guia Avançado](reference/guia-fantasma.md) antes de iniciar.\n"
            )

        code, falhas, conformes, total = auditar_skills(temp_dir, ROOT_DIR)
        assert code == 1
        assert any("guia-fantasma.md" in f["texto"] for f in falhas)


def test_gate_reprova_skill_orfa_no_harness():
    """Verifica detecção de skill existente no harness mas sem fonte canônica."""
    with tempfile.TemporaryDirectory() as temp_root:
        # Criar árvore simulada com componentes/compartilhado/skills e .claude/skills
        canon_skills = os.path.join(temp_root, "componentes", "compartilhado", "skills")
        claude_skills = os.path.join(temp_root, ".claude", "skills")
        os.makedirs(canon_skills, exist_ok=True)
        os.makedirs(claude_skills, exist_ok=True)

        # Skill canônica legítima
        os.makedirs(os.path.join(canon_skills, "skill-legitima"), exist_ok=True)
        with open(os.path.join(canon_skills, "skill-legitima", "SKILL.md"), "w") as f:
            f.write("---\nname: skill-legitima\n---\n")

        # Skill no harness idêntica à canônica
        os.makedirs(os.path.join(claude_skills, "skill-legitima"), exist_ok=True)
        with open(os.path.join(claude_skills, "skill-legitima", "SKILL.md"), "w") as f:
            f.write("---\nname: skill-legitima\n---\n")

        # Skill órfã criada apenas no harness
        os.makedirs(os.path.join(claude_skills, "skill-fantasma-orfa"), exist_ok=True)
        with open(os.path.join(claude_skills, "skill-fantasma-orfa", "SKILL.md"), "w") as f:
            f.write("---\nname: skill-fantasma-orfa\n---\n")

        orfaos = auditar_orfaos_em_mirrors(temp_root)
        assert len(orfaos) == 1
        assert "skill-fantasma-orfa" in orfaos[0]


def test_gate_subprocess_execucao_real_exit_1():
    """Valida a execução de ponta a ponta do script via subprocess retornando código 1."""
    with tempfile.TemporaryDirectory() as temp_dir:
        skill_dir = os.path.join(temp_dir, "skill-quebrada")
        os.makedirs(skill_dir, exist_ok=True)
        skill_md = os.path.join(skill_dir, "SKILL.md")
        with open(skill_md, "w", encoding="utf-8") as f:
            f.write(
                "---\nname: skill-quebrada\ndescription: Teste\n---\n\n"
                "```bash\n"
                "python scripts/script_que_nao_existe.py\n"
                "```\n"
            )

        res = subprocess.run(
            [sys.executable, GATE_SCRIPT, "--skills-dir", temp_dir, "--repo-root", ROOT_DIR],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert res.returncode == 1
        assert "[FALHA]" in res.stdout
        assert "script_que_nao_existe.py" in res.stdout
