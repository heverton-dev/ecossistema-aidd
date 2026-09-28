# -*- coding: utf-8 -*-
"""
Teste do handoff estruturado de aidd-forge (Ticket 9 / D15 / DoD 8).
Exige:
- Bootstrap concluído sem ./handoff-forge.json -> exit 1.
- Emissão de handoff-forge.json estruturado com hashes SHA-256 dos componentes
  para o handoff ao aidd-planner.
- Verificação de integridade (arquivo ausente, JSON inválido ou hash divergente
  -> exit 1).
"""

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
CLI_PATH = ROOT_DIR / ".agents" / "skills" / "aidd-forge" / "scripts" / "cli.py"
HANDOFF_ARQUIVO = "handoff-forge.json"


def carregar_cli():
    spec = importlib.util.spec_from_file_location("aidd_forge_cli_handoff", str(CLI_PATH))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _montar_componente(raiz: Path, relativo: str) -> Path:
    arquivo = raiz / relativo
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    arquivo.write_text(f"# componente {relativo}\nVALOR = 1\n", encoding="utf-8")
    return arquivo


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_bootstrap_sem_handoff_json_retorna_exit_1(tmp_path):
    """Verificação pós-bootstrap sem ./handoff-forge.json -> exit 1."""
    cli = carregar_cli()
    assert cli.main(["handoff", "verify", "--path", str(tmp_path)]) == 1


def test_emitir_handoff_gera_json_com_hashes_sha256(tmp_path):
    cli = carregar_cli()
    _montar_componente(tmp_path, "scripts/modulo_a.py")
    _montar_componente(tmp_path, "scripts/modulo_b.py")

    codigo = cli.main(
        [
            "handoff", "emit",
            "--path", str(tmp_path),
            "--componente", "scripts/modulo_a.py",
            "--componente", "scripts/modulo_b.py",
        ]
    )
    assert codigo == 0

    arquivo = tmp_path / HANDOFF_ARQUIVO
    assert arquivo.is_file()
    dados = json.loads(arquivo.read_text(encoding="utf-8"))
    assert dados["consumidor"] == "aidd-planner"
    assert dados["ferramenta"] == "aidd-forge"
    componentes = {c["caminho"]: c for c in dados["componentes"]}
    assert set(componentes) == {"scripts/modulo_a.py", "scripts/modulo_b.py"}
    assert componentes["scripts/modulo_a.py"]["sha256"] == _sha256(tmp_path / "scripts" / "modulo_a.py")
    assert componentes["scripts/modulo_b.py"]["sha256"] == _sha256(tmp_path / "scripts" / "modulo_b.py")


def test_verify_apos_emit_retorna_exit_0(tmp_path):
    cli = carregar_cli()
    _montar_componente(tmp_path, "scripts/modulo_a.py")
    assert cli.main(["handoff", "emit", "--path", str(tmp_path), "--componente", "scripts/modulo_a.py"]) == 0
    assert cli.main(["handoff", "verify", "--path", str(tmp_path), "--componente", "scripts/modulo_a.py"]) == 0


def test_verify_com_hash_divergente_retorna_exit_1(tmp_path):
    cli = carregar_cli()
    alvo = _montar_componente(tmp_path, "scripts/modulo_a.py")
    assert cli.main(["handoff", "emit", "--path", str(tmp_path), "--componente", "scripts/modulo_a.py"]) == 0
    alvo.write_text("# componente alterado pos-handoff\nVALOR = 2\n", encoding="utf-8")
    assert cli.main(["handoff", "verify", "--path", str(tmp_path), "--componente", "scripts/modulo_a.py"]) == 1


def test_verify_com_json_invalido_retorna_exit_1(tmp_path):
    cli = carregar_cli()
    (tmp_path / HANDOFF_ARQUIVO).write_text("{quebrado", encoding="utf-8")
    assert cli.main(["handoff", "verify", "--path", str(tmp_path), "--componente", "x.py"]) == 1


def test_handoff_sem_modo_retorna_exit_1():
    cli = carregar_cli()
    assert cli.main(["handoff"]) == 1


def test_subprocesso_e2e_exit_1_sem_handoff_e_exit_0_com_handoff(tmp_path):
    _montar_componente(tmp_path, "scripts/modulo_a.py")
    res1 = subprocess.run(
        [
            sys.executable, str(CLI_PATH),
            "handoff", "verify", "--path", str(tmp_path),
            "--componente", "scripts/modulo_a.py",
        ],
        capture_output=True,
        text=True,
        cwd=str(ROOT_DIR),
        timeout=120,
    )
    assert res1.returncode == 1, f"sem handoff-forge.json deve dar exit 1 (obtido {res1.returncode})"

    res2 = subprocess.run(
        [
            sys.executable, str(CLI_PATH),
            "handoff", "emit", "--path", str(tmp_path),
            "--componente", "scripts/modulo_a.py",
        ],
        capture_output=True,
        text=True,
        cwd=str(ROOT_DIR),
        timeout=120,
    )
    assert res2.returncode == 0, f"emit deve dar exit 0 (obtido {res2.returncode}): {res2.stderr[-400:]}"

    res3 = subprocess.run(
        [
            sys.executable, str(CLI_PATH),
            "handoff", "verify", "--path", str(tmp_path),
            "--componente", "scripts/modulo_a.py",
        ],
        capture_output=True,
        text=True,
        cwd=str(ROOT_DIR),
        timeout=120,
    )
    assert res3.returncode == 0, f"verify apos emit deve dar exit 0 (obtido {res3.returncode}): {res3.stderr[-400:]}"
