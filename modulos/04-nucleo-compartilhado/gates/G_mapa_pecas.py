#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_mapa_pecas (Lei #8 / Lei #13 / D14)
=============================================================================
Quality Gate Determinístico de Integridade do Mapa de Peças e Catálogo.
Valida estritamente:
  1. Integridade estrutural e factual do catálogo de peças (catalogo-pecas.json).
  2. Inexistência de achados críticos/altos abertos em achados-verificados.json.
  3. Existência e completude dos 13 mapas visuais HTML e do manual de montagem.

Critérios de Aceite:
  - Exit 0: Catálogo íntegro, nenhum achado crítico/alto aberto e mapas presentes.
  - Exit 1: Catálogo ausente/corrompido, achado crítico/alto aberto ou mapa faltante.
=============================================================================
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAIZ = next((p.parent for p in Path(__file__).resolve().parents if p.name == "modulos"), Path(__file__).resolve().parent.parent)  # raiz: pai de modulos/ (VSA) ou de gates/ (árvore sintética)

MAPAS_OBRIGATORIOS = [
    "manual-montagem-aidd.html",
    "mapa-00-indice.html",
    "mapa-01-leis.html",
    "mapa-02-ferramentas.html",
    "mapa-03-encaixes.html",
    "mapa-04-guardas.html",
    "mapa-05-skills.html",
    "mapa-06-comandos.html",
    "mapa-07-conexoes.html",
    "mapa-08-harnesses.html",
    "mapa-09-moldes.html",
    "mapa-10-scripts.html",
    "mapa-11-oficina.html",
    "mapa-12-lente15d.html",
]


def auditar_catalogo(caminho_catalogo: Path) -> List[str]:
    erros: List[str] = []
    if not caminho_catalogo.is_file():
        erros.append(f"Catálogo de peças não encontrado: {caminho_catalogo}")
        return erros

    try:
        dados = json.loads(caminho_catalogo.read_text(encoding="utf-8"))
    except Exception as e:
        erros.append(f"Erro ao decodificar JSON do catálogo {caminho_catalogo}: {e}")
        return erros

    for chave_esperada in ("versao", "gerado_por", "totais", "ferramentas", "skills", "leis", "encaixes"):
        if chave_esperada not in dados:
            erros.append(f"Catálogo incompleto: chave obrigatória '{chave_esperada}' ausente")

    totais = dados.get("totais", {})
    if not isinstance(totais, dict):
        erros.append("Catálogo inválido: seção 'totais' não é um dicionário")
        return erros

    for metrica in ("ferramentas", "skills", "leis"):
        if totais.get(metrica, 0) <= 0:
            erros.append(f"Catálogo inválido: métrica 'totais.{metrica}' menor ou igual a zero")

    if totais.get("encaixes_quebrados", 0) > 0:
        erros.append(f"Catálogo inválido: detectados {totais.get('encaixes_quebrados')} encaixes quebrados no ecossistema")

    return erros


def auditar_achados(caminho_achados: Path) -> List[str]:
    erros: List[str] = []
    if not caminho_achados.is_file():
        erros.append(f"Arquivo de achados verificados não encontrado: {caminho_achados}")
        return erros

    try:
        dados = json.loads(caminho_achados.read_text(encoding="utf-8"))
    except Exception as e:
        erros.append(f"Erro ao decodificar JSON de achados {caminho_achados}: {e}")
        return erros

    achados = dados.get("achados", [])
    if not isinstance(achados, list):
        erros.append("Campo 'achados' deve ser uma lista")
        return erros

    for item in achados:
        item_id = item.get("id", "SEM-ID")
        gravidade = str(item.get("gravidade", "")).lower()
        estado = str(item.get("estado", "")).lower()
        if gravidade in ("alta", "critica") and estado == "aberto":
            erros.append(f"Achado crítico/alto não resolvido: [{item_id}] {item.get('titulo')}")

    return erros


def auditar_mapas_visuais(pasta_mapas: Path) -> List[str]:
    erros: List[str] = []
    if not pasta_mapas.is_dir():
        erros.append(f"Diretório de mapas visuais não encontrado: {pasta_mapas}")
        return erros

    for mapa in MAPAS_OBRIGATORIOS:
        arquivo = pasta_mapas / mapa
        if not arquivo.is_file():
            erros.append(f"Mapa visual obrigatório ausente: {mapa}")
        else:
            try:
                conteudo = arquivo.read_text(encoding="utf-8", errors="replace")
                if len(conteudo.strip()) < 100 or "<html" not in conteudo.lower():
                    erros.append(f"Mapa visual inválido ou vazio: {mapa}")
            except Exception as e:
                erros.append(f"Erro ao ler mapa visual {mapa}: {e}")

    return erros


def auditar_tudo(
    caminho_catalogo: Optional[Path] = None,
    caminho_achados: Optional[Path] = None,
    pasta_mapas: Optional[Path] = None,
) -> Tuple[int, List[str]]:
    catalogo = caminho_catalogo or (RAIZ / "docs" / "auditoria" / "mapa-pecas" / "catalogo-pecas.json")
    achados = caminho_achados or (RAIZ / "docs" / "auditoria" / "mapa-pecas" / "ciclo-01" / "achados-verificados.json")
    mapas = pasta_mapas or (RAIZ / "docs" / "mapas-visuais")

    todos_erros: List[str] = []
    todos_erros.extend(auditar_catalogo(catalogo))
    todos_erros.extend(auditar_achados(achados))
    todos_erros.extend(auditar_mapas_visuais(mapas))

    codigo = 1 if todos_erros else 0
    return codigo, todos_erros


def main() -> int:
    parser = argparse.ArgumentParser(description="Quality Gate G_mapa_pecas (Lei #8 / Lei #13)")
    parser.add_argument("--catalogo", type=Path, default=None, help="Caminho do catalogo-pecas.json")
    parser.add_argument("--achados", type=Path, default=None, help="Caminho do achados-verificados.json")
    parser.add_argument("--mapas-dir", type=Path, default=None, help="Pasta dos mapas visuais")
    args = parser.parse_args()

    codigo, erros = auditar_tudo(args.catalogo, args.achados, args.mapas_dir)

    print("=" * 70)
    print(" [GATE] G_mapa_pecas — Integridade do Mapa de Peças e Catálogo Factual")
    print("=" * 70)

    if codigo == 0:
        print(" [SUCESSO] Quality Gate G_mapa_pecas APROVADO (100% OK)!")
        print("=" * 70)
        return 0

    print(" [FALHA] Quality Gate G_mapa_pecas REPROVADO!")
    for err in erros:
        print(f"  - {err}")
    print("=" * 70)
    return 1


if __name__ == "__main__":
    sys.exit(main())
