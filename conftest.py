# -*- coding: utf-8 -*-
"""
Isolamento git de TODA a suíte (raiz do pytest).

Dentro de um git hook (pre-commit) o git exporta GIT_DIR/GIT_INDEX_FILE. Numa
worktree o GIT_DIR é absoluto: todo 'git init'/'git commit' que um teste faz no
seu tmp_path passava a gravar na branch REAL da worktree (visto em 2026-09-24:
commits "Commit teste"/"Segredo novo nao catalogado" na branch do ciclo 4F).
Na main passava despercebido porque lá o GIT_DIR exportado é relativo ('.git').
"""

import os

VARIAVEIS_DE_REPOSITORIO_DO_HOOK = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_PREFIX",
)

for _var in VARIAVEIS_DE_REPOSITORIO_DO_HOOK:
    os.environ.pop(_var, None)
