import pytest
from pathlib import Path


def _fatia_minima(raiz: Path) -> Path:
    fatia = raiz / "minha_fatia"
    (fatia / "tests").mkdir(parents=True)
    (fatia / "AGENTS.md").write_text("# Regras da fatia\nInvariantes curtas.", encoding="utf-8")
    (fatia / "README.md").write_text("# Minha Fatia\nDocumentação curta e objetiva.", encoding="utf-8")
    return fatia


def test_validador_fractalidade_aprova_fatia_completa(tmp_path):
    from scripts.validador_fractalidade_vsa import validar_fractalidade_slice

    fatia = _fatia_minima(tmp_path)
    (fatia / "core").mkdir()
    (fatia / "skills").mkdir()
    (fatia / "gates").mkdir()

    valido, erros = validar_fractalidade_slice(fatia)
    assert valido is True
    assert erros == []


def test_validador_fractalidade_rejeita_elementos_ausentes(tmp_path):
    from scripts.validador_fractalidade_vsa import validar_fractalidade_slice

    fatia = tmp_path / "fatia_incompleta"
    fatia.mkdir()
    (fatia / "core").mkdir()

    valido, erros = validar_fractalidade_slice(fatia)
    assert valido is False
    assert any("AGENTS.md" in e for e in erros)
    assert any("README.md" in e for e in erros)
    assert any("tests" in e for e in erros)
    # core/skills/gates são opcionais (decisão do usuário 08/10): nunca cobrados
    assert not any("skills" in e or "gates" in e for e in erros)


def test_validador_fractalidade_rejeita_readme_acima_limite_tokens(tmp_path):
    from scripts.validador_fractalidade_vsa import validar_fractalidade_slice

    fatia = _fatia_minima(tmp_path)
    texto_longo = "palavra " * 600
    (fatia / "README.md").write_text(texto_longo, encoding="utf-8")

    valido, erros = validar_fractalidade_slice(fatia)
    assert valido is False
    assert any("orçamento de tokens" in e.lower() for e in erros)
