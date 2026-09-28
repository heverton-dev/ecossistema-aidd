# -*- coding: utf-8 -*-
"""
Teste de Quality Gate Determinístico de aidd-forge (Ticket 7 / D13 / DoD 6).
Exige que `gates/G_aidd_forge.py`:
- aprove (exit 0) um alvo de bootstrap forge conforme (governança + gates +
  hook pre-commit, sem stubs);
- reprove (exit 1) alvo incompleto, alvo com stub, rótulo ilusório (Lei #8),
  gate sem caminho de falha (Lei #13) e entrada sem --alvo.
"""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
GATE_SCRIPT = ROOT_DIR / "gates" / "G_aidd_forge.py"

AGENTS_CONFORME = """# AGENTS.md

## Leis Invioláveis
1. **Determinism First:** gates determinísticos obrigatórios.
2. **Binary Quality:** exit 0 aprova, exit 1 bloqueia.

Portão: gates/G_aidd_forge.py (provado)
"""

GATE_CONFORME = '''#!/usr/bin/env python3
def main(argv=None):
    violacoes = []
    if violacoes:
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
'''

APP_CONFORME = """def soma(a: int, b: int) -> int:
    return a + b
"""


def executar_gate(alvo: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(GATE_SCRIPT), "--alvo", str(alvo)],
        capture_output=True,
        text=True,
        cwd=str(ROOT_DIR),
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )


def _git_init(alvo: Path) -> None:
    subprocess.run(["git", "init"], cwd=str(alvo), capture_output=True, timeout=60)


def montar_alvo_conforme(alvo: Path) -> Path:
    alvo.mkdir(parents=True, exist_ok=True)
    (alvo / "AGENTS.md").write_text(AGENTS_CONFORME, encoding="utf-8")
    (alvo / "gates").mkdir()
    (alvo / "gates" / "G_BASE.py").write_text(GATE_CONFORME, encoding="utf-8")
    (alvo / "app.py").write_text(APP_CONFORME, encoding="utf-8")
    _git_init(alvo)
    hooks = alvo / ".git" / "hooks"
    hooks.mkdir(parents=True, exist_ok=True)
    (hooks / "pre-commit").write_text("#!/bin/sh\npython gates/G_BASE.py\n", encoding="utf-8")
    return alvo


def test_alvo_conforme_aprova_exit_0(tmp_path):
    alvo = montar_alvo_conforme(tmp_path / "conforme")
    res = executar_gate(alvo)
    assert res.returncode == 0, f"alvo conforme deve aprovar (obtido {res.returncode}): {res.stdout[-800:]} {res.stderr[-400:]}"


def test_alvo_sem_agents_md_reprova_exit_1(tmp_path):
    alvo = montar_alvo_conforme(tmp_path / "sem_agents")
    (alvo / "AGENTS.md").unlink()
    res = executar_gate(alvo)
    assert res.returncode == 1, f"AGENTS.md ausente deve reprovar (obtido {res.returncode})"


def test_alvo_com_stub_reprova_exit_1(tmp_path):
    alvo = montar_alvo_conforme(tmp_path / "com_stub")
    (alvo / "stub.py").write_text("def pendente():\n    ...\n", encoding="utf-8")
    res = executar_gate(alvo)
    assert res.returncode == 1, f"stub deve reprovar (obtido {res.returncode})"


def test_rotulo_ilusorio_reprova_exit_1(tmp_path):
    """Lei #8: alegação de '100% testado' sem evidência é vetada."""
    alvo = montar_alvo_conforme(tmp_path / "rotulo_ilusorio")
    (alvo / "AGENTS.md").write_text(AGENTS_CONFORME + "\nProjeto 100% testado.\n", encoding="utf-8")
    res = executar_gate(alvo)
    assert res.returncode == 1, f"rótulo ilusório deve reprovar (obtido {res.returncode})"


def test_gate_sem_caminho_de_falha_reprova_exit_1(tmp_path):
    """Lei #13: gate do alvo sem caminho de falha (return 1) é reprovado."""
    alvo = montar_alvo_conforme(tmp_path / "gate_sem_falha")
    (alvo / "gates" / "G_BASE.py").write_text(
        "def main(argv=None):\n    return 0\n", encoding="utf-8"
    )
    res = executar_gate(alvo)
    assert res.returncode == 1, f"gate sem caminho de falha deve reprovar (obtido {res.returncode})"


def test_alvo_sem_hook_pre_commit_reprova_exit_1(tmp_path):
    alvo = montar_alvo_conforme(tmp_path / "sem_hook")
    (alvo / ".git" / "hooks" / "pre-commit").unlink()
    res = executar_gate(alvo)
    assert res.returncode == 1, f"hook ausente deve reprovar (obtido {res.returncode})"


def test_sem_alvo_reprova_exit_1():
    res = subprocess.run(
        [sys.executable, str(GATE_SCRIPT)],
        capture_output=True,
        text=True,
        cwd=str(ROOT_DIR),
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    assert res.returncode == 1, f"entrada sem --alvo deve reprovar (obtido {res.returncode})"
