# -*- coding: utf-8 -*-
"""
Testes determinísticos do Gestor de Sessões (scripts/gestor_sessoes.py).
Cobre registro, idempotência, listagem, busca e espelho Markdown.
"""

import json
import pytest
from pathlib import Path
from scripts.gestor_sessoes import (
    registrar_sessao,
    listar_sessoes,
    buscar_sessao,
    carregar_historico
)


def test_registrar_e_listar_sessao(tmp_path):
    json_path = str(tmp_path / "historico.json")
    md_path = str(tmp_path / "INDICE.md")

    # Registro de sessão 1
    reg1 = registrar_sessao(
        session_id="uuid-1111",
        harness="antigravity",
        modelo="gemini-3.8-flash",
        titulo="Teste Sessão 1",
        caminho_json=json_path,
        gerar_md=True,
        caminho_md=md_path
    )
    assert reg1["id"] == "uuid-1111"
    assert reg1["harness"] == "antigravity"

    # Verificação de persistência
    sessoes = listar_sessoes(json_path)
    assert len(sessoes) == 1
    assert sessoes[0]["id"] == "uuid-1111"

    # Verificação do Markdown gerado
    assert Path(md_path).exists()
    conteudo_md = Path(md_path).read_text(encoding="utf-8")
    assert "uuid-1111" in conteudo_md
    assert "Teste Sessão 1" in conteudo_md


def test_idempotencia_ao_atualizar_mesmo_id(tmp_path):
    json_path = str(tmp_path / "historico.json")

    registrar_sessao(
        session_id="uuid-2222",
        titulo="Título Antigo",
        caminho_json=json_path,
        gerar_md=False
    )
    # Atualizar mesmo ID
    registrar_sessao(
        session_id="uuid-2222",
        titulo="Título Atualizado",
        caminho_json=json_path,
        gerar_md=False
    )

    sessoes = listar_sessoes(json_path)
    assert len(sessoes) == 1
    assert sessoes[0]["titulo"] == "Título Atualizado"


def test_busca_sessao(tmp_path):
    json_path = str(tmp_path / "historico.json")

    registrar_sessao(session_id="alpha-1", harness="claude", titulo="Refatoração API", caminho_json=json_path, gerar_md=False)
    registrar_sessao(session_id="beta-2", harness="antigravity", titulo="Criação de MCP", caminho_json=json_path, gerar_md=False)

    # Busca por ID
    res = buscar_sessao("alpha", json_path)
    assert len(res) == 1
    assert res[0]["id"] == "alpha-1"

    # Busca por Título
    res_mcp = buscar_sessao("mcp", json_path)
    assert len(res_mcp) == 1
    assert res_mcp[0]["id"] == "beta-2"


def test_rejeita_id_vazio(tmp_path):
    json_path = str(tmp_path / "historico.json")
    with pytest.raises(ValueError, match="obrigatório"):
        registrar_sessao(session_id="   ", caminho_json=json_path, gerar_md=False)
