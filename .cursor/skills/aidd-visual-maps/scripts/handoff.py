# -*- coding: utf-8 -*-
"""
Handoff do aidd-visual-maps (ciclo-01, Ticket 14): manifesto dos mapas e entrega ao livro.

  compilar_livro(raiz)        -> roda o build do aidd-textbook para docs/livros/mapas-aidd/
                                 (o `gerar` chama na worktree efêmera, depois do livro_mapas.py);
  emitir_manifesto(exit_build) -> grava docs/mapas-visuais/MANIFESTO-MAPAS.json via gravar_lote:
                                 hash do catálogo, cada mapa (técnico e não técnico) com
                                 arquivo/versao/sha256/status, e o handoff ao livro (partes com
                                 hash e o resultado do build). Sem data/hora: o mesmo estado
                                 gera o mesmo arquivo (tempos ficam na telemetria);
  conferir_manifesto()        -> lista de desvios entre o manifesto e o disco (vazia = em dia),
                                 usada pelo `visual-maps check`.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import cli
from cli import REPO_ROOT, cp, livro_mapas, mv
import compilar_mapas_nao_tecnicos as nt  # noqa: E402  (scripts/ já está no sys.path pelo cli)
from gravacao_atomica_mapas import gravar_lote  # noqa: E402

MANIFESTO = mv.MAPAS / "MANIFESTO-MAPAS.json"
LIVRO = livro_mapas.LIVRO
TEXTBOOK = Path("componentes") / "compartilhado" / "skills" / "aidd-textbook" / "scripts" / "livro.py"


def _sha(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def _rel(caminho: Path) -> str:
    return caminho.relative_to(REPO_ROOT).as_posix()


def compilar_livro(raiz: Path) -> int:
    """Build do aidd-textbook (pandoc + typst) da pasta do livro dentro de `raiz`; devolve o exit code."""
    pasta = raiz / LIVRO.relative_to(REPO_ROOT)
    return subprocess.run([sys.executable, str(raiz / TEXTBOOK), "build", str(pasta)],
                          cwd=raiz, env=cli.ambiente()).returncode


def _status_nao_tecnico(tipo: str, cat: dict, catalogo_em_dia: bool) -> str:
    arquivo = nt.destino(tipo)
    if not arquivo.is_file():
        return "a-criar"
    em_dia = catalogo_em_dia and arquivo.read_text(encoding="utf-8") == nt.compilar_nao_tecnico(tipo, cat)
    return "concluido" if em_dia else "desatualizado"


def montar_manifesto(exit_build: int) -> dict:
    cat = json.loads(cp.SAIDA_PADRAO.read_text(encoding="utf-8"))
    em_dia = cp.catalogo_em_dia(cp.RAIZ, cp.SAIDA_PADRAO)[0]
    mapas = []
    for tipo in cli.tipos_na_ordem():
        for versao, arquivo, status in (
                ("tecnica", mv.MAPAS / mv.arquivo_mapa(tipo), mv.status_mapa(tipo, cat, em_dia)),
                ("nao-tecnica", nt.destino(tipo), _status_nao_tecnico(tipo, cat, em_dia))):
            mapas.append({"tipo": tipo, "arquivo": _rel(arquivo), "versao": versao,
                          "sha256": _sha(arquivo) if arquivo.is_file() else None, "status": status})
    livro = json.loads((LIVRO / "livro.json").read_text(encoding="utf-8"))
    partes = [LIVRO / livro["pasta_partes"] / nome for nome in livro["partes"]]
    pdf = LIVRO / f"{livro['nome_base']}.pdf"
    return {
        "ferramenta": "aidd-visual-maps",
        "catalogo": _rel(cp.SAIDA_PADRAO),
        "hash_catalogo": _sha(cp.SAIDA_PADRAO),
        "mapas": mapas,
        "handoff_livro": {
            "skill": "aidd-textbook",
            "pasta": _rel(LIVRO),
            "partes": [{"arquivo": _rel(p), "sha256": _sha(p)} for p in partes],
            "build": {"comando": f"python {TEXTBOOK.as_posix()} build {_rel(LIVRO)}", "exit_code": exit_build,
                      "pdf": _rel(pdf), "sha256": _sha(pdf) if exit_build == 0 and pdf.is_file() else None},
        },
    }


def emitir_manifesto(exit_build: int) -> Path:
    texto = json.dumps(montar_manifesto(exit_build), ensure_ascii=False, indent=2) + "\n"
    gravar_lote({MANIFESTO: texto})
    return MANIFESTO


def conferir_manifesto() -> list[str]:
    """Desvios entre o manifesto e o disco: catálogo, cada mapa previsto, partes do livro e PDF."""
    if not MANIFESTO.is_file():
        return [f"{_rel(MANIFESTO)} não existe. Rode: python ecossistema.py visual-maps gerar"]
    manifesto = json.loads(MANIFESTO.read_text(encoding="utf-8"))
    desvios = []
    if not cp.SAIDA_PADRAO.is_file() or manifesto.get("hash_catalogo") != _sha(cp.SAIDA_PADRAO):
        desvios.append(f"{_rel(cp.SAIDA_PADRAO)} difere do hash_catalogo")
    previstos = {_rel(arquivo) for tipo in cli.tipos_na_ordem()
                 for arquivo in (mv.MAPAS / mv.arquivo_mapa(tipo), nt.destino(tipo))}
    registrados = {m["arquivo"] for m in manifesto.get("mapas", [])}
    desvios += [f"{arq} fora do manifesto" for arq in sorted(previstos - registrados)]
    handoff = manifesto.get("handoff_livro", {})
    livro = json.loads((LIVRO / "livro.json").read_text(encoding="utf-8"))
    if [Path(p["arquivo"]).name for p in handoff.get("partes", [])] != livro["partes"]:
        desvios.append("partes do livro no manifesto diferem de livro.json")
    build = handoff.get("build", {})
    conferidos = [*manifesto.get("mapas", []), *handoff.get("partes", [])]
    if build.get("sha256"):
        conferidos.append({"arquivo": build["pdf"], "sha256": build["sha256"]})
    for entrada in conferidos:
        arquivo = REPO_ROOT / entrada["arquivo"]
        if not arquivo.is_file() or _sha(arquivo) != entrada["sha256"]:
            desvios.append(f"{entrada['arquivo']} difere do sha256 do manifesto")
    return desvios
