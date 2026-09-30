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


# ---------------------------------------------------------------------------
# Isolamento de módulos homônimos das skills.
#
# Várias skills têm scripts/ com o mesmo nome curto (handoff.py, fallback.py,
# cli.py, parser.py...) e os testes os importam por esse nome ('import handoff').
# Na suíte inteira o Python devolvia o PRIMEIRO 'handoff' carregado para todos os
# testes seguintes (visto em 2026-09-30: 26 falhas em aidd-spec/tdd/tickets com
# "module 'handoff' has no attribute 'gerar_handoff_spec'"). Antes de importar
# cada arquivo de teste, e antes de cada teste, os módulos de skills já
# carregados saem do sys.modules e as pastas de scripts daquele arquivo de teste
# voltam para o topo do sys.path.
# ---------------------------------------------------------------------------

import sys

import pytest

_DIRS_SCRIPTS_POR_MODULO = {}


def _e_pasta_scripts_de_skill(caminho):
    partes = os.path.normcase(os.path.abspath(caminho)).split(os.sep)
    return "skills" in partes and partes[-1] == "scripts"


def _purgar_modulos_de_skills():
    for nome, modulo in list(sys.modules.items()):
        arquivo = getattr(modulo, "__file__", None)
        if arquivo and _e_pasta_scripts_de_skill(os.path.dirname(arquivo)):
            del sys.modules[nome]


def _pastas_scripts_do_modulo(modulo_teste, sys_path_antes):
    """Pastas scripts/ de skill que o arquivo de teste usa: as que ele pôs no
    sys.path, as dos módulos de skill que ele importou e as que guarda em
    variáveis globais (SCRIPTS, SKILL_SCRIPTS...), porque o 'if not in sys.path'
    de alguns testes não reinsere uma pasta que outro teste já colocou."""
    pastas = [p for p in sys.path if p not in sys_path_antes and _e_pasta_scripts_de_skill(p)]
    for valor in list(vars(modulo_teste).values()):
        arquivo = getattr(valor, "__file__", None)
        candidato = os.path.dirname(arquivo) if arquivo else valor
        if isinstance(candidato, (str, os.PathLike)):
            candidato = os.path.abspath(os.fspath(candidato))
            if os.path.isdir(candidato) and _e_pasta_scripts_de_skill(candidato) and candidato not in pastas:
                pastas.append(candidato)
    return pastas


@pytest.hookimpl(hookwrapper=True)
def pytest_pycollect_makemodule(module_path, parent):
    _purgar_modulos_de_skills()
    antes = list(sys.path)
    resultado = yield
    modulo = resultado.get_result()
    if modulo is None:
        return
    try:
        obj = modulo.obj  # força o import agora, para medir o que ele pôs no sys.path
    except BaseException:
        return  # o próprio pytest reporta o erro de import na coleta
    _DIRS_SCRIPTS_POR_MODULO[str(module_path)] = _pastas_scripts_do_modulo(obj, antes)


@pytest.fixture(autouse=True)
def _isolar_modulos_de_skills(request):
    _purgar_modulos_de_skills()
    for pasta in reversed(_DIRS_SCRIPTS_POR_MODULO.get(str(request.path), [])):
        if pasta in sys.path:
            sys.path.remove(pasta)
        sys.path.insert(0, pasta)
    yield
