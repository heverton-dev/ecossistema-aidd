# -*- coding: utf-8 -*-
"""
Espelho obrigatório do Quality Gate G_aidd_enterprise (Lei #13).
Prova que o portão morde: componente adulterado e schema quebrado retornam
returncode == 1; manifest conforme retorna returncode == 0.
Suíte completa em tests/test_gate_aidd_enterprise.py.
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT_DIR = next((p.parent for p in Path(__file__).resolve().parents if p.name == "modulos"), Path(__file__).resolve().parent.parent)  # raiz: pai de modulos/ (VSA) ou de gates/ (árvore sintética)
GATE_SCRIPT = ROOT_DIR / "modulos" / "03-plataforma-e-entrega" / "gates" / "G_aidd_enterprise.py"

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


def test_gate_aprova_manifest_conforme(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(manifest_valido()), encoding="utf-8")
    res = executar_gate("--manifest", str(manifest), "--dir", str(tmp_path))
    assert res.returncode == 0, f"esperava exit 0 (obtido {res.returncode})"


def test_gate_detecta_componente_adulterado(tmp_path):
    componente = tmp_path / "SKILL.md"
    componente.write_text(CONTEUDO, encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(manifest_valido(arquivo="SKILL.md")), encoding="utf-8")
    componente.write_text(CONTEUDO + "adulterado\n", encoding="utf-8")

    res = executar_gate("--manifest", str(manifest), "--dir", str(tmp_path))
    assert res.returncode == 1, f"componente adulterado deve retornar returncode == 1 (obtido {res.returncode})"


def test_gate_reprova_schema_quebrado(tmp_path):
    payload = manifest_valido(type="tipo-inexistente")
    payload.pop("content", None)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    res = executar_gate("--manifest", str(manifest), "--dir", str(tmp_path))
    assert res.returncode == 1, f"schema quebrado deve retornar returncode == 1 (obtido {res.returncode})"


def test_gate_reprova_entrada_sem_manifest():
    res = executar_gate()
    assert res.returncode == 1, f"entrada invalida deve retornar returncode == 1 (obtido {res.returncode})"
