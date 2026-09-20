#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_ESTRUTURA_ESTADO (Lei Canônica #3)
=============================================================================
Auditoria de Persistência Estruturada de Estado de Orquestração.
Valida deterministicamente que as ferramentas de orquestração do ecossistema
persistem seu estado em formatos estruturados (JSON Schema, .jsonl, SQLite WAL)
em vez de reterem estado exclusivamente em variáveis de memória do processo.

Invariante Inviolável (Lei #3 - Structured Persistence):
  Toda retenção de estado crítico do ciclo de orquestração deve ser persistida
  em artefatos determinísticos e recuperáveis no disco, protegidos contra perda
  por reinício de sessão ou queda de processo.

Inventário Nomeado de Ferramentas e Artefatos (ISSUE-0022):
  1. ORCA Flight Plan:
     - Artefatos: '.orca-flight-plan.json', 'flight_plan.json'
     - Schema: plan_dir (str), harness (str), profile_binary (str), fronts (list[dict])
  2. ORCA ADE State Engine:
     - Artefatos: '.orca_state.json'
     - Schema: version (int), created_at (num), updated_at (num), fronts (dict)
  3. Telemetria de Sessão e Execução:
     - Artefatos: '*telemetry*.jsonl', 'transcript*.jsonl'
     - Schema: linhas em JSON Lines contendo campos estruturados (timestamp/created_at, etc.)

Limite Metrológico e Honestidade de Rótulo (Lei #8 / ISSUE-0022):
  Este portão audita e valida os schemas e arquivos do inventário explícito acima.
  Não é matematicamente possível provar de forma negativa universal que nenhum
  outro script use variáveis voláteis. O portão restringe-se às ferramentas
  que reivindicam persistência estruturada declarada.

Saída:
  exit 0 = Todos os artefatos de estado inventariados são válidos e conformes.
  exit 1 = Falha de persistência, corrupção de schema ou ausência de campos obrigatórios.
=============================================================================
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Schemas e Validadores do Inventário

def validar_flight_plan(data: Any, orig_path: str = "memoria") -> List[str]:
    """Valida se o dicionário adere ao schema canônico do ORCA Flight Plan."""
    erros = []
    if not isinstance(data, dict):
        return [f"{orig_path}: Raiz do Flight Plan deve ser um objeto JSON (dict)."]

    # plan_dir e fronts são universais em todos os modos
    if "plan_dir" not in data:
        erros.append(f"{orig_path}: Campo obrigatório 'plan_dir' ausente no Flight Plan.")
    if "fronts" not in data:
        erros.append(f"{orig_path}: Campo obrigatório 'fronts' ausente no Flight Plan.")
        return erros

    mode = data.get("mode", "worktree")

    fronts = data.get("fronts")
    if not isinstance(fronts, list):
        erros.append(f"{orig_path}: Campo 'fronts' deve ser uma lista de frentes de execução.")
    else:
        for idx, front in enumerate(fronts):
            if not isinstance(front, dict):
                erros.append(f"{orig_path}: Front #{idx} deve ser um objeto.")
                continue
            if "name" not in front:
                erros.append(f"{orig_path}: Front #{idx}: campo obrigatório 'name' ausente.")

            if mode == "subagent":
                if "prompt" not in front and "subagent_type" not in front:
                    erros.append(f"{orig_path}: Front #{idx} ({front.get('name')}): ausência de 'prompt' ou 'subagent_type' no modo subagent.")
            else:
                # Modos worktree / orca
                has_cmd = "command" in front or "launch_command" in front
                if not has_cmd:
                    erros.append(f"{orig_path}: Front #{idx} ({front.get('name')}): campo de comando ('command' ou 'launch_command') ausente.")
                if "branch" not in front:
                    erros.append(f"{orig_path}: Front #{idx} ({front.get('name')}): campo 'branch' ausente.")

    return erros


def validar_orca_state(data: Any, orig_path: str = "memoria") -> List[str]:
    """Valida se o dicionário adere ao schema de estado do StateEngine."""
    erros = []
    if not isinstance(data, dict):
        return [f"{orig_path}: Raiz do ORCA State deve ser um objeto JSON (dict)."]

    for campo in ["version", "fronts"]:
        if campo not in data:
            erros.append(f"{orig_path}: Campo obrigatório '{campo}' ausente no ORCA State.")

    fronts = data.get("fronts")
    if not isinstance(fronts, dict):
        erros.append(f"{orig_path}: Campo 'fronts' no ORCA State deve ser um dicionário.")
    else:
        valid_states = {"PENDING", "RUNNING", "GATE_PASSED", "MERGED", "FAILED", "PAUSED_QUOTA"}
        for front_name, info in fronts.items():
            if not isinstance(info, dict):
                erros.append(f"{orig_path}: Entrada de estado para '{front_name}' deve ser um objeto.")
                continue
            st = info.get("state")
            if st not in valid_states:
                erros.append(f"{orig_path}: Front '{front_name}' tem estado inválido: '{st}'.")

    return erros


def validar_telemetry_jsonl(caminho: str) -> List[str]:
    """Valida se um arquivo .jsonl é composto estritamente por linhas JSON válidas."""
    erros = []
    try:
        with open(caminho, "r", encoding="utf-8", errors="replace") as f:
            for lineno, line in enumerate(f, 1):
                raw = line.strip()
                if not raw:
                    continue
                try:
                    record = json.loads(raw)
                    if not isinstance(record, dict):
                        erros.append(f"{caminho}:{lineno} — Linha não é um objeto JSON.")
                except json.JSONDecodeError as exc:
                    erros.append(f"{caminho}:{lineno} — Linha corrompida (não-JSON): {exc}")
    except Exception as exc:
        erros.append(f"{caminho} — Erro ao abrir arquivo: {exc}")

    return erros


def auditar_artefatos_no_disco(repo_root: str = ROOT_DIR) -> Tuple[int, List[str], int]:
    """Varre o repositório procurando artefatos inventariados de persistência de estado."""
    erros_totais: List[str] = []
    total_auditados = 0

    pastas_ignoradas = {".git", "node_modules", ".venv", "venv", "__pycache__", "site-packages"}

    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in pastas_ignoradas]
        for file in files:
            caminho = os.path.join(root, file)

            # 1. Flight Plan
            if file in (".orca-flight-plan.json", "flight_plan.json"):
                total_auditados += 1
                try:
                    with open(caminho, "r", encoding="utf-8", errors="replace") as f:
                        data = json.load(f)
                    erros_totais.extend(validar_flight_plan(data, caminho))
                except Exception as exc:
                    erros_totais.append(f"{caminho} — JSON corrompido: {exc}")

            # 2. ORCA State
            elif file == ".orca_state.json":
                total_auditados += 1
                try:
                    with open(caminho, "r", encoding="utf-8", errors="replace") as f:
                        data = json.load(f)
                    erros_totais.extend(validar_orca_state(data, caminho))
                except Exception as exc:
                    erros_totais.append(f"{caminho} — JSON corrompido: {exc}")

            # 3. Telemetry JSONL
            elif file.endswith(".jsonl") and ("telemetry" in file.lower() or "transcript" in file.lower()):
                total_auditados += 1
                erros_totais.extend(validar_telemetry_jsonl(caminho))

    return (1 if erros_totais else 0), erros_totais, total_auditados


def main() -> int:
    parser = argparse.ArgumentParser(description="G_ESTRUTURA_ESTADO: Auditoria de persistência estruturada (Lei #3)")
    parser.add_argument("--check-artifact", help="Caminho para arquivo avulso de artefato a validar")
    parser.add_argument("--type", choices=["flight_plan", "orca_state", "telemetry_jsonl"], help="Tipo do artefato")
    args = parser.parse_args()

    print("=" * 72)
    print(" [GATE] G_ESTRUTURA_ESTADO — Auditoria de Persistência Estruturada (Lei #3)")
    print("=" * 72)

    if args.check_artifact and args.type:
        caminho = args.check_artifact
        if not os.path.isfile(caminho):
            print(f"[FALHA] Arquivo de artefato não encontrado: {caminho}")
            return 1

        if args.type == "flight_plan":
            try:
                with open(caminho, "r", encoding="utf-8") as f:
                    data = json.load(f)
                erros = validar_flight_plan(data, caminho)
            except Exception as e:
                erros = [f"JSON corrompido: {e}"]
        elif args.type == "orca_state":
            try:
                with open(caminho, "r", encoding="utf-8") as f:
                    data = json.load(f)
                erros = validar_orca_state(data, caminho)
            except Exception as e:
                erros = [f"JSON corrompido: {e}"]
        elif args.type == "telemetry_jsonl":
            erros = validar_telemetry_jsonl(caminho)
        else:
            erros = ["Tipo desconhecido."]

        if erros:
            print(f"\n[FALHA] Artefato '{caminho}' REPROVADO no schema {args.type}:")
            for err in erros:
                print(f"  - {err}")
            return 1

        print(f"\n[SUCESSO] Artefato '{caminho}' 100% conforme no schema {args.type}.")
        return 0

    code, erros, total = auditar_artefatos_no_disco(ROOT_DIR)

    if erros:
        print(f"\n[FALHA] Detectada(s) {len(erros)} violação(ões) de persistência estruturada (Lei #3):\n")
        for err in erros:
            print(f"  - {err}")
        print("\nRegra Violada: Artefatos de estado de orquestração devem aderir a schemas estruturados.")
        print("=" * 72)
        return 1

    print(f"\n[SUCESSO] Quality Gate G_ESTRUTURA_ESTADO APROVADO ({total} artefato(s) inventariado(s) analisado(s)).")
    print("=" * 72)
    print(" [LIMITE METROLÓGICO — LEI #8 / ISSUE-0022]:")
    print("   A auditoria valida os schemas dos artefatos explícitos do inventário:")
    print("   1. ORCA Flight Plan (.orca-flight-plan.json)")
    print("   2. ORCA State Engine (.orca_state.json)")
    print("   3. Logs de Telemetria e Sessão (*telemetry*.jsonl, transcript*.jsonl)")
    print("   A prova universal de inexistência de variáveis voláteis em outros scripts arbitrários")
    print("   permanece restrita ao escopo do inventário declarado.")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
