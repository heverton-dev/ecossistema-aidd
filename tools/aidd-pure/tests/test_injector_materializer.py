#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes: Materializador (escrita transacional com rollback) do Injetor Universal.
"""

import os
from pathlib import Path
from unittest import mock

from scripts.core.injector.materializador import materializar


class TestMaterializacaoComSucesso:
    def test_publica_todos_os_arquivos(self, tmp_path):
        resultado = materializar(tmp_path, {
            "skills/x/SKILL.md": "# X\n",
            ".claude/skills/x/SKILL.md": "# X\n",
        })
        assert resultado.sucesso is True
        assert set(resultado.arquivos_publicados) == {"skills/x/SKILL.md", ".claude/skills/x/SKILL.md"}
        assert (tmp_path / "skills/x/SKILL.md").read_text(encoding="utf-8") == "# X\n"
        assert (tmp_path / ".claude/skills/x/SKILL.md").read_text(encoding="utf-8") == "# X\n"

    def test_nao_deixa_staging_orfao(self, tmp_path):
        materializar(tmp_path, {"rules/r.md": "conteudo"})
        staging_dir = tmp_path / ".aidd" / "cache" / "_injector_staging"
        if staging_dir.exists():
            assert list(staging_dir.iterdir()) == []

    def test_cria_diretorios_pais_automaticamente(self, tmp_path):
        resultado = materializar(tmp_path, {"a/b/c/d.md": "conteudo"})
        assert resultado.sucesso is True
        assert (tmp_path / "a" / "b" / "c" / "d.md").exists()


class TestProtecaoContraSobrescrita:
    def test_recusa_sobrescrever_destino_existente_sem_force(self, tmp_path):
        (tmp_path / "config").mkdir()
        (tmp_path / "config" / "x.json").write_text("{}", encoding="utf-8")

        resultado = materializar(tmp_path, {"config/x.json": '{"novo": true}'})
        assert resultado.sucesso is False
        assert "ja existe" in resultado.erro or "já existe" in resultado.erro
        # conteudo original preservado
        assert (tmp_path / "config" / "x.json").read_text(encoding="utf-8") == "{}"

    def test_force_permite_sobrescrever(self, tmp_path):
        (tmp_path / "config").mkdir()
        (tmp_path / "config" / "x.json").write_text("{}", encoding="utf-8")

        resultado = materializar(tmp_path, {"config/x.json": '{"novo": true}'}, force=True)
        assert resultado.sucesso is True
        assert (tmp_path / "config" / "x.json").read_text(encoding="utf-8") == '{"novo": true}'


class TestRollback:
    def test_falha_no_meio_da_publicacao_remove_tudo_que_foi_publicado(self, tmp_path):
        arquivos = {
            "skills/a/SKILL.md": "# A\n",
            "skills/a/EXTRA.md": "# B\n",
            "skills/a/MAIS.md": "# C\n",
        }

        chamadas = {"n": 0}
        original_replace = os.replace

        def replace_com_falha_na_segunda(src, dst):
            chamadas["n"] += 1
            if chamadas["n"] == 2:
                raise OSError("falha de I/O simulada")
            return original_replace(src, dst)

        with mock.patch("scripts.core.injector.materializador.os.replace", side_effect=replace_com_falha_na_segunda):
            resultado = materializar(tmp_path, arquivos)

        assert resultado.sucesso is False
        assert resultado.arquivos_publicados == []

        arquivos_no_disco = [p for p in tmp_path.rglob("*") if p.is_file()]
        assert arquivos_no_disco == []

    def test_rollback_remove_diretorios_vazios_criados(self, tmp_path):
        chamadas = {"n": 0}
        original_replace = os.replace

        def replace_com_falha_na_segunda(src, dst):
            chamadas["n"] += 1
            if chamadas["n"] == 2:
                raise OSError("falha simulada")
            return original_replace(src, dst)

        with mock.patch("scripts.core.injector.materializador.os.replace", side_effect=replace_com_falha_na_segunda):
            materializar(tmp_path, {
                "mcps/x/server.py": "# a",
                "mcps/x/extra.py": "# b",
            })

        assert not (tmp_path / "mcps").exists()

    def test_rollback_nao_toca_em_arquivos_pre_existentes(self, tmp_path):
        (tmp_path / "rules").mkdir()
        (tmp_path / "rules" / "existente.md").write_text("nao mexer", encoding="utf-8")

        chamadas = {"n": 0}
        original_replace = os.replace

        def replace_com_falha_na_primeira(src, dst):
            chamadas["n"] += 1
            if chamadas["n"] == 1:
                raise OSError("falha simulada")
            return original_replace(src, dst)

        with mock.patch("scripts.core.injector.materializador.os.replace", side_effect=replace_com_falha_na_primeira):
            materializar(tmp_path, {"rules/nova.md": "novo"}, force=True)

        assert (tmp_path / "rules" / "existente.md").read_text(encoding="utf-8") == "nao mexer"
