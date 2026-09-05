# -*- coding: utf-8 -*-
"""
Teste do Gate G_DRIFT_NUCLEO_COMPARTILHADO contra o blind spot
de arquivos que desaparecem de um dos lados (com esperado_identico==True),
e deteccao de divergencia de conteudo sem regressao.
"""

import json
import importlib.util
import os
import sys
import pytest

DOS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
GATE_PATH = os.path.join(DOS_ROOT, "gates", "G_DRIFT_NUCLEO_COMPARTILHADO.py")


@pytest.fixture
def gate_module():
    spec = importlib.util.spec_from_file_location("G_DRIFT_NUCLEO_COMPARTILHADO", GATE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_gate_falha_quando_arquivo_identico_desaparece_de_dir_a(tmp_path, monkeypatch, gate_module, capsys):
    dir_a = tmp_path / "dir_a"
    dir_b = tmp_path / "dir_b"
    dir_a.mkdir()
    dir_b.mkdir()

    (dir_b / "single.py").write_text("#_identico", encoding="utf-8")
    baseline_file = tmp_path / "baseline.json"
    baseline_file.write_text(
        json.dumps({
            "arquivos": {
                "single.py": {"esperado_identico": True, "motivo": None}
            }
        }),
        encoding="utf-8",
    )

    monkeypatch.setattr(gate_module, "DIR_A", str(dir_a))
    monkeypatch.setattr(gate_module, "DIR_B", str(dir_b))
    monkeypatch.setattr(gate_module, "BASELINE_PATH", str(baseline_file))

    code = gate_module.checar_drift()
    out, _ = capsys.readouterr()

    assert code == 1, "Precisa falhar quando o arquivo desaparece de DIR_A"
    assert "single.py" in out
    assert "desapareceu de DIR_A" in out


def test_gate_falha_quando_arquivo_identico_desaparece_de_dir_b(tmp_path, monkeypatch, gate_module, capsys):
    dir_a = tmp_path / "dir_a"
    dir_b = tmp_path / "dir_b"
    dir_a.mkdir()
    dir_b.mkdir()

    (dir_a / "single.py").write_text("#_identico", encoding="utf-8")
    baseline_file = tmp_path / "baseline.json"
    baseline_file.write_text(
        json.dumps({
            "arquivos": {
                "single.py": {"esperado_identico": True, "motivo": None}
            }
        }),
        encoding="utf-8",
    )

    monkeypatch.setattr(gate_module, "DIR_A", str(dir_a))
    monkeypatch.setattr(gate_module, "DIR_B", str(dir_b))
    monkeypatch.setattr(gate_module, "BASELINE_PATH", str(baseline_file))

    code = gate_module.checar_drift()
    out, _ = capsys.readouterr()

    assert code == 1, "Precisa falhar quando o arquivo desaparece de DIR_B"
    assert "single.py" in out
    assert "desapareceu de DIR_B" in out


def test_gate_sucesso_quando_identicos(tmp_path, monkeypatch, gate_module, capsys):
    dir_a = tmp_path / "dir_a"
    dir_b = tmp_path / "dir_b"
    dir_a.mkdir()
    dir_b.mkdir()

    (dir_a / "ok.py").write_text("conteudo_identico", encoding="utf-8")
    (dir_b / "ok.py").write_text("conteudo_identico", encoding="utf-8")
    baseline_file = tmp_path / "baseline.json"
    baseline_file.write_text(
        json.dumps({
            "arquivos": {
                "ok.py": {"esperado_identico": True, "motivo": None}
            }
        }),
        encoding="utf-8",
    )

    monkeypatch.setattr(gate_module, "DIR_A", str(dir_a))
    monkeypatch.setattr(gate_module, "DIR_B", str(dir_b))
    monkeypatch.setattr(gate_module, "BASELINE_PATH", str(baseline_file))

    code = gate_module.checar_drift()
    assert code == 0


def test_gate_falha_quando_conteudo_diverge(tmp_path, monkeypatch, gate_module, capsys):
    dir_a = tmp_path / "dir_a"
    dir_b = tmp_path / "dir_b"
    dir_a.mkdir()
    dir_b.mkdir()

    (dir_a / "div.py").write_text("conteudo_a", encoding="utf-8")
    (dir_b / "div.py").write_text("conteudo_b", encoding="utf-8")
    baseline_file = tmp_path / "baseline.json"
    baseline_file.write_text(
        json.dumps({
            "arquivos": {
                "div.py": {"esperado_identico": True, "motivo": None}
            }
        }),
        encoding="utf-8",
    )

    monkeypatch.setattr(gate_module, "DIR_A", str(dir_a))
    monkeypatch.setattr(gate_module, "DIR_B", str(dir_b))
    monkeypatch.setattr(gate_module, "BASELINE_PATH", str(baseline_file))

    code = gate_module.checar_drift()
    out, _ = capsys.readouterr()

    assert code == 1
    assert "conteudo diverge agora" in out
