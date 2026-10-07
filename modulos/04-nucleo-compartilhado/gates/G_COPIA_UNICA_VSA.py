#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_COPIA_UNICA_VSA (ciclo-03 VSA / D13)
=============================================================================
Uma peça, um lugar (decisões A e C do ciclo-03). Lê `git ls-files` e acusa:
  1. ferramenta presente em tools/aidd-<x>/ e também em modulos/ (pasta aidd-<x>);
  2. gate G_*.py com o mesmo nome em mais de uma pasta;
  3. skill com o mesmo nome em componentes/compartilhado/skills e modulos/**/skills.
Não contam (são peças, não cópias): os moldes de projeto do almoxarifado
(aidd_forge/templates/**, componentes/compartilhado/gates/** e
componentes/compartilhado/injetor/**, carimbados nos projetos gerados) e a evidência
de ciclo em docs/auditoria/**.

Níveis (AIDD_COPIA_UNICA_MODO, precedência: --modo > variável > padrão):
  - aviso    (padrão): imprime o relatório e sai com exit 0;
  - bloqueio          : exit 1 se houver violação.
Modo desconhecido ou git fora de repo → exit 1. Saída binária 0/1 (Lei #2).
=============================================================================
"""

import argparse
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[3]
MODOS = ("aviso", "bloqueio")
# Peças, não cópias: moldes carimbados em projetos gerados e evidência de auditoria.
FORA_DO_ESCOPO = (
    "aidd_forge/templates/",
    "componentes/compartilhado/gates/",
    "componentes/compartilhado/injetor/",
    "docs/auditoria/",
)


def _eh_peca(caminho: str) -> bool:
    return any(trecho in caminho for trecho in FORA_DO_ESCOPO)
SKILLS_COMPARTILHADAS = "componentes/compartilhado/skills/"


def _arquivos(raiz: Path) -> list[str]:
    proc = subprocess.run(["git", "ls-files", "-z"], cwd=str(raiz), capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", errors="replace").strip() or "git ls-files falhou")
    return [p for p in proc.stdout.decode("utf-8", errors="replace").split("\0") if p]


def ferramentas_duplicadas(arquivos: list[str]) -> list[str]:
    em_tools = {p.split("/")[1] for p in arquivos if p.startswith("tools/aidd-") and p.count("/") >= 2}
    em_modulos = set()
    for p in arquivos:
        if p.startswith("modulos/"):
            em_modulos.update(seg for seg in p.split("/")[:-1] if seg.startswith("aidd-"))
    return [f"ferramenta {nome}: tools/{nome}/ e modulos/" for nome in sorted(em_tools & em_modulos)]


def gates_duplicados(arquivos: list[str]) -> list[str]:
    locais = defaultdict(set)
    for p in arquivos:
        nome = p.rsplit("/", 1)[-1]
        if nome.startswith("G_") and nome.endswith(".py") and not _eh_peca(p):
            locais[nome].add(p.rsplit("/", 1)[0] if "/" in p else ".")
    return [f"gate {nome}: {', '.join(sorted(pastas))}"
            for nome, pastas in sorted(locais.items()) if len(pastas) > 1]


def skills_duplicadas(arquivos: list[str]) -> list[str]:
    compartilhadas, nas_fatias = set(), defaultdict(set)
    for p in arquivos:
        if p.startswith(SKILLS_COMPARTILHADAS) and p.count("/") >= 4:
            compartilhadas.add(p.split("/")[3])
        elif p.startswith("modulos/") and "/skills/" in p and not _eh_peca(p):
            antes, depois = p.split("/skills/", 1)
            if "/" in depois:
                nas_fatias[depois.split("/")[0]].add(antes + "/skills")
    return [f"skill {nome}: {SKILLS_COMPARTILHADAS.rstrip('/')} e {', '.join(sorted(nas_fatias[nome]))}"
            for nome in sorted(compartilhadas & set(nas_fatias))]


def _modo(cli: str | None) -> str:
    bruto = (cli or os.environ.get("AIDD_COPIA_UNICA_MODO", "") or "aviso").strip().lower()
    if bruto not in MODOS:
        raise ValueError(f"AIDD_COPIA_UNICA_MODO inválido: {bruto!r} (use aviso|bloqueio)")
    return bruto


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="G_COPIA_UNICA_VSA — uma peça, um lugar")
    parser.add_argument("--raiz", default=str(RAIZ))
    parser.add_argument("--modo", choices=MODOS, default=None)
    args = parser.parse_args(argv)

    try:
        modo = _modo(args.modo)
        arquivos = _arquivos(Path(args.raiz))
    except (ValueError, RuntimeError, OSError) as erro:
        print(f"[G_COPIA_UNICA_VSA] ERRO: {erro}")
        return 1

    violacoes = ferramentas_duplicadas(arquivos) + gates_duplicados(arquivos) + skills_duplicadas(arquivos)
    print(f"[G_COPIA_UNICA_VSA] modo {modo}: {len(violacoes)} violação(ões).")
    for v in violacoes:
        print(f"  - {v}")
    if violacoes and modo == "bloqueio":
        print("[G_COPIA_UNICA_VSA] REPROVADO: cada peça deve existir em um único lugar.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
