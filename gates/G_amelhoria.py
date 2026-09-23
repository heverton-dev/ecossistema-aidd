#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_amelhoria (D13 / DoD 3 / DoD 6)
=============================================================================
Quality Gate Determinístico de Rótulo Honesto para aidd-melhoria.
Valida estritamente a presença do rótulo honesto ("Sugestão de refatoração...")
e veta categoricamente afirmações imperativas ilusórias como "Refatoração concluída",
impedindo que análises pré-planejamento declarem execuções prematuras ou não realizadas.

Critérios de Aceite:
  1. Exit 0: Relatório contém rótulo honesto ("Sugestão de refatoração...") e nenhuma
             afirmação ilusória imperativa.
  2. Exit 1: Relatório contém termos ilusórios proibidos ("Refatoração concluída", etc.)
             ou omite a chancela honesta de sugestão.
=============================================================================
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PADROES_ILUSORIOS_PROIBIDOS = [
    re.compile(r"\brefatora[cç][aã]o\s+conclu[ií]da\b", re.IGNORECASE),
    re.compile(r"\brefatora[cç][aã]o\s+realizada\b", re.IGNORECASE),
    re.compile(r"\brefatora[cç][aã]o\s+finalizada\b", re.IGNORECASE),
    re.compile(r"\brefatorad[oa]\s+com\s+sucesso\b", re.IGNORECASE),
    re.compile(r"\bc[oó]digo\s+refatorado\b", re.IGNORECASE),
    re.compile(r"\bimplementa[cç][aã]o\s+conclu[ií]da\b", re.IGNORECASE),
    re.compile(r"\bcorre[cç][aã]o\s+conclu[ií]da\b", re.IGNORECASE),
]

PADRAO_ROTULO_HONESTO = re.compile(r"sugest[aã]o\s+de\s+refatora[cç][aã]o", re.IGNORECASE)


def extrair_textos_relatorio(dados: Union[Dict[str, Any], str]) -> List[str]:
    """Extrai todas as strings relevantes do relatório para validação."""
    textos: List[str] = []
    if isinstance(dados, str):
        textos.append(dados)
    elif isinstance(dados, dict):
        for chave, valor in dados.items():
            if isinstance(valor, str):
                textos.append(valor)
            elif isinstance(valor, list):
                for item in valor:
                    if isinstance(item, str):
                        textos.append(item)
                    elif isinstance(item, dict):
                        textos.extend(extrair_textos_relatorio(item))
            elif isinstance(valor, dict):
                textos.extend(extrair_textos_relatorio(valor))
    return textos


def validar_relatorio_conteudo(conteudo: Union[Dict[str, Any], str]) -> Tuple[bool, List[str]]:
    """
    Valida um conteúdo de relatório contra as regras de honestidade de rótulo.
    Retorna (aprovado, lista_de_mensagens).
    """
    textos = extrair_textos_relatorio(conteudo)
    texto_unificado = "\n".join(textos)

    erros: List[str] = []

    # 1. Checa termos imperativos ilusórios proibidos
    for padrao in PADROES_ILUSORIOS_PROIBIDOS:
        match = padrao.search(texto_unificado)
        if match:
            termo = match.group(0)
            erros.append(
                f"Rótulo Desonesto detectado: termo proibido '{termo}' presente. "
                "Violação da exigência de honestidade de rótulo (D13)."
            )

    # 2. Checa presença do rótulo honesto obrigatório
    if not PADRAO_ROTULO_HONESTO.search(texto_unificado):
        erros.append(
            "Rótulo Desonesto detectado: ausência do rótulo honesto obrigatório "
            "('Sugestão de refatoração...'). Violação da exigência de honestidade de rótulo (D13)."
        )

    if erros:
        return False, erros
    return True, ["APROVADO: Rótulo honesto validado com sucesso. EXIT 0"]


def validar_arquivo_relatorio(caminho: Union[str, Path]) -> Tuple[bool, List[str]]:
    """Lê e valida um arquivo de relatório (.json, .html ou texto)."""
    p = Path(caminho).resolve()
    if not p.is_file():
        return False, [f"Arquivo de relatório não encontrado: {p}"]

    try:
        texto = p.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return False, [f"Falha ao ler arquivo de relatório {p}: {exc}"]

    if p.suffix.lower() == ".json":
        try:
            dados = json.loads(texto)
            return validar_relatorio_conteudo(dados)
        except json.JSONDecodeError:
            return validar_relatorio_conteudo(texto)
    else:
        return validar_relatorio_conteudo(texto)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="G_amelhoria: Quality Gate Determinístico de Rótulo Honesto (D13)"
    )
    parser.add_argument(
        "--relatorio",
        "-r",
        dest="relatorio",
        default=None,
        help="Caminho do arquivo de relatório (.json ou .html) para validação",
    )
    parser.add_argument(
        "arquivos",
        nargs="*",
        default=[],
        help="Arquivos adicionais de relatório a inspecionar",
    )

    args = parser.parse_args(argv)

    alvos: List[Path] = []
    if args.relatorio:
        alvos.append(Path(args.relatorio))
    for arq in args.arquivos:
        alvos.append(Path(arq))

    if not alvos:
        docs_dir = Path("docs") / "melhorias"
        if docs_dir.is_dir():
            alvos.extend(sorted(docs_dir.glob("*.json")))

    if not alvos:
        print("[AVISO] Nenhum relatório especificado ou encontrado para auditoria.")
        return 0

    aprovado_geral = True
    for alvo in alvos:
        aprovado, msgs = validar_arquivo_relatorio(alvo)
        for msg in msgs:
            print(f"[{alvo.name}] {msg}")
        if not aprovado:
            aprovado_geral = False

    if aprovado_geral:
        print("[SUCESSO] Quality Gate G_amelhoria APROVADO. EXIT 0")
        return 0
    else:
        print("[ERRO] Quality Gate G_amelhoria REPROVADO por Rótulo Desonesto. EXIT 1")
        return 1


if __name__ == "__main__":
    sys.exit(main())
