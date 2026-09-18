# -*- coding: utf-8 -*-
"""
Testes unitários para o Quality Gate G_ISOLATION_AUDIT.
Garante detecção determinística de imports cruzados proibidos e aprovação de cenários limpos.
"""

import os
import sys
import tempfile
import pytest

from gates.G_ISOLATION_AUDIT import (
    extrair_modulo_e_fatia,
    analisar_imports_arquivo,
    scan_isolation_violations,
)


def test_extrair_modulo_e_fatia():
    caminho = "C:/projeto/src/features/encomendas/service.py"
    res = extrair_modulo_e_fatia(caminho)
    assert res is not None
    _, fatia = res
    assert fatia == "encomendas"

    caminho_core = "C:/projeto/src/core/database.py"
    assert extrair_modulo_e_fatia(caminho_core) is None


def test_analisar_imports_arquivo_sem_violacao(tmp_path):
    arquivo = tmp_path / "valid_slice.py"
    arquivo.write_text(
        "import os\n"
        "from src.core.database import get_db\n"
        "from src.features.encomendas.models import Encomenda\n"
        "from .repository import buscar\n",
        encoding="utf-8"
    )
    violacoes = analisar_imports_arquivo(str(arquivo), "encomendas")
    assert len(violacoes) == 0


def test_analisar_imports_arquivo_com_violacao_from(tmp_path):
    arquivo = tmp_path / "invalid_slice.py"
    arquivo.write_text(
        "from src.features.frotas.services import despachar_veiculo\n",
        encoding="utf-8"
    )
    violacoes = analisar_imports_arquivo(str(arquivo), "encomendas")
    assert len(violacoes) == 1
    linha, fatia_alvo, trecho = violacoes[0]
    assert linha == 1
    assert fatia_alvo == "frotas"
    assert "src.features.frotas" in trecho


def test_analisar_imports_arquivo_com_violacao_import_direto(tmp_path):
    arquivo = tmp_path / "invalid_slice_direct.py"
    arquivo.write_text(
        "import src.features.cobranca\n",
        encoding="utf-8"
    )
    violacoes = analisar_imports_arquivo(str(arquivo), "encomendas")
    assert len(violacoes) == 1
    _, fatia_alvo, _ = violacoes[0]
    assert fatia_alvo == "cobranca"


def test_scan_isolation_violations_end_to_end(tmp_path):
    features_dir = tmp_path / "src" / "features"
    slice_a = features_dir / "slice_a"
    slice_b = features_dir / "slice_b"
    slice_a.mkdir(parents=True)
    slice_b.mkdir(parents=True)

    (slice_a / "clean.py").write_text("from src.core import logs\n", encoding="utf-8")
    (slice_b / "dirty.py").write_text("from src.features.slice_a import algo\n", encoding="utf-8")

    violacoes = scan_isolation_violations(str(tmp_path))
    assert len(violacoes) == 1
    assert violacoes[0]["fatia_origem"] == "slice_b"
    assert violacoes[0]["fatia_alvo"] == "slice_a"
