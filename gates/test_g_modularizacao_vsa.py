# -*- coding: utf-8 -*-
"""
Teste de Quality Gate Determinístico de modularizacao-vsa (Lei #13 / D13).
Exige que `gates/G_modularizacao_vsa.py`:
- aprove (exit 0) diretório sem acoplamento;
- reprove (exit 1) import não autorizado entre fatias.
"""

import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
GATE_SCRIPT = ROOT_DIR / "gates" / "G_modularizacao_vsa.py"


def test_g_modularizacao_vsa_aprova(tmp_path):
    fatia = tmp_path / "fatia_limpa"
    fatia.mkdir()
    (fatia / "handler.py").write_text("def soma(): return 42\n", encoding="utf-8")

    res = subprocess.run([sys.executable, str(GATE_SCRIPT), str(fatia)], capture_output=True, text=True)
    assert res.returncode == 0
    assert "APROVADO" in res.stdout


def test_g_modularizacao_vsa_reprova_acoplamento(tmp_path):
    fatia = tmp_path / "fatia_acoplada"
    fatia.mkdir()
    codigo_acoplado = "import tools.aidd_master.core\n"
    (fatia / "handler.py").write_text(codigo_acoplado, encoding="utf-8")

    res = subprocess.run([sys.executable, str(GATE_SCRIPT), str(fatia)], capture_output=True, text=True)
    assert res.returncode == 1
    assert "REPROVADO" in res.stdout

