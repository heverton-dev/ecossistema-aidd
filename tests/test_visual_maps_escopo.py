# -*- coding: utf-8 -*-
"""
aidd-visual-maps ciclo-01, Ticket 10 (D3): escopo de escrita permitido.

Achado do laudo (D3 / DoD 2): `mapa_visual.py leis --saida <raiz>/AGENTS.md` gravava o
mapa por cima de qualquer arquivo. Dentro do repositório só se grava em
docs/mapas-visuais/, docs/auditoria/mapa-pecas/ e docs/livros/mapas-aidd/; fora dele, só
no diretório temporário (onde moram as worktrees efêmeras de teste). O resto é
[ERRO] com exit 1, sem tocar no arquivo.
"""
import hashlib
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_mapas import copiar_repo, rodar  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


@pytest.fixture(scope="module")
def repo(tmp_path_factory):
    return copiar_repo(tmp_path_factory.mktemp("repo_escopo"))


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


@pytest.mark.parametrize("script,args", [
    ("scripts/mapa_visual.py", ["leis", "--fragmento"]),
    ("scripts/catalogo_pecas.py", ["--sem-encaixe"]),
])
def test_saida_em_agents_md_reprova_sem_tocar_no_arquivo(repo, script, args):
    agents = repo / "AGENTS.md"
    antes = _sha(agents)
    proc = rodar(repo, script, *args, "--saida", str(agents))
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "[ERRO]" in proc.stdout and "fora do escopo" in proc.stdout
    assert "Traceback" not in proc.stdout + proc.stderr
    assert _sha(agents) == antes


def test_saida_no_diretorio_temporario_continua_valendo(repo, tmp_path):
    saida = tmp_path / "leis.html"
    proc = rodar(repo, "scripts/mapa_visual.py", "leis", "--fragmento", "--saida", str(saida))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert saida.read_text(encoding="utf-8").startswith("<title>")


def test_garantir_escopo_regras():
    import escopo_escrita_mapas as ee
    raiz = ROOT
    assert ee.garantir_escopo(raiz / "docs" / "mapas-visuais" / "mapa-01-leis.html") == \
        (raiz / "docs" / "mapas-visuais" / "mapa-01-leis.html").resolve()
    for permitido in ("docs/auditoria/mapa-pecas/catalogo-pecas.json", "docs/livros/mapas-aidd/partes/x.md"):
        ee.garantir_escopo(raiz / permitido)
    ee.garantir_escopo(Path(tempfile.gettempdir()) / "qualquer" / "x.html")
    for proibido in ("AGENTS.md", "docs/mapas-visuais/../../AGENTS.md", "scripts/mapa_visual.py", "docs/planos/x.html"):
        with pytest.raises(ee.ForaDoEscopo):
            ee.garantir_escopo(raiz / proibido)
