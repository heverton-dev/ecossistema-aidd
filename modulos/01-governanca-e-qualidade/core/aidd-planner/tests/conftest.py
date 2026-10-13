# -*- coding: utf-8 -*-
"""Conftest próprio da suíte (ciclo-03 VSA, Ticket 16): com pytest.ini aqui a raiz do pytest
é esta pasta e o conftest.py do repositório não carrega mais. Dentro do pre-commit o git exporta
GIT_DIR/GIT_INDEX_FILE; um 'git init'/'git commit' de teste em tmp_path gravaria no repositório real."""

import os

for _var in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR",
             "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_PREFIX"):
    os.environ.pop(_var, None)


import pytest


@pytest.fixture(autouse=True)
def _ambiente_ja_registrado(request, monkeypatch):
    """O `planner init` agora exige o bloco Ambiente (Mobbin escolhido + variáveis de deploy).
    Os testes que exercitam OUTRO assunto partem do ambiente já satisfeito; o bloqueio de verdade
    é provado em test_ambiente.py, que não usa esta fixture."""
    if request.module.__name__.endswith("test_ambiente"):
        return
    from src.core_planner import ambiente
    monkeypatch.setattr(ambiente, "verificar", lambda pasta, env: [])
