# -*- coding: utf-8 -*-
"""
aidd-visual-maps ciclo-01, Ticket 7 (D8): nenhuma contagem digitada nos moldes.

Achados N2/N7 do laudo: o molde não técnico dizia "13 leis" com o catálogo em 14, e
"8 ferramentas" estava digitado no molde e em MAPAS_PREVISTOS. Todo número de peças
vem do catálogo (Lei #8): nos moldes, como marcador {{TOTAL_<CHAVE>}} preenchido de
totais; nas descrições de MAPAS_PREVISTOS, não aparece.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAPAS = ROOT / "docs" / "mapas-visuais"
sys.path.insert(0, str(ROOT / "scripts"))

import mapa_visual as mv  # noqa: E402

RE_CONTAGEM = re.compile(r"\b\d+\s+(leis|ferramentas|mapas|skills|guardas|scripts|hooks|comandos)\b", re.IGNORECASE)


def contagens_digitadas() -> list[str]:
    achados = []
    for molde in sorted([*(MAPAS / "moldes").glob("*.html"), *(MAPAS / "moldes-nao-tecnicos").glob("*.html")]):
        for n, linha in enumerate(molde.read_text(encoding="utf-8").splitlines(), 1):
            achados += [f"{molde.parent.name}/{molde.name}:{n}: {m.group(0)}" for m in RE_CONTAGEM.finditer(linha)]
    for tipo, titulo, para_que in mv.MAPAS_PREVISTOS:
        achados += [f"MAPAS_PREVISTOS[{tipo}]: {m.group(0)}" for m in RE_CONTAGEM.finditer(f"{titulo} {para_que}")]
    return achados


def test_nenhuma_contagem_digitada_nos_moldes_nem_em_mapas_previstos():
    achados = contagens_digitadas()
    assert not achados, achados


def test_detector_acha_contagem_digitada():
    assert RE_CONTAGEM.search("as 13 Leis do ecossistema") and not RE_CONTAGEM.search("as {{TOTAL_LEIS}} leis")


def test_total_de_leis_no_mapa_nao_tecnico_vem_do_catalogo():
    cat = json.loads(mv.CATALOGO.read_text(encoding="utf-8"))
    texto = (MAPAS / "nao-tecnicos" / mv.arquivo_mapa("leis")).read_text(encoding="utf-8")
    numeros = {int(m.group(1)) for m in re.finditer(r"\b(\d+) [Ll]eis\b", texto)}
    assert numeros == {cat["totais"]["leis"]}, numeros
    ferramentas = (MAPAS / "nao-tecnicos" / mv.arquivo_mapa("ferramentas")).read_text(encoding="utf-8")
    assert {int(m.group(1)) for m in re.finditer(r"\b(\d+) [Ff]erramentas\b", ferramentas)} == {cat["totais"]["ferramentas"]}
