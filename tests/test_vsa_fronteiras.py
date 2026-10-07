import sys

import pytest
from pathlib import Path

# G_modularizacao_vsa mora no núcleo (MAPA-GATES.json, ciclo-03 VSA).
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "modulos" / "04-nucleo-compartilhado" / "gates"))

def test_gate_modularizacao_vsa_aprova_codigo_sem_acoplamento(tmp_path):
    from G_modularizacao_vsa import verificar_fronteiras_vsa

    fatia = tmp_path / "fatia_limpa"
    fatia.mkdir()
    codigo_limpo = """
import os
import sys

def handler():
    return 42
"""
    (fatia / "handler.py").write_text(codigo_limpo, encoding="utf-8")

    aprovado, violacoes = verificar_fronteiras_vsa(fatia)
    assert aprovado is True
    assert violacoes == []

def test_gate_modularizacao_vsa_rejeita_import_ilegal_entre_fatias(tmp_path):
    from G_modularizacao_vsa import verificar_fronteiras_vsa

    fatia = tmp_path / "fatia_acoplada"
    fatia.mkdir()
    codigo_acoplado = """
import os
from tools.aidd_master.core import modulo_secreto

def handler():
    return modulo_secreto()
"""
    (fatia / "handler.py").write_text(codigo_acoplado, encoding="utf-8")

    aprovado, violacoes = verificar_fronteiras_vsa(fatia)
    assert aprovado is False
    assert len(violacoes) == 1
    assert "tools.aidd_master.core" in violacoes[0]
