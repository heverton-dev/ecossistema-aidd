# -*- coding: utf-8 -*-
import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent

def carregar_handoff():
    h_path = ROOT / "componentes" / "compartilhado" / "skills" / "aidd-handoff" / "scripts" / "handoff.py"
    spec = importlib.util.spec_from_file_location("aidd_handoff_signer", str(h_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_emitir_e_verificar_assinatura_hmac(tmp_path):
    h = carregar_handoff()
    arquivo_md = tmp_path / "sessao.md"
    arquivo_md.write_text("conteudo sessao", encoding="utf-8")

    manifesto = h.emitir_manifesto(arquivo_md, secret="chave-secreta")  # pragma: allowlist secret
    assert "assinatura_hmac" in manifesto
    assert h.verificar_manifesto(manifesto, secret="chave-secreta") is True  # pragma: allowlist secret
    assert h.verificar_manifesto(manifesto, secret="chave-errada") is False  # pragma: allowlist secret

def test_verificar_detecta_adulteracao(tmp_path):
    h = carregar_handoff()
    arquivo_md = tmp_path / "sessao.md"
    arquivo_md.write_text("conteudo sessao", encoding="utf-8")

    manifesto = h.emitir_manifesto(arquivo_md, secret="chave-secreta")  # pragma: allowlist secret
    manifesto["arquivo"] = "adulterado.md"
    assert h.verificar_manifesto(manifesto, secret="chave-secreta") is False  # pragma: allowlist secret

