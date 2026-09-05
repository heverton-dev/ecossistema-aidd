# -*- coding: utf-8 -*-
"""
Suíte de testes do gate determinístico G_INJECT — executa o gate como
subprocesso (mesma forma que scripts/run_all.py o invoca) contra um diretório
de projeto isolado em tmp_path, validando exit code 0 (íntegro) e 1 (falha).
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GATE_SCRIPT = os.path.join(REPO_ROOT, "scripts", "gates", "G_INJECT.py")


def _montar_projeto_fixture(tmp_path):
    """Copia o suficiente de src/core para o gate rodar isolado."""
    shutil.copytree(
        os.path.join(REPO_ROOT, "src", "core"),
        os.path.join(str(tmp_path), "src", "core"),
    )
    (tmp_path / "src" / "__init__.py").touch()


def _run_gate(tmp_path):
    return subprocess.run(
        [sys.executable, GATE_SCRIPT, "--dir", str(tmp_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )


def test_gate_passa_sem_registry(tmp_path):
    _montar_projeto_fixture(tmp_path)
    resultado = _run_gate(tmp_path)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    assert "[OK]" in resultado.stdout


def test_gate_passa_com_registry_integro(tmp_path):
    _montar_projeto_fixture(tmp_path)

    arquivo_rel = "templates/rules/exemplo.md"
    arquivo_path = tmp_path / "templates" / "rules" / "exemplo.md"
    arquivo_path.parent.mkdir(parents=True)
    conteudo = b"conteudo de exemplo"
    arquivo_path.write_bytes(conteudo)

    catalogo = {
        "rule": [{
            "nome": "exemplo",
            "descricao": "",
            "alvo_projeto": "aidd-enterprise",
            "arquivos": [str(arquivo_path)],
            "arquivos_hashes": {arquivo_rel: hashlib.sha256(conteudo).hexdigest()},
            "atualizado_em": "2026-01-01T00:00:00Z",
        }]
    }
    (tmp_path / "CAPABILITIES.json").write_text(json.dumps(catalogo), encoding="utf-8")

    resultado = _run_gate(tmp_path)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr


def test_gate_falha_com_registry_com_hash_divergente(tmp_path):
    _montar_projeto_fixture(tmp_path)

    arquivo_rel = "templates/rules/exemplo.md"
    arquivo_path = tmp_path / "templates" / "rules" / "exemplo.md"
    arquivo_path.parent.mkdir(parents=True)
    arquivo_path.write_bytes(b"conteudo alterado depois do registro")

    catalogo = {
        "rule": [{
            "nome": "exemplo",
            "descricao": "",
            "alvo_projeto": "aidd-enterprise",
            "arquivos": [str(arquivo_path)],
            "arquivos_hashes": {arquivo_rel: hashlib.sha256(b"conteudo original registrado").hexdigest()},
            "atualizado_em": "2026-01-01T00:00:00Z",
        }]
    }
    (tmp_path / "CAPABILITIES.json").write_text(json.dumps(catalogo), encoding="utf-8")

    resultado = _run_gate(tmp_path)
    assert resultado.returncode == 1
    assert "[FAIL]" in resultado.stdout


def test_gate_falha_com_registry_referenciando_arquivo_ausente(tmp_path):
    _montar_projeto_fixture(tmp_path)

    catalogo = {
        "rule": [{
            "nome": "fantasma",
            "descricao": "",
            "alvo_projeto": "aidd-enterprise",
            "arquivos": [str(tmp_path / "templates" / "rules" / "fantasma.md")],
            "arquivos_hashes": {"templates/rules/fantasma.md": "0" * 64},
            "atualizado_em": "2026-01-01T00:00:00Z",
        }]
    }
    (tmp_path / "CAPABILITIES.json").write_text(json.dumps(catalogo), encoding="utf-8")

    resultado = _run_gate(tmp_path)
    assert resultado.returncode == 1


def test_gate_falha_com_registry_json_malformado(tmp_path):
    _montar_projeto_fixture(tmp_path)
    (tmp_path / "CAPABILITIES.json").write_text("{ nao e json valido", encoding="utf-8")

    resultado = _run_gate(tmp_path)
    assert resultado.returncode == 1


def test_gate_falha_sem_schema(tmp_path):
    # Monta fixture mas remove o schema
    _montar_projeto_fixture(tmp_path)
    schema_path = tmp_path / "src" / "core" / "schema_injector_request.json"
    if schema_path.exists():
        schema_path.unlink()
    resultado = _run_gate(tmp_path)
    assert resultado.returncode == 1
    assert "Contrato" in (resultado.stdout + resultado.stderr)
