# -*- coding: utf-8 -*-
"""
Teste do injetor deterministico de aidd-enterprise (Ticket 3 / D8).
Exige:
- Validacao estrita de JSON Schema (component_manifest.schema.json) de payload
  corrompido -> exit 1.
- Verificacao de SHA-256 antes de copiar componentes; hash divergente -> exit 1
  e nenhum arquivo copiado.
- Copia deterministica apenas apos integridade confirmada -> exit 0.
"""

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
INJETOR_PATH = ROOT_DIR / ".agents" / "skills" / "aidd-enterprise" / "scripts" / "injetor.py"
SCHEMA_PATH = (
    ROOT_DIR / "componentes" / "compartilhado" / "injetor" / "schema" / "component_manifest.schema.json"
)


def carregar_injetor():
    spec = importlib.util.spec_from_file_location("aidd_enterprise_injetor", str(INJETOR_PATH))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def manifest_valido(**trocas):
    conteudo = "# Skill enterprise\nConteudo real do componente.\n"
    base = {
        "type": "skill",
        "name": "skill-enterprise",
        "description": "Componente de governanca enterprise.",
        "content": conteudo,
        "sha256": hashlib.sha256(conteudo.encode("utf-8")).hexdigest(),
    }
    base.update(trocas)
    return base


def test_import_injetor():
    mod = carregar_injetor()
    assert hasattr(mod, "validar_manifest")
    assert hasattr(mod, "calcular_sha256")
    assert hasattr(mod, "injetar_componente")
    assert hasattr(mod, "main")
    assert hasattr(mod, "ManifestValidationError")
    assert hasattr(mod, "IntegrityError")


def test_schema_existe_no_repositorio():
    assert SCHEMA_PATH.is_file(), f"schema canonico ausente: {SCHEMA_PATH}"


def test_manifest_valido_e_aceito():
    mod = carregar_injetor()
    normalizado = mod.validar_manifest(manifest_valido())
    assert normalizado["type"] == "skill"
    assert normalizado["name"] == "skill-enterprise"


@pytest.mark.parametrize(
    "trocas",
    [
        {"type": "tipo_invalido"},
        {"name": "Nome_Com_Spasce"},
        {"name": "9-comeca-com-numero"},
        {"type": "mcp", "name": "srv"},  # sem bloco mcp
        {"type": "config", "name": "cfg"},  # sem files
        {"type": "hook"},  # sem content
        {"type": 42},
        {"content": ""},
        {"mcp": {"command": "", "args": "nao-e-lista"}},
        {"files": {}},
        {"description": 123},
    ],
    ids=lambda t: "-".join(f"{k}" for k in t),
)
def test_payload_corrompido_falha_na_validacao(trocas):
    """Payload corrompido (schema) -> ManifestValidationError (exit 1 no main)."""
    mod = carregar_injetor()
    payload = manifest_valido(**trocas)
    if "type" in trocas and trocas["type"] != "skill":
        payload.pop("content", None)
    with pytest.raises(mod.ManifestValidationError):
        mod.validar_manifest(payload)


def test_skill_sem_content_falha_na_validacao():
    """Skill sem content (condicional do schema) -> ManifestValidationError."""
    mod = carregar_injetor()
    payload = manifest_valido()
    payload.pop("content")
    with pytest.raises(mod.ManifestValidationError):
        mod.validar_manifest(payload)


def test_sha256_divergente_falha(tmp_path):
    """Hash divergente -> IntegrityError e nenhum componente copiado."""
    mod = carregar_injetor()
    payload = manifest_valido()
    payload["sha256"] = "0" * 64
    destino = tmp_path / "destino"
    with pytest.raises(mod.IntegrityError):
        mod.injetar_componente(payload, destino=destino, repo_root=tmp_path)
    assert not (destino / "skill-enterprise").exists()


def test_sha256_correto_permite_copia(tmp_path):
    """Hash correto -> componente copiado e hash recalculado bate."""
    mod = carregar_injetor()
    payload = manifest_valido()
    destino = tmp_path / "destino"
    arquivos = mod.injetar_componente(payload, destino=destino, repo_root=tmp_path)
    assert arquivos, "injetar_componente deve copiar ao menos um arquivo"
    for caminho in arquivos:
        assert caminho.exists()
    assert mod.calcular_sha256(payload["content"]) == payload["sha256"]


def test_main_payload_corrompido_exit_1(tmp_path):
    """CLI: payload corrompido -> exit 1."""
    mod = carregar_injetor()
    payload = manifest_valido(type="arquivo-invalido")
    arquivo = tmp_path / "manifest.json"
    arquivo.write_text(json.dumps(payload), encoding="utf-8")
    assert mod.main(["--payload", str(arquivo), "--destino", str(tmp_path / "d"), "--repo-root", str(tmp_path)]) == 1


def test_main_hash_divergente_exit_1(tmp_path):
    """CLI: hash divergente -> exit 1."""
    mod = carregar_injetor()
    payload = manifest_valido()
    payload["sha256"] = hashlib.sha256(b"outra-coisa").hexdigest()
    arquivo = tmp_path / "manifest.json"
    arquivo.write_text(json.dumps(payload), encoding="utf-8")
    destino = tmp_path / "d"
    assert mod.main(["--payload", str(arquivo), "--destino", str(destino), "--repo-root", str(tmp_path)]) == 1
    assert not destino.exists()


def test_main_payload_valido_exit_0(tmp_path):
    """CLI: payload integro -> exit 0."""
    mod = carregar_injetor()
    arquivo = tmp_path / "manifest.json"
    arquivo.write_text(json.dumps(manifest_valido()), encoding="utf-8")
    destino = tmp_path / "d"
    assert mod.main(["--payload", str(arquivo), "--destino", str(destino), "--repo-root", str(tmp_path)]) == 0


def test_main_json_invalido_exit_1(tmp_path):
    """CLI: arquivo que nao e JSON valido -> exit 1."""
    mod = carregar_injetor()
    arquivo = tmp_path / "manifest.json"
    arquivo.write_text("{isso nao e json", encoding="utf-8")
    assert mod.main(["--payload", str(arquivo), "--destino", str(tmp_path / "d"), "--repo-root", str(tmp_path)]) == 1


def test_end_to_end_subprocesso_exit_1(tmp_path):
    """End-to-end: subprocesso com payload corrompido termina com exit 1."""
    payload = manifest_valido()
    payload["type"] = "tipo-invalido"
    arquivo = tmp_path / "manifest.json"
    arquivo.write_text(json.dumps(payload), encoding="utf-8")
    res = subprocess.run(
        [
            sys.executable,
            str(INJETOR_PATH),
            "--payload",
            str(arquivo),
            "--destino",
            str(tmp_path / "d"),
            "--repo-root",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1, f"payload corrompido deve terminar com exit 1 (obtido {res.returncode})"
    assert not (tmp_path / "d").exists()
