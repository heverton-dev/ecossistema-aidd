# -*- coding: utf-8 -*-
"""
Suíte de testes unitários do Universal Component Injector (aidd_core_injector).
Valida contrato, resolução de rotas por Target Profile, dry-run, fan-out
multi-harness, rollback transacional em falha parcial, merge de mcp.json,
rejeição de path-traversal e atualização idempotente do registry.
"""

import builtins
import hashlib
import json
import os
import sys

import pytest

SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from injector import aidd_core_injector as injector_core
from injector import target_profile


# ---------------------------------------------------------------------------
# validate_component
# ---------------------------------------------------------------------------

def test_validate_component_skill_valido():
    resultado = injector_core.validate_component(
        {"type": "skill", "name": "minha-skill", "description": "desc", "content": "corpo"}
    )
    assert resultado.sucesso is True


def test_validate_component_type_invalido():
    resultado = injector_core.validate_component({"type": "nao-existe", "name": "x", "content": "y"})
    assert resultado.sucesso is False
    assert resultado.codigo == "TYPE_INVALIDO"


@pytest.mark.parametrize("nome_invalido", ["Maiuscula", "1comeca-com-numero", "com espaco", "com_underscore"])
def test_validate_component_name_invalido(nome_invalido):
    resultado = injector_core.validate_component({"type": "rule", "name": nome_invalido, "content": "x"})
    assert resultado.sucesso is False
    assert resultado.codigo == "NAME_INVALIDO"


def test_validate_component_skill_sem_content():
    resultado = injector_core.validate_component({"type": "skill", "name": "sem-conteudo"})
    assert resultado.sucesso is False
    assert resultado.codigo == "CONTENT_AUSENTE"


def test_validate_component_mcp_sem_command():
    resultado = injector_core.validate_component({"type": "mcp", "name": "meu-mcp", "mcp": {}})
    assert resultado.sucesso is False
    assert resultado.codigo == "MCP_INVALIDO"


def test_validate_component_config_sem_files():
    resultado = injector_core.validate_component({"type": "config", "name": "minha-config"})
    assert resultado.sucesso is False
    assert resultado.codigo == "FILES_AUSENTE"


# ---------------------------------------------------------------------------
# resolve_targets / target_profile (rotas por type)
# ---------------------------------------------------------------------------

def test_resolve_targets_skill_fan_out_5_harnesses(tmp_path):
    resultado = injector_core.resolve_targets(
        {"type": "skill", "name": "foo", "content": "corpo"}, str(tmp_path)
    )
    assert resultado.sucesso is True
    caminhos = set(resultado.valor.keys())
    assert caminhos == {
        ".claude/skills/foo/SKILL.md",
        ".agent/skills/foo/SKILL.md",
        ".mimocode/skills/foo/SKILL.md",
        ".gemini/skills/foo/SKILL.md",
        ".skills/foo/SKILL.md",
    }
    for conteudo in resultado.valor.values():
        assert conteudo == b"corpo"


def test_resolve_targets_hook_fan_out_5_harnesses(tmp_path):
    resultado = injector_core.resolve_targets(
        {"type": "hook", "name": "foo", "content": "{}"}, str(tmp_path)
    )
    assert resultado.sucesso is True
    assert set(resultado.valor.keys()) == {
        ".claude/hooks/foo.json",
        ".agent/hooks/foo.json",
        ".mimocode/hooks/foo.json",
        ".gemini/hooks/foo.json",
        ".hooks/foo.json",
    }


def test_resolve_targets_rule_single_file(tmp_path):
    resultado = injector_core.resolve_targets({"type": "rule", "name": "foo", "content": "corpo"}, str(tmp_path))
    assert resultado.sucesso is True
    assert resultado.valor == {"templates/rules/foo.md": b"corpo"}


def test_resolve_targets_spec_single_file(tmp_path):
    resultado = injector_core.resolve_targets({"type": "spec", "name": "foo", "content": "corpo"}, str(tmp_path))
    assert resultado.valor == {"docs/specs/foo.md": b"corpo"}


def test_resolve_targets_agent_single_file(tmp_path):
    resultado = injector_core.resolve_targets({"type": "agent", "name": "foo", "content": "corpo"}, str(tmp_path))
    assert resultado.valor == {"templates/agents/foo.md": b"corpo"}


def test_resolve_targets_config_generic_files(tmp_path):
    resultado = injector_core.resolve_targets(
        {"type": "config", "name": "foo", "files": {"a/b.txt": "conteudo-x"}}, str(tmp_path)
    )
    assert resultado.sucesso is True
    assert resultado.valor == {"a/b.txt": b"conteudo-x"}


def test_resolve_targets_config_rejeita_path_traversal(tmp_path):
    resultado = injector_core.resolve_targets(
        {"type": "config", "name": "foo", "files": {"../fora-do-repo.txt": "x"}}, str(tmp_path)
    )
    assert resultado.sucesso is False
    assert resultado.codigo == "PATH_TRAVERSAL_REJEITADO"


def test_resolve_targets_mcp_merge(tmp_path):
    resultado = injector_core.resolve_targets(
        {"type": "mcp", "name": "meu-servidor", "mcp": {"command": "python", "args": ["a.py"], "env": {"X": "1"}}},
        str(tmp_path),
    )
    assert resultado.sucesso is True
    assert list(resultado.valor.keys()) == ["mcp.json"]
    dados = json.loads(resultado.valor["mcp.json"])
    assert dados["mcpServers"]["meu-servidor"]["command"] == "python"


# ---------------------------------------------------------------------------
# materialize — dry_run
# ---------------------------------------------------------------------------

def test_materialize_dry_run_nao_escreve_nada(tmp_path):
    component = {"type": "skill", "name": "dry-run-teste", "description": "", "content": "corpo"}
    resultado = injector_core.materialize(component, base_dir=str(tmp_path), dry_run=True)

    assert resultado.sucesso is True
    assert resultado.detalhes.get("dry_run") is True
    assert len(resultado.valor) == 5
    assert not (tmp_path / ".claude" / "skills" / "dry-run-teste" / "SKILL.md").exists()
    assert not (tmp_path / "COMPONENT-REGISTRY.json").exists()


# ---------------------------------------------------------------------------
# materialize — fan-out real + registry
# ---------------------------------------------------------------------------

def test_materialize_skill_fan_out_identico_e_registry(tmp_path):
    component = {"type": "skill", "name": "skill-real", "description": "Uma skill real", "content": "CONTEUDO IDENTICO"}
    resultado = injector_core.materialize(component, base_dir=str(tmp_path), dry_run=False)

    assert resultado.sucesso is True
    assert len(resultado.valor) == 5

    conteudos = set()
    for d in target_profile.HARNESS_SKILL_DIRS:
        caminho = tmp_path / d.replace("/", os.sep) / "skill-real" / "SKILL.md"
        assert caminho.exists()
        conteudos.add(caminho.read_text(encoding="utf-8"))
    assert conteudos == {"CONTEUDO IDENTICO"}

    registry_path = tmp_path / "COMPONENT-REGISTRY.json"
    assert registry_path.exists()
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    assert len(registry) == 1
    assert registry[0]["name"] == "skill-real"
    assert registry[0]["type"] == "skill"
    assert len(registry[0]["files"]) == 5


def test_materialize_reinjecao_atualiza_entrada_sem_duplicar(tmp_path):
    base = {"type": "rule", "name": "regra-dup", "content": "v1"}
    r1 = injector_core.materialize(base, base_dir=str(tmp_path))
    assert r1.sucesso is True

    base2 = {"type": "rule", "name": "regra-dup", "description": "v2", "content": "v2"}
    r2 = injector_core.materialize(base2, base_dir=str(tmp_path))
    assert r2.sucesso is True

    registry = json.loads((tmp_path / "COMPONENT-REGISTRY.json").read_text(encoding="utf-8"))
    entradas = [r for r in registry if r["name"] == "regra-dup" and r["type"] == "rule"]
    assert len(entradas) == 1
    assert entradas[0]["description"] == "v2"
    assert (tmp_path / "templates" / "rules" / "regra-dup.md").read_text(encoding="utf-8") == "v2"


def test_materialize_mcp_merge_preserva_servidores_existentes(tmp_path):
    mcp_path = tmp_path / "mcp.json"
    mcp_path.write_text(
        json.dumps({"mcpServers": {"servidor-existente": {"command": "node", "args": [], "env": {}}}}),
        encoding="utf-8",
    )

    component = {"type": "mcp", "name": "servidor-novo", "mcp": {"command": "python", "args": ["s.py"], "env": {}}}
    resultado = injector_core.materialize(component, base_dir=str(tmp_path))
    assert resultado.sucesso is True

    dados = json.loads(mcp_path.read_text(encoding="utf-8"))
    assert "servidor-existente" in dados["mcpServers"]
    assert dados["mcpServers"]["servidor-novo"]["command"] == "python"


def test_materialize_config_rejeita_path_traversal_sem_escrever(tmp_path):
    component = {"type": "config", "name": "cfg-malicioso", "files": {"../escapou.txt": "x"}}
    resultado = injector_core.materialize(component, base_dir=str(tmp_path))
    assert resultado.sucesso is False
    assert resultado.codigo == "PATH_TRAVERSAL_REJEITADO"
    assert not (tmp_path.parent / "escapou.txt").exists()


# ---------------------------------------------------------------------------
# materialize — rollback transacional em falha parcial
# ---------------------------------------------------------------------------

def test_materialize_rollback_em_falha_parcial(tmp_path, monkeypatch):
    real_open = builtins.open

    # Um dos 5 alvos já possui conteúdo pré-existente — deve ser restaurado no rollback.
    pre_path = tmp_path / ".claude" / "skills" / "rollback-teste" / "SKILL.md"
    pre_path.parent.mkdir(parents=True)
    pre_path.write_text("CONTEUDO_ANTIGO", encoding="utf-8")

    alvo_falha = os.path.abspath(str(tmp_path / ".gemini" / "skills" / "rollback-teste" / "SKILL.md"))

    def fake_open(file, mode="r", *args, **kwargs):
        if "w" in mode and "b" in mode and os.path.abspath(str(file)) == alvo_falha:
            raise OSError("Falha simulada de escrita em disco")
        return real_open(file, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", fake_open)

    component = {"type": "skill", "name": "rollback-teste", "content": "CONTEUDO_NOVO"}
    resultado = injector_core.materialize(component, base_dir=str(tmp_path), dry_run=False)

    monkeypatch.undo()

    assert resultado.sucesso is False
    assert resultado.codigo == "MATERIALIZE_FALHOU_ROLLBACK_OK"

    # Alvo que já existia antes: restaurado ao conteúdo original (rollback).
    assert pre_path.read_text(encoding="utf-8") == "CONTEUDO_ANTIGO"

    # Alvos novos escritos antes da falha (.agent, .mimocode): removidos no rollback.
    for d in (".agent/skills/rollback-teste/SKILL.md", ".mimocode/skills/rollback-teste/SKILL.md"):
        assert not (tmp_path / d.replace("/", os.sep)).exists()

    # Alvo que falhou e o alvo seguinte (.skills) nunca deveriam ter sido escritos.
    assert not (tmp_path / ".gemini" / "skills" / "rollback-teste" / "SKILL.md").exists()
    assert not (tmp_path / ".skills" / "rollback-teste" / "SKILL.md").exists()

    # Nenhum registry deve ter sido criado por uma injeção que falhou.
    assert not (tmp_path / "COMPONENT-REGISTRY.json").exists()


# ---------------------------------------------------------------------------
# sync_check
# ---------------------------------------------------------------------------

def test_sync_check_ok_quando_tudo_integro(tmp_path):
    component = {"type": "rule", "name": "regra-sync", "content": "corpo"}
    injector_core.materialize(component, base_dir=str(tmp_path))

    resultado = injector_core.sync_check(str(tmp_path))
    assert resultado.sucesso is True


def test_sync_check_detecta_drift(tmp_path):
    component = {"type": "rule", "name": "regra-drift", "content": "corpo"}
    injector_core.materialize(component, base_dir=str(tmp_path))

    (tmp_path / "templates" / "rules" / "regra-drift.md").write_text("EDITADO_MANUALMENTE", encoding="utf-8")

    resultado = injector_core.sync_check(str(tmp_path))
    assert resultado.sucesso is False
    assert resultado.codigo == "SYNC_DIVERGENTE"
    assert any("regra-drift" in p for p in resultado.detalhes["problemas"])


def test_remove_component_apaga_arquivos_e_entrada(tmp_path):
    component = {"type": "rule", "name": "regra-remover", "content": "corpo"}
    injector_core.materialize(component, base_dir=str(tmp_path))

    resultado = injector_core.remove_component("regra-remover", "rule", base_dir=str(tmp_path))
    assert resultado.sucesso is True
    assert not (tmp_path / "templates" / "rules" / "regra-remover.md").exists()

    registry = json.loads((tmp_path / "COMPONENT-REGISTRY.json").read_text(encoding="utf-8"))
    assert not any(r["name"] == "regra-remover" for r in registry)
