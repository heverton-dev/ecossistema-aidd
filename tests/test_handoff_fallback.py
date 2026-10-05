# -*- coding: utf-8 -*-
import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent

def carregar_fallback():
    fb_path = ROOT / "componentes" / "compartilhado" / "skills" / "aidd-handoff" / "scripts" / "fallback.py"
    spec = importlib.util.spec_from_file_location("aidd_handoff_fallback", str(fb_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_resolver_colisao_nome_anexa_sufixo(tmp_path):
    fb = carregar_fallback()
    original = tmp_path / "sessao-2026-10-04-teste.md"
    original.write_text("conteudo 1", encoding="utf-8")

    novo = fb.resolver_colisao_nome(original)
    assert novo.name == "sessao-2026-10-04-teste-2.md"
    assert not novo.exists()

def test_extrair_fatos_git_fallback():
    fb = carregar_fallback()
    fatos = fb.extrair_fatos_git_fallback(repo_root=ROOT, base="HEAD~1")
    assert isinstance(fatos, dict)
    assert "arquivos_modificados" in fatos
    assert "commits" in fatos
