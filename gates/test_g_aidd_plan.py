# -*- coding: utf-8 -*-
import subprocess
import sys
from pathlib import Path
import tempfile
import importlib.util

ROOT = Path(__file__).resolve().parent.parent

def _carregar_modulo(nome, rel_path):
    p = ROOT / rel_path
    spec = importlib.util.spec_from_file_location(nome, str(p))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

g_plan = _carregar_modulo("g_aidd_plan", "gates/G_aidd_plan.py")


def test_gate_plan_aprova_plano_valido():
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir)
        pasta = dest / "PLAN-0001-teste"
        pasta.mkdir()
        (pasta / "00-PROCESSO-E-DECISOES.md").write_text("# Processo\n```bash\necho ok\n```\n", encoding="utf-8")
        (pasta / "01-item.md").write_text("# Item 1\n> **Status:** [DRAFT]\n", encoding="utf-8")

        res = subprocess.run([sys.executable, str(ROOT / "gates" / "G_aidd_plan.py"), str(pasta)], capture_output=True)
        assert res.returncode == 0


def test_gate_plan_reprova_sem_processo():
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir)
        pasta = dest / "PLAN-0001-teste"
        pasta.mkdir()
        (pasta / "01-item.md").write_text("# Item 1\n", encoding="utf-8")

        res = subprocess.run([sys.executable, str(ROOT / "gates" / "G_aidd_plan.py"), str(pasta)], capture_output=True)
        assert res.returncode == 1


def test_gate_plan_reprova_cerca_quebrada():
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir)
        pasta = dest / "PLAN-0001-teste"
        pasta.mkdir()
        (pasta / "00-PROCESSO-E-DECISOES.md").write_text("# Processo\n```bash\necho ok\nsem fechar\n", encoding="utf-8")

        res = subprocess.run([sys.executable, str(ROOT / "gates" / "G_aidd_plan.py"), str(pasta)], capture_output=True)
        assert res.returncode == 1
