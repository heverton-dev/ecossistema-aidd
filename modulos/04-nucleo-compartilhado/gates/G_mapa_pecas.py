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
  3. Conteúdo de cada mapa visual oficial (técnico e não técnico, lista de
     MAPAS_PREVISTOS em scripts/mapa_visual.py) idêntico, byte a byte, ao que o
     gerador monta do catálogo, e presença do manual de montagem.

Critérios de Aceite:
  - Exit 0: Catálogo íntegro (listas cheias, totais batendo), nenhum achado
    crítico/alto aberto e mapas iguais ao que o gerador monta.
  - Exit 1: Catálogo ausente/corrompido/vazio, achado crítico/alto aberto, mapa
    faltante ou mapa com conteúdo diferente do gerado.
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

sys.path.insert(0, str(RAIZ / "scripts"))
import catalogo_pecas as cp  # noqa: E402  (caminho do catálogo declarado uma vez: cp.SAIDA_PADRAO)
import mapa_visual as mv  # noqa: E402  (mesma montagem do --check: fonte única da regra)
import compilar_mapas_nao_tecnicos as nt  # noqa: E402

MANUAL = mv.MANUAL
# Listas que um catálogo de verdade nunca tem vazias (F2: catálogo de listas vazias aprovava).
LISTAS_OBRIGATORIAS = ("ferramentas", "skills", "leis", "encaixes", "gates")
# totais.<chave> que não têm o mesmo nome da lista que contam.
TOTAIS_DE_OUTRA_LISTA = {"gates_nomes": "gates"}


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

    for chave in LISTAS_OBRIGATORIAS:
        if not isinstance(dados.get(chave), list) or not dados[chave]:
            erros.append(f"Catálogo inválido: lista '{chave}' vazia ou ausente")

    for chave, valor in sorted(totais.items()):
        lista = dados.get(TOTAIS_DE_OUTRA_LISTA.get(chave, chave))
        if isinstance(lista, list) and valor != len(lista):
            erros.append(f"Catálogo inválido: totais.{chave} = {valor}, mas a lista tem {len(lista)} itens")

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


def mapas_esperados(catalogo: dict) -> List[Tuple[str, str]]:
    """(caminho relativo à pasta dos mapas, texto que o gerador monta) de cada mapa oficial,
    nas duas versões, com o índice e os tipos de MAPAS_PREVISTOS."""
    pares = []
    for tipo in ("indice", *(t for t, _, _ in mv.MAPAS_PREVISTOS)):
        nome = mv.arquivo_mapa(tipo)
        pares.append((nome, mv.montar(tipo, catalogo, MANUAL, False)))
        pares.append((f"nao-tecnicos/{nome}", nt.compilar_nao_tecnico(tipo, catalogo)))
    return pares


def auditar_mapas_visuais(pasta_mapas: Path, caminho_catalogo: Optional[Path] = None) -> List[str]:
    erros: List[str] = []
    if not pasta_mapas.is_dir():
        erros.append(f"Diretório de mapas visuais não encontrado: {pasta_mapas}")
        return erros
    if not (pasta_mapas / MANUAL).is_file():
        erros.append(f"Mapa visual obrigatório ausente: {MANUAL}")

    caminho_catalogo = caminho_catalogo or mv.CATALOGO
    try:
        catalogo = json.loads(caminho_catalogo.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return erros + [f"Sem catálogo legível para conferir os mapas ({caminho_catalogo}): {e}"]

    # O índice mostra o estado de cada mapa na pasta conferida, não na pasta oficial.
    mapas_originais, catalogo_original = mv.MAPAS, mv.CATALOGO
    mv.MAPAS, mv.CATALOGO = pasta_mapas, caminho_catalogo
    try:
        esperados = mapas_esperados(catalogo)
    except (KeyError, OSError, ValueError) as e:
        return erros + [f"Gerador não monta os mapas a partir de {caminho_catalogo}: {e}"]
    finally:
        mv.MAPAS, mv.CATALOGO = mapas_originais, catalogo_original

    for rel, texto in esperados:
        arquivo = pasta_mapas / rel
        if not arquivo.is_file():
            erros.append(f"Mapa visual obrigatório ausente: {rel}")
        elif arquivo.read_bytes() != texto.encode("utf-8"):
            erros.append(f"Mapa visual {rel} difere do que o mapa_visual monta do catálogo. "
                         f"Rode: python scripts/mapa_visual.py <tipo>")
    return erros


def auditar_tudo(
    caminho_catalogo: Optional[Path] = None,
    caminho_achados: Optional[Path] = None,
    pasta_mapas: Optional[Path] = None,
) -> Tuple[int, List[str]]:
    catalogo = caminho_catalogo or cp.SAIDA_PADRAO
    achados = caminho_achados or (RAIZ / "docs" / "auditoria" / "mapa-pecas" / "ciclo-01" / "achados-verificados.json")
    mapas = pasta_mapas or (RAIZ / "docs" / "mapas-visuais")

    todos_erros: List[str] = []
    todos_erros.extend(auditar_catalogo(catalogo))
    todos_erros.extend(auditar_achados(achados))
    todos_erros.extend(auditar_mapas_visuais(mapas, catalogo))

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
