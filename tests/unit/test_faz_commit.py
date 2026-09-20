# -*- coding: utf-8 -*-
"""
Testes unitários para o script determinístico faz-commit.
"""

import sys
import os
import subprocess
from unittest.mock import patch, MagicMock

# Adiciona diretório scripts ao path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT_DIR, "scripts"))

import faz_commit


def test_fallback_mensagem_vazia():
    msg = faz_commit.fallback_mensagem("")
    assert msg == "chore: atualizar alterações no repositório"


def test_fallback_mensagem_arquivo_unico():
    msg = faz_commit.fallback_mensagem("M docs/readme.md")
    assert "readme.md" in msg
    assert msg.startswith("chore:")


def test_fallback_mensagem_multiplos_arquivos():
    msg = faz_commit.fallback_mensagem("M file1.py\nA file2.py")
    assert "file1.py" in msg
    assert "mais 1 arquivo(s)" in msg


def test_obter_diff_resumido_nao_vazio():
    res = faz_commit.obter_diff_resumido()
    assert "STATUS DOS ARQUIVOS:" in res
    assert "ESTATÍSTICAS:" in res
