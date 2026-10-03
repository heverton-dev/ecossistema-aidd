# -*- coding: utf-8 -*-
"""
Testes determinísticos do Gestor de Dependências (scripts/gestor_dependencias.py).
Garante que .gitignore e o manifesto são gravados só com LF, inclusive no Windows
(o gate_final reprova CRLF).
"""

from scripts import gestor_dependencias as gd


def test_gitignore_recebe_padroes_sem_crlf(tmp_path, monkeypatch):
    gitignore = tmp_path / ".gitignore"
    gitignore.write_bytes(b"node_modules/\n")
    monkeypatch.setattr(gd, "GITIGNORE_PATH", str(gitignore))

    novos = gd._adicionar_padroes_gitignore(["*/skills/x/", "*/skills/y/"])

    assert novos == ["*/skills/x/", "*/skills/y/"]
    conteudo = gitignore.read_bytes()
    assert b"\r" not in conteudo
    assert conteudo.endswith(b"*/skills/y/\n")


def test_manifesto_salvo_sem_crlf(tmp_path, monkeypatch):
    manifesto = tmp_path / "dependencias_externas.json"
    monkeypatch.setattr(gd, "MANIFESTO_PATH", str(manifesto))

    gd._salvar_manifesto({"skills": {"x": {"pacote": "p"}}, "mcps": {}})

    assert b"\r" not in manifesto.read_bytes()
