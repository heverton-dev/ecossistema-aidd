# -*- coding: utf-8 -*-
"""
aidd-visual-maps ciclo-01, Ticket 1 (D10): catálogo conferido contra o repositório.

Achado F1 do laudo: com o catálogo commitado citando um script já apagado, os
`--check` dos mapas e do livro davam exit 0 e o índice mostrava "concluído".
Aqui, num repositório de teste, o catálogo é gerado e commitado em dia, o script
é apagado e os três (mapa --check, livro --check e status_mapa) têm de acusar o
catálogo velho.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_mapas import commitar, copiar_repo, rodar  # noqa: E402

CATALOGO = "docs/auditoria/mapa-pecas/catalogo-pecas.json"
SCRIPT_APAGADO = "scripts/peca_que_sera_apagada.py"

STATUS_LEIS = (
    "import json, sys; sys.path.insert(0, 'scripts'); import mapa_visual as mv;"
    "cat = json.loads(mv.CATALOGO.read_text(encoding='utf-8')); print(mv.status_mapa('leis', cat))"
)
EM_DIA = (
    "import json, sys; sys.path.insert(0, 'scripts'); import catalogo_pecas as cp;"
    "print(json.dumps(cp.catalogo_em_dia(cp.RAIZ)))"
)


@pytest.fixture(scope="module")
def repo(tmp_path_factory):
    raiz = copiar_repo(tmp_path_factory.mktemp("repo_catalogo_fresco"))
    (raiz / SCRIPT_APAGADO).write_text('"""Peça que o teste apaga depois do catálogo commitado."""\n', encoding="utf-8")
    for passo in (("scripts/catalogo_pecas.py",), ("scripts/mapa_visual.py", "leis"),
                  ("scripts/livro_mapas.py",)):
        proc = rodar(raiz, *passo)
        assert proc.returncode == 0, f"{passo}: {proc.stdout}\n{proc.stderr}"
    commitar(raiz, CATALOGO, mensagem="catálogo em dia")
    assert SCRIPT_APAGADO.split("/")[1].removesuffix(".py") in (raiz / CATALOGO).read_text(encoding="utf-8")
    return raiz


def test_em_dia_antes_de_apagar(repo):
    """Controle: com o catálogo em dia, os três dizem que está tudo certo."""
    for passo in (("scripts/mapa_visual.py", "leis", "--check"), ("scripts/livro_mapas.py", "--check")):
        proc = rodar(repo, *passo)
        assert proc.returncode == 0, f"{passo}: {proc.stdout}\n{proc.stderr}"
    assert rodar(repo, "-c", STATUS_LEIS).stdout.strip() == "concluido"


def test_script_apagado_reprova_mapa_livro_e_indice(repo):
    (repo / SCRIPT_APAGADO).unlink()

    em_dia, divergentes = json.loads(rodar(repo, "-c", EM_DIA).stdout)
    assert em_dia is False and "scripts" in divergentes

    mapa = rodar(repo, "scripts/mapa_visual.py", "leis", "--check")
    assert mapa.returncode == 1, mapa.stdout + mapa.stderr
    assert "[DESATUALIZADO]" in mapa.stdout and "catálogo" in mapa.stdout

    livro = rodar(repo, "scripts/livro_mapas.py", "--check")
    assert livro.returncode == 1, livro.stdout + livro.stderr
    assert "[DESATUALIZADO]" in livro.stdout and "catálogo" in livro.stdout

    status = rodar(repo, "-c", STATUS_LEIS)
    assert status.stdout.strip() == "desatualizado", status.stdout + status.stderr
