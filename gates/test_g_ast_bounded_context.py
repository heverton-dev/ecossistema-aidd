# -*- coding: utf-8 -*-
"""
Teste do Quality Gate G_AST_BOUNDED_CONTEXT (Lei #13 / Contraprova de reprovação exit 1).
"""

import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
GATE_SCRIPT = ROOT_DIR / "gates" / "G_AST_BOUNDED_CONTEXT.py"


def test_g_ast_bounded_context_aprova(tmp_path):
    fatia = tmp_path / "modulos" / "fatia_limpa"
    fatia.mkdir(parents=True)
    (fatia / "servico.py").write_text("import json\ndef run(): return json.dumps({'ok': True})\n", encoding="utf-8")

    res = subprocess.run([sys.executable, str(GATE_SCRIPT), str(tmp_path)], capture_output=True, text=True)
    assert res.returncode == 0
    assert "APROVADO" in res.stdout


def test_g_ast_bounded_context_reprova_acoplamento(tmp_path):
    fatia = tmp_path / "modulos" / "fatia_acoplada"
    fatia.mkdir(parents=True)
    (fatia / "servico.py").write_text("import tools.aidd_master.core\n", encoding="utf-8")

    res = subprocess.run([sys.executable, str(GATE_SCRIPT), str(tmp_path)], capture_output=True, text=True)
    assert res.returncode == 1
    assert "REPROVADO" in res.stdout
