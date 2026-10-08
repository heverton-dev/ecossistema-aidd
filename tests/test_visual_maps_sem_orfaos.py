# -*- coding: utf-8 -*-
"""
aidd-visual-maps ciclo-01, Ticket 3 (D3): nenhum HTML órfão em docs/mapas-visuais/.

Achado F3 do laudo: docs/mapas-visuais/tecnicos/ tinha 14 cópias versionadas que
nenhum script gera nem lê. Todo .html da pasta (versionado ou novo) tem de ser um
arquivo esperado: mapa oficial de MAPAS_PREVISTOS + índice, seu par não técnico,
o manual (e o par dele) ou um molde de moldes/ e moldes-nao-tecnicos/.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAPAS = ROOT / "docs" / "mapas-visuais"
sys.path.insert(0, str(ROOT / "scripts"))

import mapa_visual as mv  # noqa: E402


def html_na_pasta() -> set[str]:
    """Todo .html sob docs/mapas-visuais/ que o git vê (versionado ou novo não ignorado)."""
    saida = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", "docs/mapas-visuais"],
                           cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8")
    return {Path(rel).relative_to("docs/mapas-visuais").as_posix() for rel in saida.split("\0")
            if rel.endswith(".html") and (ROOT / rel).is_file()}


def test_nenhum_html_orfao_em_mapas_visuais():
    orfaos = sorted(html_na_pasta() - mv.arquivos_esperados())
    assert not orfaos, f"{len(orfaos)} HTML sem dono em docs/mapas-visuais/: {orfaos}"


def test_esperados_cobrem_mapas_pares_manual_e_moldes():
    esperados = mv.arquivos_esperados()
    for tipo in ("indice", *(t for t, _, _ in mv.MAPAS_PREVISTOS)):
        assert mv.arquivo_mapa(tipo) in esperados and f"nao-tecnicos/{mv.arquivo_mapa(tipo)}" in esperados
        assert f"moldes/{tipo}.html" in esperados and f"moldes-nao-tecnicos/{tipo}.html" in esperados
    assert {"manual-montagem-aidd.html", "nao-tecnicos/manual-montagem-aidd.html"} <= esperados
    assert not any(rel.startswith("tecnicos/") for rel in esperados)
