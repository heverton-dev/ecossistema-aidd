# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_COMPONENTE_AGNOSTICO
=============================================================================
Audita se todo componente novo ou modificado (detectado via git diff / status)
possui cobertura completa em todas as pastas de harness exigidas pelo
manifesto canonico (gates/manifesto_harnesses.json).

Identifica componentes tocados sob:
  - componentes/<escopo>/<pasta_fonte>/<nome>/...
  - <harness>/skills/<nome>/...
  - <harness>/commands/<nome>...
e valida que cada um possui presenca fisica e conteudo identico em todos os
destinos exigidos pelo manifesto unico.

Uso:
  python gates/G_COMPONENTE_AGNOSTICO.py [--base <commit_ref>] [--todos]
      exit 0 = todos os componentes tocados estao 100% conformes com o manifesto.
      exit 1 = algum componente tocado esta ausente em algum harness ou diverge.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT_DIR, "scripts"))
import gestor_componentes

MANIFESTO_PATH = os.path.join(ROOT_DIR, "gates", "manifesto_harnesses.json")


def _obter_arquivos_tocados(base: str | None = None) -> list[str]:
    """Coleta caminhos relativos de arquivos tocados (staged, uncommitted, untracked ou diff contra base)."""
    arquivos: set[str] = set()

    # 1. git diff contra base ou HEAD
    ref = base if base else "HEAD"
    try:
        proc = subprocess.run(
            ["git", "diff", "--name-only", ref],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0:
            for linha in proc.stdout.splitlines():
                if linha.strip():
                    arquivos.add(linha.strip().replace("/", os.sep))
    except Exception:
        pass

    # 2. git status --porcelain (captura working tree e untracked)
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0:
            for linha in proc.stdout.splitlines():
                if len(linha) > 3:
                    caminho = linha[3:].strip().replace("/", os.sep)
                    # Tratamento para renomeacoes "R old -> new"
                    if " -> " in caminho:
                        caminho = caminho.split(" -> ")[1].strip()
                    arquivos.add(caminho)
    except Exception:
        pass

    return sorted(arquivos)


def _mapear_pasta_fonte_para_tipo(manifesto: dict) -> dict[str, str]:
    mapping = {}
    for tipo, cfg in manifesto["tipos_componente"].items():
        mapping[cfg["pasta_fonte"]] = tipo
    return mapping


def _detectar_componentes_tocados(arquivos: list[str], manifesto: dict) -> set[tuple[str, str]]:
    """Retorna conjunto de (tipo, ferramenta) para componentes tocados."""
    pasta_para_tipo = _mapear_pasta_fonte_para_tipo(manifesto)
    componentes_detectados: set[tuple[str, str]] = set()

    for caminho_rel in arquivos:
        partes = caminho_rel.split(os.sep)
        if not partes:
            continue

        # Caso 1: sob componentes/<escopo>/<pasta_fonte>/<nome>
        if partes[0] == "componentes" and len(partes) >= 3:
            escopo = partes[1]
            pasta_fonte = partes[2]
            if pasta_fonte in pasta_para_tipo and escopo in manifesto["escopos"]:
                tipo = pasta_para_tipo[pasta_fonte]
                componentes_detectados.add((tipo, escopo))
                continue

        # Caso 2: alteracao direta em pastas de harness (.claude, .agent, .gemini, skills)
        # Ex: .claude/skills/minha-skill/SKILL.md ou skills/minha-skill/SKILL.md
        for idx, parte in enumerate(partes):
            if parte in ("skills", "commands"):
                tipo = "skill" if parte == "skills" else "command"
                # Identifica se eh compartilhado (raiz) ou de tools/*
                escopo = "compartilhado"
                if len(partes) > 1 and partes[0] == "tools" and partes[1] in manifesto["escopos"]:
                    escopo = partes[1]
                componentes_detectados.add((tipo, escopo))

    return componentes_detectados


def auditar(base: str | None = None, todos: bool = False) -> int:
    print("=" * 70)
    print(" [GATE] G_COMPONENTE_AGNOSTICO — Cobertura Multi-Harness de Componentes")
    print("=" * 70)

    manifesto = gestor_componentes.carregar_manifesto()
    arquivos_tocados = _obter_arquivos_tocados(base)
    componentes_tocados = _detectar_componentes_tocados(arquivos_tocados, manifesto)

    erros: list[str] = []

    if todos or not componentes_tocados:
        modo = "completa (todos os componentes)" if todos else "global (nenhum componente especifico no diff)"
        print(f"\n--- Verificacao {modo} ---")
        total, problemas = gestor_componentes.verify("todos")
        print(f"Componentes verificados: {total}")
        if problemas:
            for p in problemas:
                erros.append(p)
                print(f"[ERRO] {p}")
        else:
            print("[OK] Todos os componentes cumprem 100% de cobertura multi-harness.")
    else:
        print(f"\n--- Verificando {len(componentes_tocados)} tipo(s)/escopo(s) tocado(s) no diff ---")
        for tipo, escopo in sorted(componentes_tocados):
            print(f"Auditando [{tipo}] em escopo '{escopo}'...")
            total, problemas = gestor_componentes.verify(tipo=tipo, ferramenta=escopo)
            print(f"  Componentes verificados: {total}")
            if problemas:
                for p in problemas:
                    erros.append(p)
                    print(f"  [ERRO] {p}")
            else:
                print(f"  [OK] Cobertura multi-harness completa para [{tipo}/{escopo}].")

    print("\n" + "=" * 70)
    if erros:
        print(f" [FALHA] Quality Gate REPROVADO com {len(erros)} erro(s) de distribuicao:")
        for err in erros:
            print(f"  - {err}")
        print("\nExecute: python ecossistema.py components sync --tipo <tipo> [--ferramenta <nome>]")
        print("=" * 70)
        return 1

    print(" [SUCESSO] Quality Gate G_COMPONENTE_AGNOSTICO APROVADO (100% OK)!")
    print("=" * 70)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="G_COMPONENTE_AGNOSTICO")
    parser.add_argument("--base", default=None, help="Commit base para o git diff (padrao: HEAD)")
    parser.add_argument("--todos", action="store_true", help="Audita todos os componentes incondicionalmente")
    args = parser.parse_args(argv)
    return auditar(base=args.base, todos=args.todos)


if __name__ == "__main__":
    sys.exit(main())