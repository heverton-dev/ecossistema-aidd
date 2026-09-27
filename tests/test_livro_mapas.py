# -*- coding: utf-8 -*-
"""
Livro dos mapas (scripts/livro_mapas.py): partes geradas do catálogo e do ACHADOS.json.

Prova que o livro segue a ordem de leitura dos mapas, que todo achado em aberto
aparece no apêndice, que '--' não vira travessão, e que --check reprova parte
desatualizada.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import livro_mapas as lm  # noqa: E402
import mapa_visual as mv  # noqa: E402


def test_capitulos_seguem_a_ordem_dos_mapas():
    partes = lm.gerar()
    texto = "".join(partes[n] for n in sorted(partes))
    numeros = [int(n) for n in re.findall(r"^# Capítulo (\d+) — ", texto, flags=re.MULTILINE)]
    assert numeros == list(range(1, len(mv.MAPAS_PREVISTOS) + 1))
    titulos = re.findall(r"^# Capítulo \d+ — (.+)$", texto, flags=re.MULTILINE)
    assert titulos == [t for _, t, _ in mv.MAPAS_PREVISTOS]


def test_todo_achado_em_aberto_esta_no_apendice():
    import json
    achados = json.loads(lm.ACHADOS.read_text(encoding="utf-8"))["achados"]
    apendice = lm.gerar()["91-apendice-estado.md"]
    faltando = [x["id"] for x in achados if x["id"] not in apendice]
    assert not faltando


def test_traco_duplo_e_escapado():
    assert lm._txt("bridge scan --dir") == r"bridge scan \-\-dir"


def test_check_reprova_parte_desatualizada(tmp_path, monkeypatch):
    monkeypatch.setattr(lm, "LIVRO", tmp_path)
    (tmp_path / "partes").mkdir()
    (tmp_path / "partes" / "00-frontmatter.md").write_text("velho", encoding="utf-8")
    assert lm.main(["--check"]) == 1


def test_repositorio_em_dia():
    assert lm.main(["--check"]) == 0
