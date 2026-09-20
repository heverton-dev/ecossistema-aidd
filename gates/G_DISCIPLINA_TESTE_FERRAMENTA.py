#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_DISCIPLINA_TESTE_FERRAMENTA (Lei Canônica #9)
=============================================================================
Auditoria de Disciplina de Teste e Validação de Ferramentas.
Valida deterministicamente o cumprimento do ciclo de 5 passos definido em
docs/protocolos/PROTOCOLO-TESTES-FERRAMENTAS.md, bloqueando commits que alterem
ferramentas sob tools/<ferramenta>/ sem a correspondente atualização do relatório
de teste end-to-end em docs/teste-end-to-end/.

Invariante Inviolável (Lei #9 - Tool Testing Discipline):
  Toda modificação de código, correção de bugs ou evolução de ferramenta em tools/
  deve seguir estritamente o ciclo de 5 passos:
  1. Auto-correção de bugs até 100% de conformidade.
  2. Commit e push no repositório.
  3. Limpeza cirúrgica do projeto alvo.
  4. Execução correta e limpa.
  5. Atualização obrigatória do relatório dinâmico em docs/teste-end-to-end/.

Regras de Auditoria (ISSUE-0023):
  1. Identificação de Alvo: Verifica se o changeset toca arquivos sob 'tools/<nome>/'.
  2. Condição de Bloqueio: Se qualquer ferramenta for alterada, exige que ao menos um
     relatório sob 'docs/teste-end-to-end/' seja atualizado no mesmo changeset ou
     possua data/timestamp contemporâneo à modificação da ferramenta.

Saída:
  exit 0 = Nenhuma ferramenta tocada OU ferramenta tocada com relatório atualizado.
  exit 1 = Ferramenta em tools/ alterada sem atualização do relatório em docs/teste-end-to-end/.
=============================================================================
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Set, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(ROOT_DIR, "docs", "teste-end-to-end")


def obter_arquivos_alterados(explicit_files: List[str] | None = None) -> List[str]:
    """Obtém a lista de arquivos alterados (staged, working tree ou lista explícita)."""
    if explicit_files:
        return [f.replace("\\", "/") for f in explicit_files]

    # 1. Tenta git diff --cached (staged files)
    res_staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
        cwd=ROOT_DIR,
        encoding="utf-8",
        errors="replace",
    )
    staged = [line.strip().replace("\\", "/") for line in res_staged.stdout.splitlines() if line.strip()]
    if staged:
        return staged

    # 2. Tenta git status --porcelain
    res_status = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        cwd=ROOT_DIR,
        encoding="utf-8",
        errors="replace",
    )
    status_files = []
    for line in res_status.stdout.splitlines():
        if len(line) > 3:
            path = line[3:].strip().replace("\\", "/")
            if " -> " in path:
                path = path.split(" -> ")[1].strip()
            status_files.append(path)
    if status_files:
        return status_files

    # 3. Fallback: último commit (git diff HEAD~1 --name-only)
    res_head = subprocess.run(
        ["git", "diff", "HEAD~1", "--name-only"],
        capture_output=True,
        text=True,
        cwd=ROOT_DIR,
        encoding="utf-8",
        errors="replace",
    )
    head_files = [line.strip().replace("\\", "/") for line in res_head.stdout.splitlines() if line.strip()]
    return head_files


def extrair_ferramentas_tocadas(arquivos: List[str]) -> Set[str]:
    """Extrai os nomes das ferramentas sob tools/<nome>/ que foram tocadas."""
    ferramentas = set()
    for f in arquivos:
        norm = f.strip().replace("\\", "/")
        if norm.startswith("tools/"):
            partes = norm.split("/")
            if len(partes) >= 2 and partes[1]:
                # Ignora arquivos soltos diretamente na raiz de tools/ se houver
                ferramenta = partes[1]
                ferramentas.add(ferramenta)
    return ferramentas


def tem_relatorio_atualizado(arquivos: List[str]) -> bool:
    """Verifica se algum relatório sob docs/teste-end-to-end/ está na lista de arquivos alterados."""
    for f in arquivos:
        norm = f.strip().replace("\\", "/")
        if norm.startswith("docs/teste-end-to-end/") and norm.endswith(".md"):
            return True
    return False


def auditar_disciplina(arquivos_alterados: List[str]) -> Tuple[int, List[str], Set[str]]:
    """Audita se mudanças em ferramentas são acompanhadas de relatório de teste atualizado."""
    ferramentas = extrair_ferramentas_tocadas(arquivos_alterados)
    if not ferramentas:
        return 0, [], set()

    relatorio_presente = tem_relatorio_atualizado(arquivos_alterados)
    if relatorio_presente:
        return 0, [], ferramentas

    erros = [
        f"Ferramenta(s) alterada(s) sem atualização de relatório: {', '.join(sorted(ferramentas))}.",
        "Regra Obrigatória (Lei #9 & PROTOCOLO-TESTES-FERRAMENTAS.md Passo 5):",
        "Toda alteração sob tools/<ferramenta>/ requer a atualização do relatório",
        "dinâmico de teste correspondente em docs/teste-end-to-end/relatorio-teste-end-to-end.md",
    ]
    return 1, erros, ferramentas


def main() -> int:
    parser = argparse.ArgumentParser(
        description="G_DISCIPLINA_TESTE_FERRAMENTA: Auditoria do ciclo de testes per Lei #9"
    )
    parser.add_argument("--files", nargs="*", help="Lista explícita de arquivos modificados para validar")
    args = parser.parse_args()

    print("=" * 72)
    print(" [GATE] G_DISCIPLINA_TESTE_FERRAMENTA — Disciplina de Teste (Lei #9)")
    print("=" * 72)

    arquivos = obter_arquivos_alterados(args.files)
    code, erros, ferramentas = auditar_disciplina(arquivos)

    if code != 0:
        print(f"\n[FALHA] Violação da Lei #9 (Tool Testing Discipline) detectada:\n")
        for err in erros:
            print(f"  {err}")
        print("\n" + "=" * 72)
        print(" [AÇÃO NECESSÁRIA]: Atualize o relatório em docs/teste-end-to-end/ antes do commit.")
        print("=" * 72)
        return 1

    if ferramentas:
        print(f"\n[SUCESSO] Quality Gate APROVADO: Ferramenta(s) {sorted(ferramentas)} com relatório atualizado.")
    else:
        print("\n[SUCESSO] Quality Gate APROVADO: Nenhuma ferramenta em tools/ alterada neste changeset.")

    print("=" * 72)
    print(" [LIMITE METROLÓGICO — LEI #8 / ISSUE-0023]:")
    print("   O portão audita deterministicamente a presença de relatório atualizado em")
    print("   docs/teste-end-to-end/ para todo commit que modifique caminhos sob tools/<nome>/.")
    print("   A validade substancial dos resultados empíricos do relatório permanece sujeita")
    print("   à integridade metrológica dos testes reais de cada ferramenta.")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
