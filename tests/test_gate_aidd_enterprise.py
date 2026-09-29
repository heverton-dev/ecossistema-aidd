# -*- coding: utf-8 -*-
"""
Teste do Quality Gate Determinístico de aidd-enterprise (Ticket 7 / D13).
Exige que `gates/G_aidd_enterprise.py`:
- aprove (exit 0) manifest de componente conforme (schema + SHA-256);
- reprove (exit 1) componente adulterado, hash divergente, schema quebrado
  e entrada inválida (Lei #13: portão que não morde é fachada).
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
GATE_SCRIPT = ROOT_DIR / "gates" / "G_aidd_enterprise.py"

CONTEUDO = "# Skill enterprise\nComponente integro para o gate.\n"


def executar_gate(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(GATE_SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=str(ROOT_DIR),
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )


def manifest_valido(**trocas) -> dict:
    base = {
        "type": "skill",
        "name": "skill-gate",
        "description": "Componente para validacao do gate.",
        "content": CONTEUDO,
        "sha256": hashlib.sha256(CONTEUDO.encode("utf-8")).hexdigest(),
    }
    base.update(trocas)
    return base


def escrever_manifest(tmp_path: Path, payload: dict) -> Path:
    arquivo = tmp_path / "manifest.json"
    arquivo.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return arquivo


def test_gate_existe():
    assert GATE_SCRIPT.is_file(), f"gate ausente: {GATE_SCRIPT}"


def test_manifest_conforme_retorna_exit_0(tmp_path):
    manifest = escrever_manifest(tmp_path, manifest_valido())
    res = executar_gate("--manifest", str(manifest), "--dir", str(tmp_path))
    assert res.returncode == 0, (
        f"esperava exit 0 para manifest conforme (obtido {res.returncode}): "
        f"{(res.stdout + res.stderr)[-800:]}"
    )


def test_componente_adulterado_reprova_com_exit_1(tmp_path):
    """Bytes do componente divergem do SHA-256 declarado -> exit 1."""
    componente = tmp_path / "SKILL.md"
    componente.write_text(CONTEUDO, encoding="utf-8")
    manifest = escrever_manifest(tmp_path, manifest_valido(arquivo="SKILL.md"))
    # adultera o componente apos a declaracao do hash
    componente.write_text(CONTEUDO + "conteudo adulterado apos assinatura\n", encoding="utf-8")

    res = executar_gate("--manifest", str(manifest), "--dir", str(tmp_path))
    assert res.returncode == 1, f"componente adulterado deve reprovar com exit 1 (obtido {res.returncode})"
    assert "adulter" in (res.stdout + res.stderr).lower()


def test_sha256_divergente_no_manifest_reprova_com_exit_1(tmp_path):
    payload = manifest_valido(sha256="0" * 64)
    manifest = escrever_manifest(tmp_path, payload)
    res = executar_gate("--manifest", str(manifest), "--dir", str(tmp_path))
    assert res.returncode == 1, f"hash divergente deve reprovar com exit 1 (obtido {res.returncode})"


def test_schema_quebrado_reprova_com_exit_1(tmp_path):
    payload = manifest_valido(type="tipo-inexistente")
    payload.pop("content", None)
    manifest = escrever_manifest(tmp_path, payload)
    res = executar_gate("--manifest", str(manifest), "--dir", str(tmp_path))
    assert res.returncode == 1, f"schema quebrado deve reprovar com exit 1 (obtido {res.returncode})"


def test_manifest_sem_sha256_reprova_com_exit_1(tmp_path):
    payload = manifest_valido()
    payload.pop("sha256")
    manifest = escrever_manifest(tmp_path, payload)
    res = executar_gate("--manifest", str(manifest), "--dir", str(tmp_path))
    assert res.returncode == 1, f"manifest sem hash deve reprovar com exit 1 (obtido {res.returncode})"


def test_componente_ausente_reprova_com_exit_1(tmp_path):
    manifest = escrever_manifest(tmp_path, manifest_valido(arquivo="NAO_EXISTE.md"))
    res = executar_gate("--manifest", str(manifest), "--dir", str(tmp_path))
    assert res.returncode == 1, f"componente ausente deve reprovar com exit 1 (obtido {res.returncode})"


def test_json_invalido_reprova_com_exit_1(tmp_path):
    arquivo = tmp_path / "manifest.json"
    arquivo.write_text("{isso nao e json", encoding="utf-8")
    res = executar_gate("--manifest", str(arquivo), "--dir", str(tmp_path))
    assert res.returncode == 1, f"json invalido deve reprovar com exit 1 (obtido {res.returncode})"


def test_sem_argumento_manifest_reprova_com_exit_1():
    res = executar_gate()
    assert res.returncode == 1, f"entrada sem --manifest deve reprovar com exit 1 (obtido {res.returncode})"


def test_manifest_inexistente_reprova_com_exit_1(tmp_path):
    res = executar_gate("--manifest", str(tmp_path / "nao_existe.json"), "--dir", str(tmp_path))
    assert res.returncode == 1, f"manifest inexistente deve reprovar com exit 1 (obtido {res.returncode})"
