# -*- coding: utf-8 -*-
"""
Testes unitários para G_DRIFT_ANALYZER
"""

import os
import shutil
import tempfile
import pytest

from gates.G_DRIFT_ANALYZER import analyze_slice_drift


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
