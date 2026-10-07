# -*- coding: utf-8 -*-
import subprocess
import sys
from pathlib import Path
import tempfile
import importlib.util

ROOT = next((p.parent for p in Path(__file__).resolve().parents if p.name == "modulos"), Path(__file__).resolve().parent.parent)  # raiz: pai de modulos/ (VSA) ou de gates/ (árvore sintética)

def _carregar_modulo(nome, rel_path):
    p = ROOT / rel_path
    spec = importlib.util.spec_from_file_location(nome, str(p))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

g_planner = _carregar_modulo("g_aidd_planner_runner", "modulos/01-governanca-e-qualidade/gates/G_aidd_planner_runner.py")


def test_gate_planner_runner_valida_projeto():
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir)
        (dest / "PLANNER.json").write_text('{"projeto": "ok"}', encoding="utf-8")

        res = subprocess.run([sys.executable, str(ROOT / "modulos" / "01-governanca-e-qualidade" / "gates" / "G_aidd_planner_runner.py"), str(dest)], capture_output=True)
        assert res.returncode == 0


def test_gate_planner_runner_reprova_sem_planner():
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir)
        res = subprocess.run([sys.executable, str(ROOT / "modulos" / "01-governanca-e-qualidade" / "gates" / "G_aidd_planner_runner.py"), str(dest)], capture_output=True)
        assert res.returncode == 1
