# -*- coding: utf-8 -*-
import json
import pytest
from pathlib import Path

from contratos.validador_sha256 import (
    calcular_sha256_payload,
    assinar_contrato_payload,
    validar_integridade_contrato,
)


def test_calcular_sha256_payload_deterministico():
    d1 = {"b": 2, "a": 1}
    d2 = {"a": 1, "b": 2}
    assert calcular_sha256_payload(d1) == calcular_sha256_payload(d2)
    assert len(calcular_sha256_payload(d1)) == 64


def test_assinar_e_validar_contrato_ok(tmp_path: Path):
    d = {"projeto": "teste", "fases": [1, 2, 3]}
    assinado = assinar_contrato_payload(d)
    assert "payload_sha256" in assinado
    assert len(assinado["payload_sha256"]) == 64

    ok, motivo = validar_integridade_contrato(assinado)
    assert ok is True
    assert motivo == ""

    # Teste gravando em disco
    p = tmp_path / "contrato.json"
    p.write_text(json.dumps(assinado), encoding="utf-8")
    ok_disco, motivo_disco = validar_integridade_contrato(p)
    assert ok_disco is True
    assert motivo_disco == ""


def test_validar_integridade_adulterado():
    d = {"projeto": "teste", "fases": [1, 2, 3]}
    assinado = assinar_contrato_payload(d)
    assinado["fases"].append(4)  # Adultera o payload

    ok, motivo = validar_integridade_contrato(assinado)
    assert ok is False
    assert "Violação de integridade SHA-256" in motivo


def test_validar_integridade_hash_ausente():
    d = {"projeto": "teste"}
    ok, motivo = validar_integridade_contrato(d)
    assert ok is False
    assert "ausente" in motivo


def test_validar_arquivo_inexistente():
    ok, motivo = validar_integridade_contrato(Path("caminho_inexistente.json"))
    assert ok is False
    assert "não encontrado" in motivo
