# -*- coding: utf-8 -*-
"""
Testes automatizados para G_ZERO_EMOJIS_DOCS.
Garante cumprimento da Lei #13 (Todo Portão Deve Provar que Morde).
"""

import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
GATE_SCRIPT = ROOT_DIR / "modulos" / "01-governanca-e-qualidade" / "gates" / "G_ZERO_EMOJIS_DOCS.py"


def test_g_zero_emojis_docs_reprova_sob_violacao_morde(tmp_path):
    """Lei #13: Prova que o portão morde e retorna exit 1 quando há emojis em Markdown."""
    pasta_teste = tmp_path / "projeto_com_emojis"
    pasta_teste.mkdir()
    
    # Cria README com emoji
    readme = pasta_teste / "README.md"
    readme.write_text("# Projeto Teste 🚀\nEste texto tem emoji 💡.", encoding="utf-8")

    cmd = [sys.executable, str(GATE_SCRIPT), "--alvo", str(pasta_teste)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 1, f"O portão deveria ter falhado (exit 1), mas retornou {res.returncode}"
    assert "FALHA" in res.stderr
    assert "emoji proibido" in res.stderr


def test_g_zero_emojis_docs_aprova_quando_limpo(tmp_path):
    """Verifica se o portão passa com exit 0 quando os arquivos estão limpos."""
    pasta_teste = tmp_path / "projeto_limpo"
    pasta_teste.mkdir()

    readme = pasta_teste / "README.md"
    readme.write_text("# Projeto Corporativo\nDocumentacao institucional sem emojis.", encoding="utf-8")

    docs = pasta_teste / "docs"
    docs.mkdir()
    manual = docs / "manual.md"
    manual.write_text("## Arquitetura\nTexto puramente tecnico e corporativo.", encoding="utf-8")

    cmd = [sys.executable, str(GATE_SCRIPT), "--alvo", str(pasta_teste)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"O portão deveria passar (exit 0), mas falhou: {res.stderr}"
    assert "PASS" in res.stdout
