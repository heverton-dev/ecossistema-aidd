#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_g_zero_headless.py - Testes determinísticos do gate G_ZERO_HEADLESS e do hook anti-headless.
Valida aprovação em repositório íntegro, reprodução real de bloqueio e permissão,
e reprovação comprovada (exit 1) quando a condição protegida é violada (Lei #13).
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import pytest

from _gate_test_utils import rodar_gate

GATE_DIR = os.path.dirname(os.path.abspath(__file__))
GATE_PATH = os.path.join(GATE_DIR, "G_ZERO_HEADLESS.py")
ROOT_DIR = os.path.dirname(GATE_DIR)
HOOK_PATH = os.path.join(ROOT_DIR, "componentes", "compartilhado", "hooks", "anti_headless_subagent_hook.py")


def test_g_zero_headless_passa_no_repositorio():
    """Valida que o repositório atual passa com exit 0 no G_ZERO_HEADLESS e exercita o hook."""
    proc = rodar_gate(GATE_PATH, cwd=ROOT_DIR)
    assert proc.returncode == 0, f"G_ZERO_HEADLESS reprovou com saida:\n{proc.stdout}\n{proc.stderr}"
    assert "APROVADO" in proc.stdout
    assert "Tentativa paralela sem confirma" in proc.stdout
    assert "EFETIVAMENTE BLOQUEADA" in proc.stdout
    assert "LIMITE CONHECIDO" in proc.stdout


def test_hook_reproducao_bloqueia_dois_agentes_paralelos(tmp_path):
    """
    Reprodução Real: tentativa de disparar 2 subagentes paralelos sem confirmação
    deve ser EFETIVAMENTE BLOQUEADA com código != 0 e mensagem visível na saída.
    """
    lock_file = tmp_path / "subagent.lock"
    payload = {
        "tool_name": "Task",
        "tool_input": {
            "subagents": [
                {"name": "worker_1", "task": "tarefa_1"},
                {"name": "worker_2", "task": "tarefa_2"}
            ],
            "user_confirmed": False
        }
    }
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    res = subprocess.run(
        [sys.executable, HOOK_PATH, "--lock-file", str(lock_file)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env
    )
    saida = (res.stdout or "") + "\n" + (res.stderr or "")
    assert res.returncode != 0, f"O hook deveria ter bloqueado, mas retornou code 0. Saída:\n{saida}"
    assert "[BLOQUEIO G_ZERO_HEADLESS]" in saida
    assert "paralelo" in saida.lower()


def test_hook_reproducao_bloqueia_concorrencia_com_agente_ativo(tmp_path):
    """
    Reprodução Real: tentativa de disparar subagente concorrente enquanto outro
    está ativo no lockfile deve ser EFETIVAMENTE BLOQUEADA.
    """
    lock_file = tmp_path / "subagent.lock"
    lock_data = {
        "pid": os.getpid(),
        "agent_name": "agente-em-execucao",
        "timestamp": 9999999999.0
    }
    lock_file.write_text(json.dumps(lock_data), encoding="utf-8")

    payload = {
        "tool_name": "Agent",
        "tool_input": {"prompt": "Tarefa concorrente silenciosa"},
        "user_confirmed": False
    }
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    res = subprocess.run(
        [sys.executable, HOOK_PATH, "--lock-file", str(lock_file)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env
    )
    saida = (res.stdout or "") + "\n" + (res.stderr or "")
    assert res.returncode != 0, f"Deveria ter bloqueado a concorrência, retornou code 0. Saída:\n{saida}"
    assert "[BLOQUEIO G_ZERO_HEADLESS]" in saida


def test_hook_reproducao_permite_caminho_legitimo_com_confirmacao(tmp_path):
    """
    Reprodução Real: lançamento com confirmação explícita do usuário é PERMITIDO (exit 0).
    """
    lock_file = tmp_path / "subagent.lock"
    payload = {
        "tool_name": "Task",
        "tool_input": {
            "subagents": [{"name": "worker_1", "task": "tarefa_1"}],
            "user_confirmed": True
        }
    }
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    res = subprocess.run(
        [sys.executable, HOOK_PATH, "--lock-file", str(lock_file)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env
    )
    saida = (res.stdout or "") + "\n" + (res.stderr or "")
    assert res.returncode == 0, f"O hook deveria ter permitido, mas retornou {res.returncode}. Saída:\n{saida}"
    assert "[PERMITIDO]" in saida


def test_g_zero_headless_reprova_se_hook_nao_bloquear_paralelos(tmp_path):
    """
    Lei #13: Valida que G_ZERO_HEADLESS reprova (exit 1) se o hook de intercepção
    for adulterado para não bloquear chamadas paralelas (falha da proteção).
    """
    fake_gates = tmp_path / "gates"
    fake_gates.mkdir()
    shutil.copy2(GATE_PATH, fake_gates / "G_ZERO_HEADLESS.py")

    # Hook falso permissivo que não bloqueia (fachada / bug)
    fake_hooks_dir = tmp_path / "componentes" / "compartilhado" / "hooks"
    fake_hooks_dir.mkdir(parents=True)
    fake_hook = fake_hooks_dir / "anti_headless_subagent_hook.py"
    fake_hook.write_text("#!/usr/bin/env python3\nimport sys\nprint('[FACHADA] tudo liberado')\nsys.exit(0)\n", encoding="utf-8")

    fake_claude_hooks = tmp_path / ".claude" / "hooks"
    fake_claude_hooks.mkdir(parents=True)
    shutil.copy2(fake_hook, fake_claude_hooks / "anti_headless_subagent_hook.py")

    fake_settings = tmp_path / ".claude" / "settings.json"
    fake_settings.write_text(json.dumps({
        "hooks": {
            "PreToolUse": [{"matcher": "Task|Agent", "hooks": [{"command": "python anti_headless_subagent_hook.py"}]}]
        }
    }), encoding="utf-8")

    fake_engine_dir = tmp_path / "componentes" / "compartilhado" / "skills" / "orca-plan-orchestrator" / "scripts"
    fake_engine_dir.mkdir(parents=True)
    (fake_engine_dir / "orchestrator_engine.py").write_text("interactive: bool = True\n", encoding="utf-8")

    (tmp_path / "ecossistema.py").write_text("@click.option(\"--dangerously-force-headless\")\n", encoding="utf-8")

    proc = rodar_gate(str(fake_gates / "G_ZERO_HEADLESS.py"), cwd=str(tmp_path))
    assert proc.returncode == 1, f"Gate deveria ter reprovado com returncode 1, mas retornou {proc.returncode}"
    assert "Hook FALHOU em bloquear" in proc.stdout


def test_g_zero_headless_reprova_se_hook_estiver_desconfigurado(tmp_path):
    """
    Lei #13: Valida que G_ZERO_HEADLESS reprova (exit 1) se o settings.json não tiver o hook registrado.
    """
    fake_gates = tmp_path / "gates"
    fake_gates.mkdir()
    shutil.copy2(GATE_PATH, fake_gates / "G_ZERO_HEADLESS.py")

    fake_hooks_dir = tmp_path / "componentes" / "compartilhado" / "hooks"
    fake_hooks_dir.mkdir(parents=True)
    shutil.copy2(HOOK_PATH, fake_hooks_dir / "anti_headless_subagent_hook.py")

    fake_claude_hooks = tmp_path / ".claude" / "hooks"
    fake_claude_hooks.mkdir(parents=True)
    shutil.copy2(HOOK_PATH, fake_claude_hooks / "anti_headless_subagent_hook.py")

    # Settings sem o hook em PreToolUse
    fake_settings = tmp_path / ".claude" / "settings.json"
    fake_settings.write_text(json.dumps({"hooks": {}}), encoding="utf-8")

    fake_engine_dir = tmp_path / "componentes" / "compartilhado" / "skills" / "orca-plan-orchestrator" / "scripts"
    fake_engine_dir.mkdir(parents=True)
    (fake_engine_dir / "orchestrator_engine.py").write_text("interactive: bool = True\n", encoding="utf-8")
    (tmp_path / "ecossistema.py").write_text("@click.option(\"--dangerously-force-headless\")\n", encoding="utf-8")

    proc = rodar_gate(str(fake_gates / "G_ZERO_HEADLESS.py"), cwd=str(tmp_path))
    assert proc.returncode == 1, f"Gate deveria ter reprovado com 1, retornou {proc.returncode}"
    assert "Hook anti_headless_subagent_hook não registrado" in proc.stdout
