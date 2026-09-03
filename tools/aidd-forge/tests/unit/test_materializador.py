import json
from pathlib import Path

import pytest

from aidd_forge.core.materializador import (
    ConteudoStubError,
    DestinoExistenteError,
    InjectionRequest,
    MaterializacaoError,
    Materializador,
)


def _request(**overrides) -> InjectionRequest:
    base = dict(tipo="spec", nome="demo-spec", descricao="Uma spec de demonstracao", conteudo="Conteudo real.\n")
    base.update(overrides)
    return InjectionRequest(**base)


def test_materializar_skill_grava_arquivo(tmp_path: Path):
    resultado = Materializador(tmp_path).materializar(
        _request(tipo="skill", nome="demo-skill", conteudo="# Demo\n")
    )

    dest = tmp_path / ".agent" / "skills" / "demo-skill" / "SKILL.md"
    assert resultado.dest == dest
    assert dest.read_text(encoding="utf-8") == "# Demo\n"
    assert resultado.registry_updated is None
    assert resultado.anchor_updated is None


def test_materializar_mcp_atualiza_registry(tmp_path: Path):
    resultado = Materializador(tmp_path).materializar(
        _request(tipo="mcp", nome="demo-mcp", conteudo="def handler():\n    return 1\n")
    )

    registry_path = tmp_path / "aidd_forge" / "mcps" / "registry.json"
    assert resultado.registry_updated == registry_path
    entries = json.loads(registry_path.read_text(encoding="utf-8"))
    assert entries == [
        {"nome": "demo-mcp", "descricao": "Uma spec de demonstracao", "path": "aidd_forge/mcps/demo-mcp.py"}
    ]


def test_materializar_rule_atualiza_anchor(tmp_path: Path):
    (tmp_path / "AGENTS.md").write_text("# AGENTS.md\n", encoding="utf-8")

    resultado = Materializador(tmp_path).materializar(
        _request(tipo="rule", nome="demo-rule", conteudo="Regra real.\n")
    )

    anchor_path = tmp_path / "AGENTS.md"
    assert resultado.anchor_updated == anchor_path
    assert "docs/rules/demo-rule.md" in anchor_path.read_text(encoding="utf-8")


def test_conteudo_vazio_levanta_erro_sem_tocar_disco(tmp_path: Path):
    with pytest.raises(ConteudoStubError):
        Materializador(tmp_path).materializar(_request(conteudo="   "))

    assert not (tmp_path / "docs" / "specs" / "demo-spec.md").exists()


def test_conteudo_placeholder_pass_levanta_erro(tmp_path: Path):
    with pytest.raises(ConteudoStubError):
        Materializador(tmp_path).materializar(_request(conteudo="pass"))


def test_destino_existente_sem_force_levanta_erro(tmp_path: Path):
    materializador = Materializador(tmp_path)
    materializador.materializar(_request())

    with pytest.raises(DestinoExistenteError):
        materializador.materializar(_request())


def test_destino_existente_com_force_sobrescreve(tmp_path: Path):
    materializador = Materializador(tmp_path)
    materializador.materializar(_request(conteudo="Versao 1.\n"))

    materializador.materializar(_request(conteudo="Versao 2.\n"), force=True)

    dest = tmp_path / "docs" / "specs" / "demo-spec.md"
    assert dest.read_text(encoding="utf-8") == "Versao 2.\n"


def test_rollback_remove_arquivo_ja_criado_quando_segunda_escrita_falha(tmp_path: Path, monkeypatch):
    materializador = Materializador(tmp_path)
    original_write = materializador._write
    chamadas = {"n": 0}

    def _write_falha_na_segunda(path, content):
        chamadas["n"] += 1
        if chamadas["n"] == 2:
            raise OSError("falha simulada de I/O")
        original_write(path, content)

    monkeypatch.setattr(materializador, "_write", _write_falha_na_segunda)

    with pytest.raises(MaterializacaoError):
        materializador.materializar(
            _request(tipo="mcp", nome="demo-mcp", conteudo="def handler():\n    return 1\n")
        )

    dest = tmp_path / "aidd_forge" / "mcps" / "demo-mcp.py"
    registry_path = tmp_path / "aidd_forge" / "mcps" / "registry.json"
    assert not dest.exists()
    assert not registry_path.exists()


def test_rollback_restaura_conteudo_original_de_arquivo_preexistente(tmp_path: Path, monkeypatch):
    dest_path = tmp_path / "docs" / "rules" / "demo-rule.md"
    dest_path.parent.mkdir(parents=True)
    dest_path.write_text("Original Regra.\n", encoding="utf-8")

    materializador = Materializador(tmp_path)
    original_write = materializador._write
    chamadas = {"n": 0}

    def _write_falha_na_segunda(path, content):
        chamadas["n"] += 1
        if chamadas["n"] == 2:
            raise OSError("falha simulada de I/O")
        original_write(path, content)

    monkeypatch.setattr(materializador, "_write", _write_falha_na_segunda)

    with pytest.raises(MaterializacaoError):
        materializador.materializar(
            _request(tipo="rule", nome="demo-rule", conteudo="Nova Regra.\n"), force=True
        )

    assert dest_path.read_text(encoding="utf-8") == "Original Regra.\n"
    assert not (tmp_path / "AGENTS.md").exists()
