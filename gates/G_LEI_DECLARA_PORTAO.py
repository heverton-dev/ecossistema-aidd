#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_LEI_DECLARA_PORTAO (ISSUE-0010)
=============================================================================
Meta-Quality Gate que audita e bloqueia se qualquer Lei Inviolável em AGENTS.md
não declarar explicitamente seu portão verificador ou a ausência deliberada dele,
junto com o nível de força de enforcement (provado, nao-provado, sem-gate).

Regra Canônica (ISSUE-0010):
  Cada lei invariante em AGENTS.md DEVE carregar uma linha de declaração:
  o portão verificador (ex: gates/G_*.py) ou o literal:
  "sem gate — cumprimento por convenção".
  Além disso, cada declaração carrega a força de enforcement:
  - provado: portão existe E possui teste de reprovação real (exit 1).
  - nao-provado: portão existe, mas carece de teste provando que morde.
  - sem-gate: ausência deliberada de portão; cumprimento por convenção.

Saída:
  exit 0 = Todas as leis declaram portão e força de forma consistente.
  exit 1 = Ao menos uma lei carece de declaração ou contém declaração inválida.
"""

import argparse
import os
import re
import sys
from typing import Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTS_FILE_DEFAULT = os.path.join(ROOT_DIR, "AGENTS.md")

# Regex para capturar itens numerados de leis: "1. **Determinism First:** ..."
RE_LAW_HEADER = re.compile(r"^(\d+)\.\s+\*\*(.+?)\*\*")

# Regex para linha de declaração de portão
# Aceita: "- Portão: <gate_ou_literal> (<força>)" ou com colchetes "[<força>]"
RE_GATE_DECLARATION = re.compile(
    r"^\s*-\s+(?:\*\*)?(?:Portão|Portao|Gate)(?:\*\*)?:\s+(?P<target>.+?)\s+(?:[\(\[])(?P<strength>[\w\-]+)(?:[\)\]])\s*$",
    re.IGNORECASE,
)

LITERAL_SEM_GATE = "sem gate — cumprimento por convenção"
VALID_STRENGTHS = {"provado", "nao-provado", "sem-gate"}


def normalizar_literal_sem_gate(texto: str) -> bool:
    """Aceita variações de traço (em-dash, en-dash, hífen)."""
    norm = texto.strip().replace("—", "-").replace("–", "-")
    esperado = LITERAL_SEM_GATE.replace("—", "-")
    return norm.lower() == esperado.lower()


def extrair_bloco_leis(conteudo: str) -> str:
    """Extrai o texto sob '## 2. Inviolable Laws' até a próxima seção de nível 2 ou separador."""
    match = re.search(r"##\s+2\.\s+Inviolable Laws.*?\n(.*?)(?=\n##\s+\d|\n---\s*\n\s*##|$)", conteudo, re.DOTALL)
    if not match:
        return ""
    return match.group(1)


def parse_leis_e_declaracoes(bloco_leis: str) -> List[Dict[str, any]]:
    """Analisa o bloco de leis e extrai cada número de lei com seu texto e declaração."""
    linhas = bloco_leis.splitlines()
    leis = []
    lei_atual: Optional[Dict[str, any]] = None

    for linha in linhas:
        header_match = RE_LAW_HEADER.match(linha.strip())
        if header_match:
            if lei_atual is not None:
                leis.append(lei_atual)
            num = int(header_match.group(1))
            titulo = header_match.group(2)
            lei_atual = {
                "numero": num,
                "titulo": titulo,
                "texto": linha.strip(),
                "declaracao": None,
                "raw_declaracao": None,
            }
            continue

        if lei_atual is not None:
            decl_match = RE_GATE_DECLARATION.match(linha)
            if decl_match:
                lei_atual["declaracao"] = {
                    "target": decl_match.group("target").strip(),
                    "strength": decl_match.group("strength").strip().lower(),
                }
                lei_atual["raw_declaracao"] = linha.strip()

    if lei_atual is not None:
        leis.append(lei_atual)

    return leis


def auditar_declaracoes_leis(agents_path: str = AGENTS_FILE_DEFAULT) -> Tuple[int, List[str]]:
    """Audita a declaração de portão para todas as leis em AGENTS.md."""
    if not os.path.isfile(agents_path):
        return 1, [f"Arquivo de governança não encontrado: {agents_path}"]

    try:
        with open(agents_path, "r", encoding="utf-8", errors="replace") as f:
            conteudo = f.read()
    except Exception as e:
        return 1, [f"Erro ao ler {agents_path}: {e}"]

    bloco = extrair_bloco_leis(conteudo)
    if not bloco.strip():
        return 1, ["Seção '## 2. Inviolable Laws' não encontrada ou vazia em AGENTS.md."]

    leis = parse_leis_e_declaracoes(bloco)
    if not leis:
        return 1, ["Nenhuma lei inviolável numerada encontrada na seção 2."]

    erros = []
    conformes = []

    for lei in leis:
        num = lei["numero"]
        titulo = lei["titulo"]
        decl = lei["declaracao"]

        if not decl:
            erros.append(f"Lei #{num} ({titulo}): Ausência de linha de declaração de portão.")
            continue

        target = decl["target"]
        strength = decl["strength"]

        if strength not in VALID_STRENGTHS:
            erros.append(
                f"Lei #{num} ({titulo}): Força '{strength}' inválida. Esperado: provado, nao-provado ou sem-gate."
            )
            continue

        # Caso sem gate
        if normalizar_literal_sem_gate(target):
            if strength != "sem-gate":
                erros.append(
                    f"Lei #{num} ({titulo}): Declara '{target}', portanto a força DEVE ser 'sem-gate', mas foi '{strength}'."
                )
            else:
                conformes.append((num, titulo, target, strength))
            continue

        # Caso com portão declarado
        gate_path = os.path.normpath(os.path.join(ROOT_DIR, target))
        if not os.path.isfile(gate_path):
            erros.append(f"Lei #{num} ({titulo}): Portão declarado não existe no disco: '{target}'.")
            continue

        if strength == "sem-gate":
            erros.append(
                f"Lei #{num} ({titulo}): Portão '{target}' existe, mas foi marcado como 'sem-gate'."
            )
            continue

        conformes.append((num, titulo, target, strength))

    return (0 if not erros else 1), erros, conformes, len(leis)


def main() -> int:
    parser = argparse.ArgumentParser(description="G_LEI_DECLARA_PORTAO: Auditoria de declarações de portões por lei.")
    parser.add_argument("--agents-file", default=AGENTS_FILE_DEFAULT, help="Caminho alternativo para AGENTS.md")
    args = parser.parse_args()

    print("=" * 72)
    print(" [GATE] G_LEI_DECLARA_PORTAO — Inventário de Portões por Lei (ISSUE-0010)")
    print("=" * 72)

    res = auditar_declaracoes_leis(args.agents_file)
    if len(res) == 2:
        code, erros = res
        print(f"[ERRO CRÍTICO] {erros[0]}")
        return code

    code, erros, conformes, total_leis = res

    print(f"[AUDITORIA] Total de Leis Analisadas: {total_leis}\n")
    for num, titulo, target, strength in conformes:
        print(f"  [OK] Lei #{num:02d} | {titulo:<32} -> {target} [{strength}]")

    if erros:
        print("\n" + "=" * 72)
        print(f" [FALHA] {len(erros)} violação(ões) de declaração detectada(s) (ISSUE-0010):")
        print("=" * 72)
        for err in erros:
            print(f"  [VIOLAÇÃO] {err}")
        print("\n" + "=" * 72)
        print(" REGRA CANÔNICA VIOLADA (ISSUE-0010):")
        print(" Toda lei inviolável em AGENTS.md deve declarar explicitamente seu")
        print(" portão verificador ou 'sem gate — cumprimento por convenção' com sua")
        print(" respectiva força de enforcement: provado, nao-provado ou sem-gate.")
        print("=" * 72)
        return 1

    print("\n" + "=" * 72)
    print(f" [SUCESSO] 100% das {total_leis} Leis Invioláveis possuem declaração conforme!")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
