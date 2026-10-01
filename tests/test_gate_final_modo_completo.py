# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — TESTE: MODO COMPLETO NO GATE_FINAL E NO AUDIT
=============================================================================
Regra (Ticket 4 - Agilidade Gates / D13):
- No orquestrador 4F, o gate_final deve SEMPRE rodar em modo completo
  (AIDD_GATES_MODO=completo), ignorando qualquer valor herdado do ambiente.
- O gate_fase deve continuar no modo herdado (ex.: rapido).
- O comando 'python ecossistema.py audit' também deve sempre forçar
  AIDD_GATES_MODO=completo para garantir que a auditoria geral do ecossistema
  execute a bateria completa.
=============================================================================
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))
sys.path.insert(0, str(ROOT_DIR))

import orquestrador_4f  # noqa: E402
import ecossistema  # noqa: E402


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
        encoding="utf-8",
    ).stdout.strip()


@pytest.fixture
def repo(tmp_path, monkeypatch):
    r = tmp_path / "repo"
    r.mkdir()
    _git(r, "init", "-q", "-b", "main")
    _git(r, "config", "user.email", "test@test.local")
    _git(r, "config", "user.name", "Test Runner")
    _git(r, "config", "core.hooksPath", "/dev/null")
    (r / "prompt.txt").write_text("prompt", encoding="utf-8")
    (r / "README.md").write_text("base", encoding="utf-8")
    _git(r, "add", "-A")
    _git(r, "commit", "-q", "-m", "base")
    monkeypatch.chdir(r)

    def agente_falso(cmd, cwd=None, input_data=None, expected_handoff=None, titulo=None):
        if expected_handoff:
            expected_handoff.parent.mkdir(parents=True, exist_ok=True)
            expected_handoff.write_text(f"saida {expected_handoff.name}", encoding="utf-8")
        return True

    monkeypatch.setattr(orquestrador_4f, "run_cmd_tty", agente_falso)
    return SimpleNamespace(path=r)


def test_gate_final_forca_modo_completo_e_gate_fase_herda_modo(repo, monkeypatch, capfd):
    monkeypatch.setenv("AIDD_GATES_MODO", "rapido")

    log_fase = repo.path / "modo_fase.txt"
    log_final = repo.path / "modo_final.txt"

    # Fake gate da fase grava o valor e imprime
    cmd_fase = (
        f'"{sys.executable}" -c "import os, pathlib; '
        f'm = os.environ.get(\'AIDD_GATES_MODO\', \'\'); '
        f'print(\'FASE_MODO=\' + m); '
        f'pathlib.Path(r\'{log_fase}\').write_text(m, encoding=\'utf-8\')"'
    )

    # Fake gate final grava o valor e imprime
    cmd_final = (
        f'"{sys.executable}" -c "import os, pathlib; '
        f'm = os.environ.get(\'AIDD_GATES_MODO\', \'\'); '
        f'print(\'FINAL_MODO=\' + m); '
        f'pathlib.Path(r\'{log_final}\').write_text(m, encoding=\'utf-8\')"'
    )

    manifesto_data = {
        "pipeline_id": "aud-modo-ciclo-01",
        "target_tool": "teste",
        "ciclo": "ciclo-01",
        "gate_final": cmd_final,
        "fases": [
            {
                "nome": "Fase_1_Inspetor",
                "comando_terminal": "agente",
                "input_prompt": "prompt.txt",
                "output_handoff": "out/fase1.md",
                "gate_fase": cmd_fase,
            }
        ],
    }

    manifesto_path = repo.path / "manifesto.json"
    manifesto_path.write_text(json.dumps(manifesto_data), encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["orquestrador_4f.py", "--manifest", str(manifesto_path)])
    
    retorno = 0
    try:
        orquestrador_4f.main()
    except SystemExit as e:
        retorno = e.code or 0

    assert retorno == 0, f"Orquestrador falhou com código {retorno}"

    # Valida saída capturada e arquivos de log
    captured = capfd.readouterr()
    assert "FASE_MODO=rapido" in captured.out
    assert "FINAL_MODO=completo" in captured.out

    assert log_fase.exists()
    assert log_fase.read_text(encoding="utf-8").strip() == "rapido"

    assert log_final.exists()
    assert log_final.read_text(encoding="utf-8").strip() == "completo"


def test_ecossistema_audit_forca_modo_completo_pre_commit(monkeypatch):
    monkeypatch.setenv("AIDD_GATES_MODO", "rapido")

    chamadas_env = []

    def fake_run_command(cmd, cwd, env=None):
        chamadas_env.append(env or {})
        return 0

    monkeypatch.setattr(ecossistema, "run_command", fake_run_command)
    import importlib.util
    monkeypatch.setattr(importlib.util, "find_spec", lambda name: object() if name == "pre_commit" else None)

    ret = ecossistema.cmd_audit([])
    assert ret == 0
    assert len(chamadas_env) == 1
    assert chamadas_env[0].get("AIDD_GATES_MODO") == "completo"


def test_ecossistema_audit_forca_modo_completo_legado(monkeypatch):
    monkeypatch.setenv("AIDD_GATES_MODO", "rapido")

    chamadas_env = []

    def fake_run_command(cmd, cwd, env=None):
        chamadas_env.append(env or {})
        return 0

    monkeypatch.setattr(ecossistema, "run_command", fake_run_command)
    monkeypatch.setattr(ecossistema, "_GATES_AUDIT", ["G_FAKE_GATE.py"])
    import importlib.util
    monkeypatch.setattr(importlib.util, "find_spec", lambda name: None)

    ret = ecossistema.cmd_audit([])
    assert ret == 0
    assert len(chamadas_env) == 1
    assert chamadas_env[0].get("AIDD_GATES_MODO") == "completo"
