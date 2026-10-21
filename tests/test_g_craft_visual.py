# -*- coding: utf-8 -*-
"""
Bateria de testes que prova que o gate G_CRAFT_VISUAL morde (Lei #13).
"""

import os
import subprocess
import sys
from pathlib import Path
import pytest


def _achar_gate() -> str:
    curr = Path(__file__).resolve().parent
    while curr.parent != curr:
        cand = curr / "modulos" / "01-governanca-e-qualidade" / "gates" / "G_CRAFT_VISUAL.py"
        if cand.is_file():
            return str(cand)
        cand_local = curr / "G_CRAFT_VISUAL.py"
        if cand_local.is_file():
            return str(cand_local)
        curr = curr.parent
    raise FileNotFoundError("G_CRAFT_VISUAL.py não encontrado")


GATE_PATH = _achar_gate()


def test_craft_visual_aprova_frontend_conforme(tmp_path):
    """Frontend bem formatado com tokens OKLCH e sem emojis deve retornar exit 0."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "tokens.css").write_text(":root { --primary: oklch(0.6 0.2 260); }", encoding="utf-8")
    (src / "Page.tsx").write_text(
        "export function Page() { return <div className='grid grid-cols-1 md:grid-cols-3 gap-6 text-slate-100'>Dashboard</div>; }",
        encoding="utf-8",
    )

    res = subprocess.run(
        [sys.executable, GATE_PATH, "--alvo", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "[PASS]" in res.stdout


def test_craft_visual_morde_se_houver_emoji_em_ui(tmp_path):
    """Frontend com emojis amadores deve reprovar (exit 1)."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "tokens.css").write_text(":root { --primary: oklch(0.6 0.2 260); }", encoding="utf-8")
    (src / "BadPage.tsx").write_text(
        "export function BadPage() { return <div>🚀 Sucesso total! 🎉</div>; }",
        encoding="utf-8",
    )

    res = subprocess.run(
        [sys.executable, GATE_PATH, "--alvo", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1
    assert "Emoji Unicode detectado" in res.stdout


def test_craft_visual_morde_se_layout_for_espremido(tmp_path):
    """Frontend com layout espremido amador (max-w-xs min-h-screen) deve reprovar (exit 1)."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "tokens.css").write_text(":root { --primary: oklch(0.6 0.2 260); }", encoding="utf-8")
    (src / "NarrowPage.tsx").write_text(
        "export function NarrowPage() { return <div className='max-w-xs min-h-screen'>Espremido</div>; }",
        encoding="utf-8",
    )

    res = subprocess.run(
        [sys.executable, GATE_PATH, "--alvo", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1
    assert "Layout principal confinado" in res.stdout


def test_craft_visual_morde_se_nao_houver_tokens(tmp_path):
    """Frontend sem tokens OKLCH/Design System deve reprovar (exit 1)."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "SimplePage.tsx").write_text(
        "export function SimplePage() { return <div>Simples</div>; }",
        encoding="utf-8",
    )

    res = subprocess.run(
        [sys.executable, GATE_PATH, "--alvo", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1
    assert "Nenhum arquivo de tokens OKLCH" in res.stdout
