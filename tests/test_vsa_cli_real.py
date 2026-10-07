# -*- coding: utf-8 -*-
"""
Testes TDD para a CLI de Modularização VSA Real (Ticket 13 / D2).
Verifica inspect, verify e status com dados medidos e integrados aos gates.
"""

import json
import subprocess
import sys
from pathlib import Path
import pytest

from scripts.cli_modularizacao_vsa import main, criar_parser


def test_cli_parser_tem_subcomandos():
    parser = criar_parser()
    # Verifica que inspect, verify, status e index-subgraphs existem
    subparsers_actions = [
        action for action in parser._actions
        if action.dest == "subcomando"
    ]
    assert len(subparsers_actions) == 1
    choices = subparsers_actions[0].choices
    assert "inspect" in choices
    assert "verify" in choices
    assert "status" in choices
    assert "index-subgraphs" in choices


def test_inspect_lista_fatias_e_contagens_medidas(capsys):
    rc = main(["inspect"])
    assert rc == 0
    captured = capsys.readouterr().out
    assert "01-governanca-e-qualidade" in captured
    assert "fluxo-01-pure" in captured
    # Deve conter arquivos, testes ou gates medidos (não apenas texto fixo)
    assert "arquivos:" in captured or "gates:" in captured or "ferramentas:" in captured


def test_status_imprime_dados_medidos(capsys):
    rc = main(["status"])
    assert rc == 0
    captured = capsys.readouterr().out
    # Não pode ser texto fixo antigo '4 macro-módulos canônicos íntegros'
    assert "Status: 4 macro-módulos canônicos íntegros." not in captured
    assert "fatias:" in captured.lower() or "macro-módulos:" in captured.lower() or "status vsa:" in captured.lower()


def test_verify_em_arvore_com_slice_quebrado_falha(tmp_path, monkeypatch):
    """
    Simula uma árvore com slice sem README.md e com referência cruzada.
    Assert verify sai com código diferente de zero.
    """
    raiz_falsa = tmp_path / "repo_falso"
    raiz_falsa.mkdir()

    # Cria estrutura básica de modulos com slice quebrado
    modulos = raiz_falsa / "modulos"
    modulos.mkdir()
    slice_quebrado = modulos / "01-governanca-e-qualidade"
    slice_quebrado.mkdir()
    # Não cria README.md para quebrar fractalidade
    (slice_quebrado / "core").mkdir()
    (slice_quebrado / "skills").mkdir()
    (slice_quebrado / "gates").mkdir()
    (slice_quebrado / "tests").mkdir()

    # Cria arquivo com import cruzado indevido
    py_cruzado = slice_quebrado / "core" / "teste_cruzado.py"
    py_cruzado.write_text("import modulos.fluxo_01_pure\n", encoding="utf-8")

    # Faz o cli rodar apontando para raiz_falsa via argumento ou monkeypatch
    rc = main(["verify", "--raiz", str(raiz_falsa)])
    assert rc != 0
