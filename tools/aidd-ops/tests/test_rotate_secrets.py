# -*- coding: utf-8 -*-
"""
Testes unitários para rotate_secrets.py em aidd-ops
"""

import os
import sys
import pytest

TOOL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if TOOL_ROOT not in sys.path:
    sys.path.insert(0, TOOL_ROOT)

from scripts.rotate_secrets import (
    gerar_segredo_criptografico,
    rotacionar_segredos,
    verificar_integridade_segredos,
)


def test_gerar_segredo_criptografico_entropy():
    jwt = gerar_segredo_criptografico("jwt_secret")
    db = gerar_segredo_criptografico("db_password")

    assert len(jwt) == 128  # 64 bytes hex = 128 chars
    assert len(db) >= 32
    assert jwt != db


def test_rotacionar_segredos_cria_arquivos_e_auditoria(tmp_path):
    secrets_dir = tmp_path / "secrets"
    res = rotacionar_segredos(str(secrets_dir), keys=["jwt_secret", "db_password"])

    assert len(res["rotacionados"]) == 2
    assert (secrets_dir / "jwt_secret.txt").is_file()
    assert (secrets_dir / "db_password.txt").is_file()
    assert (secrets_dir / "rotation_audit.json").is_file()
    assert verificar_integridade_segredos(str(secrets_dir), keys=["jwt_secret", "db_password"]) is True


def test_rotacionar_segredos_preserva_backup_anterior(tmp_path):
    secrets_dir = tmp_path / "secrets"
    # Primeira geracao
    rotacionar_segredos(str(secrets_dir), keys=["jwt_secret"])
    primeiro_valor = (secrets_dir / "jwt_secret.txt").read_text(encoding="utf-8")

    # Segunda rotacao
    rotacionar_segredos(str(secrets_dir), keys=["jwt_secret"])
    segundo_valor = (secrets_dir / "jwt_secret.txt").read_text(encoding="utf-8")
    backup_valor = (secrets_dir / "jwt_secret.prev").read_text(encoding="utf-8")

    assert primeiro_valor != segundo_valor
    assert backup_valor == primeiro_valor


def test_verificar_integridade_falha_se_ausente(tmp_path):
    secrets_dir = tmp_path / "vazio"
    assert verificar_integridade_segredos(str(secrets_dir), keys=["jwt_secret"]) is False
