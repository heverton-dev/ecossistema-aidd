# -*- coding: utf-8 -*-
"""
Testes unitários para G_DRIFT_ANALYZER
"""

import os
import shutil
import subprocess
import sys
import tempfile
import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from gates.G_DRIFT_ANALYZER import analyze_slice_drift, main



@pytest.fixture
def temp_project(tmp_path):
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return project_dir


def test_no_features_directory_returns_empty(temp_project):
    res = analyze_slice_drift(str(temp_project))
    assert res == []


def test_unique_functions_returns_no_drift(temp_project):
    features = temp_project / "src" / "features"
    slice1 = features / "auth"
    slice2 = features / "billing"
    slice1.mkdir(parents=True)
    slice2.mkdir(parents=True)

    (slice1 / "handler.py").write_text(
        "def login_user(email: str):\n    res = email.lower().strip()\n    return res\n",
        encoding="utf-8"
    )
    (slice2 / "processor.py").write_text(
        "def process_payment(amount: float):\n    total = amount * 1.1\n    return total\n",
        encoding="utf-8"
    )

    duplicates = analyze_slice_drift(str(temp_project))
    assert duplicates == []


def test_duplicate_function_across_slices_is_detected(temp_project):
    features = temp_project / "src" / "features"
    slice1 = features / "auth"
    slice2 = features / "billing"
    slice1.mkdir(parents=True)
    slice2.mkdir(parents=True)

    code_duplicate = (
        "def sanitize_string(val: str) -> str:\n"
        "    clean = val.strip().lower()\n"
        "    return clean\n"
    )

    (slice1 / "utils.py").write_text(code_duplicate, encoding="utf-8")
    (slice2 / "helpers.py").write_text(code_duplicate, encoding="utf-8")

    duplicates = analyze_slice_drift(str(temp_project))
    assert len(duplicates) == 1
    assert duplicates[0]["function"] == "sanitize_string"
    assert {duplicates[0]["slice_a"], duplicates[0]["slice_b"]} == {"auth", "billing"}


def test_same_slice_function_duplicate_is_not_cross_slice(temp_project):
    features = temp_project / "src" / "features"
    slice1 = features / "auth"
    slice1.mkdir(parents=True)

    code_duplicate = (
        "def normalize_name(name: str) -> str:\n"
        "    val = name.strip()\n"
        "    return val\n"
    )

    (slice1 / "file1.py").write_text(code_duplicate, encoding="utf-8")
    (slice1 / "file2.py").write_text(code_duplicate, encoding="utf-8")

    duplicates = analyze_slice_drift(str(temp_project))
    # Duplicação interna na mesma fatia não é drift inter-fatias
    assert duplicates == []


def test_gate_reprova_com_drift_duplicado_em_modo_estrito(temp_project):
    """Lei #13: Prova que o gate morde (exit 1) quando há drift e invocado em modo --strict."""
    features = temp_project / "src" / "features"
    slice1 = features / "auth"
    slice2 = features / "billing"
    slice1.mkdir(parents=True)
    slice2.mkdir(parents=True)

    code_duplicate = (
        "def sanitize_string(val: str) -> str:\n"
        "    clean = val.strip().lower()\n"
        "    return clean\n"
    )

    (slice1 / "utils.py").write_text(code_duplicate, encoding="utf-8")
    (slice2 / "helpers.py").write_text(code_duplicate, encoding="utf-8")

    gate_script = os.path.join(ROOT_DIR, "gates", "G_DRIFT_ANALYZER.py")
    cmd = [sys.executable, gate_script, "--target", str(temp_project), "--strict"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 1
    assert "Detectadas 1 duplicidade(s) estrutural(is) inter-fatias" in res.stdout

