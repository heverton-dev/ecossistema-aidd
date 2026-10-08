# -*- coding: utf-8 -*-
"""Ciclo-03 VSA, Bloco 6 (achado do Bloco 3): a barreira calculava a raiz do ecossistema
em modulos/03-plataforma-e-entrega, o import de micro_gates_worktree falhava e o
ImportError era engolido. Os micro-gates (sintaxe, stubs) nunca rodavam."""
import subprocess
import sys
from pathlib import Path

MASTER_DIR = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = MASTER_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import vsa_join_barrier  # noqa: E402


def test_raiz_do_ecossistema_e_o_pai_de_modulos():
    assert (vsa_join_barrier.ROOT_DIR / "modulos").is_dir(), vsa_join_barrier.ROOT_DIR
    assert (vsa_join_barrier.ROOT_DIR / "scripts" / "micro_gates_worktree.py").is_file()


def test_barreira_roda_micro_gates_e_reprova_sintaxe_invalida(tmp_path):
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True, check=True)
    fatia = tmp_path / "src" / "slices" / "auth"
    fatia.mkdir(parents=True)
    (fatia / "router.py").write_text("def quebrado(:\n", encoding="utf-8")
    slice_info = {
        "slice_id": "slice_auth",
        "barreira_validacao": {"comandos_teste": [], "quality_gates": []},
    }
    aprovado, erros = vsa_join_barrier.executar_barreira_fatia(tmp_path, slice_info, verbose=False)
    assert aprovado is False
    assert any("Erro de sintaxe" in e for e in erros), erros


def test_micro_gates_indisponivel_reprova_em_vez_de_pular(tmp_path, monkeypatch):
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True, check=True)
    monkeypatch.setattr(vsa_join_barrier, "ROOT_DIR", tmp_path / "sem-ecossistema")
    monkeypatch.delitem(sys.modules, "micro_gates_worktree", raising=False)
    monkeypatch.setattr(sys, "path", [p for p in sys.path if not Path(p, "micro_gates_worktree.py").is_file()])
    slice_info = {"slice_id": "slice_auth", "barreira_validacao": {"comandos_teste": [], "quality_gates": []}}
    aprovado, erros = vsa_join_barrier.executar_barreira_fatia(tmp_path, slice_info, verbose=False)
    assert aprovado is False
    assert any("micro_gates_worktree" in e for e in erros), erros
