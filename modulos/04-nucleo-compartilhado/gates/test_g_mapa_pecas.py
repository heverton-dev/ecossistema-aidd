# -*- coding: utf-8 -*-
"""
Testes automatizados do Quality Gate G_mapa_pecas (Lei #8 e Lei #13 - Portão Deve Provar que Morde).
Comprova que o portão aprova em conformidade (exit 0) e reprova estritamente sob mutações
sintéticas e violações deliberadas (exit 1).
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = next((p.parent for p in Path(__file__).resolve().parents if p.name == "modulos"), Path(__file__).resolve().parent.parent)  # raiz: pai de modulos/ (VSA) ou de gates/ (árvore sintética)
GATE_SCRIPT = RAIZ / "modulos" / "04-nucleo-compartilhado" / "gates" / "G_mapa_pecas.py"


def test_mapa_pecas_conformidade_real():
    """Valida o estado real do repositório: deve passar com exit 0."""
    res = subprocess.run(
        [sys.executable, str(GATE_SCRIPT)],
        cwd=str(RAIZ),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert res.returncode == 0
    assert "Quality Gate G_mapa_pecas APROVADO (100% OK)!" in res.stdout


def test_morde_catalogo_ausente(tmp_path):
    """Lei #13: Prova que morde com exit 1 quando o catálogo não existe."""
    fake_cat = tmp_path / "catalogo_fantasma.json"
    res = subprocess.run(
        [sys.executable, str(GATE_SCRIPT), "--catalogo", str(fake_cat)],
        cwd=str(RAIZ),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert res.returncode == 1
    assert "Catálogo de peças não encontrado" in res.stdout


def test_morde_catalogo_corrompido(tmp_path):
    """Lei #13: Prova que morde com exit 1 quando o catálogo tem JSON corrompido."""
    bad_cat = tmp_path / "catalogo_corrompido.json"
    bad_cat.write_text("{ versao: incorreta, json invalido", encoding="utf-8")
    res = subprocess.run(
        [sys.executable, str(GATE_SCRIPT), "--catalogo", str(bad_cat)],
        cwd=str(RAIZ),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert res.returncode == 1
    assert "Erro ao decodificar JSON do catálogo" in res.stdout


def test_morde_catalogo_chave_ausente(tmp_path):
    """Lei #13: Prova que morde com exit 1 quando chaves essenciais faltam."""
    cat_incompleto = tmp_path / "catalogo_incompleto.json"
    cat_incompleto.write_text(json.dumps({"versao": "1.0.0"}), encoding="utf-8")
    res = subprocess.run(
        [sys.executable, str(GATE_SCRIPT), "--catalogo", str(cat_incompleto)],
        cwd=str(RAIZ),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert res.returncode == 1
    assert "Catálogo incompleto" in res.stdout


def test_morde_encaixes_quebrados(tmp_path):
    """Lei #13: Prova que morde com exit 1 quando encaixes quebrados > 0."""
    cat = tmp_path / "catalogo_quebrado.json"
    dados = {
        "versao": "1.0.0",
        "gerado_por": "teste",
        "totais": {
            "ferramentas": 1,
            "skills": 1,
            "leis": 1,
            "encaixes_quebrados": 3,
        },
        "ferramentas": [],
        "skills": [],
        "leis": [],
        "encaixes": [],
    }
    cat.write_text(json.dumps(dados), encoding="utf-8")
    res = subprocess.run(
        [sys.executable, str(GATE_SCRIPT), "--catalogo", str(cat)],
        cwd=str(RAIZ),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert res.returncode == 1
    assert "encaixes quebrados no ecossistema" in res.stdout


def test_morde_achado_critico_aberto(tmp_path):
    """Lei #13: Prova que morde com exit 1 quando existe achado crítico/alto aberto."""
    achados_file = tmp_path / "achados_violados.json"
    dados = {
        "achados": [
            {
                "id": "VER-TEST-999",
                "titulo": "Bug crítico simulado",
                "gravidade": "alta",
                "estado": "aberto",
            }
        ]
    }
    achados_file.write_text(json.dumps(dados), encoding="utf-8")
    res = subprocess.run(
        [sys.executable, str(GATE_SCRIPT), "--achados", str(achados_file)],
        cwd=str(RAIZ),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert res.returncode == 1
    assert "Achado crítico/alto não resolvido: [VER-TEST-999]" in res.stdout


def test_morde_mapa_visual_ausente(tmp_path):
    """Lei #13: Prova que morde com exit 1 quando falta um mapa visual obrigatório."""
    fake_mapas = tmp_path / "mapas_incompletos"
    fake_mapas.mkdir()
    # Cria apenas 1 dos 14 arquivos obrigatórios
    (fake_mapas / "mapa-00-indice.html").write_text("<!DOCTYPE html><html><body>ok</body></html>", encoding="utf-8")

    res = subprocess.run(
        [sys.executable, str(GATE_SCRIPT), "--mapas-dir", str(fake_mapas)],
        cwd=str(RAIZ),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert res.returncode == 1
    assert "Mapa visual obrigatório ausente" in res.stdout
