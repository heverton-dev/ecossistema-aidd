# -*- coding: utf-8 -*-
"""
Testes unitários para G_PROTOTYPE_REWRITE
"""

import os
import pytest
from gates.G_PROTOTYPE_REWRITE import (
    verificar_imports_sandbox,
    verificar_promocao_sem_testes,
)


def test_no_src_dir_returns_no_violations(tmp_path):
    assert verificar_imports_sandbox(str(tmp_path)) == []
    assert verificar_promocao_sem_testes(str(tmp_path)) == []


def test_valid_src_without_sandbox_imports(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "service.py").write_text("import os\nfrom math import sqrt\n", encoding="utf-8")

    violations = verificar_imports_sandbox(str(tmp_path))
    assert violations == []


def test_import_sandbox_detected(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "leak.py").write_text(
        "import sandbox.poc\nfrom sandbox.experiment import run\n",
        encoding="utf-8"
    )

    violations = verificar_imports_sandbox(str(tmp_path))
    assert len(violations) == 2
    assert any("sandbox.poc" in v[2] for v in violations)
    assert any("sandbox.experiment" in v[2] for v in violations)


def test_prototype_promoted_without_tests_fails(tmp_path):
    features = tmp_path / "src" / "features" / "checkout"
    features.mkdir(parents=True)
    (features / "payment.py").write_text(
        "# Origem: Prototype experimental migrado\ndef cobrar(): pass\n",
        encoding="utf-8"
    )

    sem_testes = verificar_promocao_sem_testes(str(tmp_path))
    assert len(sem_testes) == 1
    assert "origem protótipo sem teste" in sem_testes[0]


def test_prototype_promoted_with_tests_passes(tmp_path):
    features = tmp_path / "src" / "features" / "checkout"
    features.mkdir(parents=True)
    (features / "payment.py").write_text(
        "# Origem: Prototype experimental migrado\ndef cobrar(): pass\n",
        encoding="utf-8"
    )

    tests = tmp_path / "tests" / "unit"
    tests.mkdir(parents=True)
    (tests / "test_checkout_payment.py").write_text("def test_cobrar(): pass\n", encoding="utf-8")

    sem_testes = verificar_promocao_sem_testes(str(tmp_path))
    assert sem_testes == []
