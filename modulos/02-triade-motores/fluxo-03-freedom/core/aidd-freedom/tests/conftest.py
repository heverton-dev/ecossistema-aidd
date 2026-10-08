# -*- coding: utf-8 -*-
"""Conftest próprio da suíte (ciclo-03 VSA, Ticket 16): com pytest.ini aqui a raiz do pytest
é esta pasta e o conftest.py do repositório não carrega mais. Dentro do pre-commit o git exporta
GIT_DIR/GIT_INDEX_FILE; um 'git init'/'git commit' de teste em tmp_path gravaria no repositório real."""

import os

for _var in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR",
             "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_PREFIX"):
    os.environ.pop(_var, None)
