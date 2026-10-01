#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes: Sincronizador de Harness (anchors globais) do Injetor Universal.
"""

import json

import pytest

from scripts.core.injector.sincronizador_harness import sincronizar

AGENTS_MD_FIXTURE = """# AGENTS

## 📦 Registro de Componentes Injetados

| Tipo | Nome | Destino | Data | Descrição |
| :--- | :--- | :--- | :--- | :--- |
<!-- INJECTOR:TABELA:INICIO -->
<!-- INJECTOR:TABELA:FIM -->

## Próximas Referências
"""


@pytest.fixture
def repo_fixture(tmp_path):
    (tmp_path / "AGENTS.md").write_text(AGENTS_MD_FIXTURE, encoding="utf-8")
    (tmp_path / "HARNESS-COMPAT.json").write_text(json.dumps({
        "metadata": {"ultima_atualizacao": "2026-01-01T00:00:00+00:00"},
        "harness_compatibility": {},
    }), encoding="utf-8")
    (tmp_path / "PLANO-EXECUCAO-ESTRUTURADO.json").write_text(json.dumps({
        "etapas": [{"id": "fase-existente", "status": "✅ COMPLETO"}],
        "proxima_acao": {"recomendacao": "nao mexer"},
    }), encoding="utf-8")
    return tmp_path


class TestSincronizarAgentsMd:
    def test_insere_linha_na_tabela(self, repo_fixture):
        resultado = sincronizar(repo_fixture, "skill", "minha-skill", "descricao da skill", "skills/minha-skill/SKILL.md", ["AGENTS.md"])
        assert "AGENTS.md" in resultado.anchors_atualizados

        texto = (repo_fixture / "AGENTS.md").read_text(encoding="utf-8")
        assert "| skill | `minha-skill` | `skills/minha-skill/SKILL.md` |" in texto
        assert "descricao da skill" in texto

    def test_nao_duplica_marcadores(self, repo_fixture):
        sincronizar(repo_fixture, "skill", "a", "descricao a", "skills/a/SKILL.md", ["AGENTS.md"])
        sincronizar(repo_fixture, "skill", "b", "descricao b", "skills/b/SKILL.md", ["AGENTS.md"])

        texto = (repo_fixture / "AGENTS.md").read_text(encoding="utf-8")
        assert texto.count("<!-- INJECTOR:TABELA:INICIO -->") == 1
        assert texto.count("<!-- INJECTOR:TABELA:FIM -->") == 1
        assert "minha-skill" not in texto  # sanity: nome do outro teste nao vaza
        assert "`a`" in texto and "`b`" in texto

    def test_ausencia_de_agents_md_nao_quebra(self, tmp_path):
        resultado = sincronizar(tmp_path, "skill", "x", "descricao", "skills/x/SKILL.md", ["AGENTS.md"])
        assert resultado.anchors_atualizados == []

    def test_agents_md_sem_marcadores_nao_e_reportado_como_atualizado(self, tmp_path):
        (tmp_path / "AGENTS.md").write_text("# AGENTS sem secao de injetor\n", encoding="utf-8")
        resultado = sincronizar(tmp_path, "skill", "x", "descricao", "skills/x/SKILL.md", ["AGENTS.md"])
        assert resultado.anchors_atualizados == []


class TestSincronizarHarnessCompat:
    def test_registra_componente_injetado(self, repo_fixture):
        resultado = sincronizar(repo_fixture, "mcp", "meu-mcp", "descricao do mcp", "mcps/meu-mcp/server.py", ["HARNESS-COMPAT.json"])
        assert "HARNESS-COMPAT.json" in resultado.anchors_atualizados

        dados = json.loads((repo_fixture / "HARNESS-COMPAT.json").read_text(encoding="utf-8"))
        assert len(dados["componentes_injetados"]) == 1
        assert dados["componentes_injetados"][0]["nome"] == "meu-mcp"
        assert dados["componentes_injetados"][0]["tipo"] == "mcp"

    def test_preserva_estrutura_existente(self, repo_fixture):
        sincronizar(repo_fixture, "mcp", "x", "descricao", "mcps/x/server.py", ["HARNESS-COMPAT.json"])
        dados = json.loads((repo_fixture / "HARNESS-COMPAT.json").read_text(encoding="utf-8"))
        assert "harness_compatibility" in dados  # nao removido

    def test_ausencia_de_arquivo_nao_e_reportada_como_atualizada(self, tmp_path):
        resultado = sincronizar(tmp_path, "mcp", "x", "descricao", "mcps/x/server.py", ["HARNESS-COMPAT.json"])
        assert resultado.anchors_atualizados == []


class TestSincronizarPlanoExecucao:
    def test_acrescenta_etapa_sem_remover_existentes(self, repo_fixture):
        resultado = sincronizar(repo_fixture, "spec", "minha-spec", "descricao da spec", "docs/specs/minha-spec.md", ["PLANO-EXECUCAO-ESTRUTURADO.json"])
        assert "PLANO-EXECUCAO-ESTRUTURADO.json" in resultado.anchors_atualizados

        dados = json.loads((repo_fixture / "PLANO-EXECUCAO-ESTRUTURADO.json").read_text(encoding="utf-8"))
        ids = [e["id"] for e in dados["etapas"]]
        assert "fase-existente" in ids
        assert "injecao-spec-minha-spec" in ids

    def test_nao_mexe_em_proxima_acao(self, repo_fixture):
        sincronizar(repo_fixture, "spec", "x", "descricao", "docs/specs/x.md", ["PLANO-EXECUCAO-ESTRUTURADO.json"])
        dados = json.loads((repo_fixture / "PLANO-EXECUCAO-ESTRUTURADO.json").read_text(encoding="utf-8"))
        assert dados["proxima_acao"] == {"recomendacao": "nao mexer"}

    def test_idempotente_nao_duplica_mesma_spec(self, repo_fixture):
        sincronizar(repo_fixture, "spec", "dup", "descricao", "docs/specs/dup.md", ["PLANO-EXECUCAO-ESTRUTURADO.json"])
        sincronizar(repo_fixture, "spec", "dup", "descricao", "docs/specs/dup.md", ["PLANO-EXECUCAO-ESTRUTURADO.json"])

        dados = json.loads((repo_fixture / "PLANO-EXECUCAO-ESTRUTURADO.json").read_text(encoding="utf-8"))
        ids = [e["id"] for e in dados["etapas"] if e["id"] == "injecao-spec-dup"]
        assert len(ids) == 1

    def test_ausencia_de_arquivo_nao_e_reportada_como_atualizada(self, tmp_path):
        resultado = sincronizar(tmp_path, "spec", "x", "descricao", "docs/specs/x.md", ["PLANO-EXECUCAO-ESTRUTURADO.json"])
        assert resultado.anchors_atualizados == []
