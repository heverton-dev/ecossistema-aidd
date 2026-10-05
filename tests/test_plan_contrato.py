import pytest
from pathlib import Path
import importlib.util

def _carregar_modulo(nome, rel_path):
    p = Path(__file__).resolve().parent.parent / rel_path
    spec = importlib.util.spec_from_file_location(nome, str(p))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

contrato = _carregar_modulo("aidd_plan_contrato", "componentes/compartilhado/skills/aidd-plan/scripts/contrato.py")


def test_validar_status_item():
    assert contrato.validar_status_item("DRAFT") is True
    assert contrato.validar_status_item("APROVADO") is True
    assert contrato.validar_status_item("EM EXECUCAO") is True
    assert contrato.validar_status_item("CONCLUIDO") is True
    assert contrato.validar_status_item("STATUS_INVALIDO") is False


def test_validar_regra_nota_com_e_sem_evidencia():
    valido, _ = contrato.validar_nota_e_evidencia("8", "docs/melhorias/rep.html")
    assert valido is True

    invalido_sem_evidencia, msg = contrato.validar_nota_e_evidencia("8", None)
    assert invalido_sem_evidencia is False
    assert "exige evidencia" in msg

    valido_nao_auditado, _ = contrato.validar_nota_e_evidencia("NAO AUDITADO", None)
    assert valido_nao_auditado is True
