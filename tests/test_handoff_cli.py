# -*- coding: utf-8 -*-
import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent

def carregar_cli():
    cli_path = ROOT / "componentes" / "compartilhado" / "skills" / "aidd-handoff" / "scripts" / "cli.py"
    spec = importlib.util.spec_from_file_location("aidd_handoff_cli", str(cli_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_handoff_cli_rejeita_sem_subcomando():
    cli = carregar_cli()
    assert cli.main([]) == 1

def test_handoff_cli_gerar_sucesso(tmp_path):
    cli = carregar_cli()
    output = tmp_path / "docs" / "secoes" / "sessao-teste.md"
    res = cli.main(["gerar", "--output", str(output), "--goal", "Finalizar auditoria"])
    assert res == 0
    assert output.exists()

def test_handoff_cli_validar_sucesso(tmp_path):
    cli = carregar_cli()
    arquivo = tmp_path / "docs" / "secoes" / "sessao-teste.md"
    cli.main(["gerar", "--output", str(arquivo), "--goal", "Meta teste"])
    res = cli.main(["validar", "--arquivo", str(arquivo)])
    assert res == 0

def test_handoff_cli_emitir_sucesso(tmp_path):
    cli = carregar_cli()
    arquivo = tmp_path / "docs" / "secoes" / "sessao-teste.md"
    cli.main(["gerar", "--output", str(arquivo), "--goal", "Meta teste"])
    manifesto = tmp_path / "handoff-sessao.json"
    res = cli.main(["emitir", "--arquivo", str(arquivo), "--output", str(manifesto)])
    assert res == 0
    assert manifesto.exists()
