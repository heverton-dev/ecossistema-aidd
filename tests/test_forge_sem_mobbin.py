# -*- coding: utf-8 -*-
"""ETAPA_09 (Ticket 5 da ETAPA_05): o Mobbin é do planner; o forge não tem subcomando `mobbin`.

O subcomando existia só declarado (sem tratamento) e duplicava `planner mobbin`. Cobrir pelo planner:
`python ecossistema.py planner mobbin search ...` (ou `python ecossistema.py mobbin ...`).
"""
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CLI_FORGE = RAIZ / "componentes" / "compartilhado" / "skills" / "aidd-forge" / "scripts" / "cli.py"


def test_forge_nao_tem_subcomando_mobbin():
    res = subprocess.run([sys.executable, "-X", "utf8", str(CLI_FORGE), "mobbin", "--help"],
                         cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    assert res.returncode != 0
    assert "invalid choice" in (res.stderr + res.stdout).lower() or "mobbin" in res.stderr.lower()


def test_forge_help_nao_lista_mobbin():
    res = subprocess.run([sys.executable, "-X", "utf8", str(CLI_FORGE), "--help"],
                         cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    assert "mobbin" not in res.stdout.lower()
