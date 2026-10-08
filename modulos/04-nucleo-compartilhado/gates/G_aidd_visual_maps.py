#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_aidd_visual_maps (D13 / aidd-visual-maps ciclo-01)
=============================================================================
Quality gate da ferramenta aidd-visual-maps. Junta, sem reimplementar, as conferências
que o ciclo-01 criou nos scripts dos mapas:
  1. catálogo em dia com o repositório      (catalogo_pecas.catalogo_em_dia);
  2. nenhum HTML órfão em docs/mapas-visuais (mapa_visual.arquivos_esperados);
  3. nenhuma frase-padrão em inglês nos mapas não técnicos (mapa_visual.frases_em_ingles);
  4. nenhuma contagem digitada nos moldes    (mapa_visual.contagens_digitadas);
  5. manual de montagem com link para cada mapa (mapa_visual.links_faltando_no_manual);
  6. manifesto MANIFESTO-MAPAS.json batendo com o disco: catálogo, cada mapa, partes do
     livro e PDF (handoff.conferir_manifesto) — pega mapa trocado depois do `gerar`.
O conteúdo de cada mapa contra o gerador é do G_mapa_pecas (não é repetido aqui).

Critérios de Aceite:
  - Exit 0: APROVADO, nenhuma das conferências acusou desvio.
  - Exit 1: REPROVADO, com um motivo por linha.
=============================================================================
"""

import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAIZ = next((p.parent for p in Path(__file__).resolve().parents if p.name == "modulos"), Path(__file__).resolve().parent.parent)  # raiz: pai de modulos/ (VSA) ou de gates/ (árvore sintética)

sys.path.insert(0, str(RAIZ / "componentes" / "compartilhado" / "skills" / "aidd-visual-maps" / "scripts"))
import handoff  # noqa: E402  (também põe scripts/ no sys.path, via cli)
import catalogo_pecas as cp  # noqa: E402
import mapa_visual as mv  # noqa: E402


def html_na_pasta() -> set[str]:
    """Todo .html sob docs/mapas-visuais/ que o git vê (versionado ou novo não ignorado)."""
    pasta = mv.MAPAS.relative_to(RAIZ).as_posix()
    saida = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", pasta],
                           cwd=RAIZ, capture_output=True, check=True).stdout.decode("utf-8")
    return {Path(rel).relative_to(pasta).as_posix() for rel in saida.split("\0")
            if rel.endswith(".html") and (RAIZ / rel).is_file()}


def auditar() -> list[str]:
    motivos = []
    em_dia, divergentes = cp.catalogo_em_dia(cp.RAIZ, cp.SAIDA_PADRAO)
    if not em_dia:
        motivos.append(f"catálogo desatualizado ({', '.join(divergentes)}): rode python ecossistema.py visual-maps gerar")
    motivos += [f"HTML órfão: {rel}" for rel in sorted(html_na_pasta() - mv.arquivos_esperados())]
    motivos += [f"inglês no mapa não técnico: {achado}" for achado in mv.frases_em_ingles()]
    motivos += [f"contagem digitada: {achado}" for achado in mv.contagens_digitadas()]
    manual = mv.MAPAS / mv.MANUAL
    if not manual.is_file():
        motivos.append(f"manual ausente: {mv.MANUAL}")
    else:
        motivos += [f"manual sem link para {arq}" for arq in mv.links_faltando_no_manual(manual.read_text(encoding="utf-8"))]
    motivos += [f"manifesto: {desvio}" for desvio in handoff.conferir_manifesto()]
    return motivos


def main() -> int:
    motivos = auditar()
    if not motivos:
        print("[G_aidd_visual_maps] APROVADO: catálogo, órfãos, PT-BR, contagens, manual e manifesto em dia.")
        return 0
    print("[G_aidd_visual_maps] REPROVADO:")
    for motivo in motivos:
        print(f"  - {motivo}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
