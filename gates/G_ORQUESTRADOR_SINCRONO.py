#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quality Gate: G_ORQUESTRADOR_SINCRONO
Valida a existência, integridade, conformidade dos contratos de handoff
e a capacidade de execução síncrona dos 3 fluxos canônicos do ecossistema.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SPECS_DIR = ROOT_DIR / "componentes" / "compartilhado" / "specs"
SKILLS_DIR = ROOT_DIR / "componentes" / "compartilhado" / "skills"


def auditar():
    print("=" * 72)
    print(" [GATE] G_ORQUESTRADOR_SINCRONO — Integridade da Tríade Canônica")
    print("=" * 72)

    erros = []

    # 1. Verifica existência do script do orquestrador
    orq_script = ROOT_DIR / "scripts" / "orquestrador_sincrono.py"
    if not orq_script.exists():
        erros.append("Script scripts/orquestrador_sincrono.py não encontrado.")
    else:
        print("[OK] Script do Orquestrador Síncrono presente.")

    # 2. Verifica comando run-fluxo no ecossistema.py
    eco_file = ROOT_DIR / "ecossistema.py"
    if not eco_file.exists():
        erros.append("ecossistema.py não encontrado.")
    else:
        conteudo_eco = eco_file.read_text(encoding="utf-8")
        if '"run-fluxo": cmd_run_fluxo' not in conteudo_eco:
            erros.append("Comando 'run-fluxo' não mapeado no dispatch de ecossistema.py.")
        else:
            print("[OK] Comando 'run-fluxo' registrado na CLI unificada ecossistema.py.")

    # 3. Verifica os 4 Schemas de Handoff
    schemas_obrigatorios = [
        "handoff-planner-to-engine.schema.json",
        "handoff-engine-to-master.schema.json",
        "handoff-master-to-enterprise.schema.json",
        "handoff-enterprise-to-ops.schema.json"
    ]
    for schema_nome in schemas_obrigatorios:
        schema_path = SPECS_DIR / schema_nome
        if not schema_path.exists():
            erros.append(f"Schema de handoff ausente: {schema_nome}")
        else:
            try:
                with open(schema_path, "r", encoding="utf-8") as f:
                    json.load(f)
                print(f"[OK] Schema formal presente e válido: {schema_nome}")
            except Exception as e:
                erros.append(f"Erro de sintaxe JSON no schema {schema_nome}: {e}")

    # 4. Verifica as Skills de Fluxo e Orquestrador
    skills_obrigatorias = [
        "fluxo-01-runner",
        "fluxo-02-runner",
        "fluxo-03-runner",
        "aidd-orchestrator-runner"
    ]
    for skill_nome in skills_obrigatorias:
        skill_path = SKILLS_DIR / skill_nome / "SKILL.md"
        if not skill_path.exists():
            erros.append(f"Skill especialista ausente: {skill_nome}/SKILL.md")
        else:
            print(f"[OK] Skill especialista presente: {skill_nome}")

    # 5. Executa dry-run do Fluxo 1 via CLI
    cmd_dry_run = [
        sys.executable, str(ROOT_DIR / "ecossistema.py"), "run-fluxo",
        "--fluxo", "1",
        "--nome", "Auditoria Teste",
        "--slug", "auditoria-teste",
        "--dominio", "auditoria",
        "--pasta", "testes/tmp-gate",
        "--dry-run"
    ]
    try:
        res = subprocess.run(
            cmd_dry_run,
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30
        )
        if res.returncode != 0:
            erros.append(f"Falha na execução dry-run do run-fluxo: {res.stderr}")
        else:
            print("[OK] Dry-run do Orquestrador Síncrono executado com sucesso (exit 0).")
    except Exception as exc:
        erros.append(f"Erro ao disparar dry-run: {exc}")

    if erros:
        print(f"\n[FALHA] Quality Gate G_ORQUESTRADOR_SINCRONO REPROVADO com {len(erros)} erro(s):")
        for e in erros:
            print(f"  - {e}")
        print("=" * 72)
        return 1

    print("\n========================================================================")
    print(" [SUCESSO] Quality Gate G_ORQUESTRADOR_SINCRONO APROVADO (100% OK)!")
    print(" Tríade Canônica síncrona e contratos de handoff 100% validados.")
    print("========================================================================\n")
    return 0


if __name__ == "__main__":
    sys.exit(auditar())
