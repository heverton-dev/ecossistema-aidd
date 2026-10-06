#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prova que G_GRAPH_FIRST morde (Lei #13): agente com histórico legível e zero chamadas ao graph reprova."""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

GATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "G_GRAPH_FIRST.py")


def _historico(projetos: Path, worktree: Path, ferramentas: list) -> None:
    pasta = projetos / re.sub(r"[^A-Za-z0-9]", "-", str(worktree.resolve()))
    pasta.mkdir(parents=True)
    linhas = [{"type": "user", "message": {"content": "faça o ticket"}}]
    for nome in ferramentas:
        linhas.append({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": nome, "input": {}}]}})
    (pasta / "sessao.jsonl").write_text("\n".join(json.dumps(l) for l in linhas), encoding="utf-8")


def _rodar(tmp_path: Path, worktree: Path, *extra: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "AIDD_CLAUDE_PROJETOS": str(tmp_path / "projetos")}
    return subprocess.run([sys.executable, GATE_PATH, "--worktree", str(worktree), *extra], capture_output=True,
                          text=True, encoding="utf-8", errors="replace", env=env)


def test_agente_sem_chamada_ao_graph_reprova_exit_1(tmp_path):
    wt = tmp_path / "wt_fase"
    wt.mkdir()
    _historico(tmp_path / "projetos", wt, ["Bash", "Grep", "Read", "Bash"])

    res = _rodar(tmp_path, wt)

    assert res.returncode == 1, res.stdout + res.stderr
    assert "0 chamada" in res.stdout


def test_agente_que_consulta_o_graph_aprova(tmp_path):
    wt = tmp_path / "wt_fase"
    wt.mkdir()
    _historico(tmp_path / "projetos", wt, ["mcp__codebase-memory-mcp__search_graph", "Grep"])

    res = _rodar(tmp_path, wt)

    assert res.returncode == 0, res.stdout + res.stderr


def test_harness_sem_historico_legivel_so_avisa(tmp_path):
    wt = tmp_path / "wt_agy"
    wt.mkdir()
    (tmp_path / "projetos").mkdir()

    res = _rodar(tmp_path, wt)

    assert res.returncode == 0, res.stdout + res.stderr
    assert "AVISO" in res.stdout


def test_sessao_de_rodada_anterior_na_mesma_pasta_nao_conta(tmp_path):
    wt = tmp_path / "wt_fase"
    wt.mkdir()
    _historico(tmp_path / "projetos", wt, ["mcp__codebase-memory-mcp__search_graph"])
    antiga = next((tmp_path / "projetos").rglob("*.jsonl"))
    os.utime(antiga, (1000, 1000))

    res = _rodar(tmp_path, wt, "--desde", "2000")

    assert "AVISO" in res.stdout and res.returncode == 0
