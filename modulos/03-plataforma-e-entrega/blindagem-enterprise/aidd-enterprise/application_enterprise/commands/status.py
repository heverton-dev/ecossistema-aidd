# -*- coding: utf-8 -*-
"""Use Case: status — inspeção de saúde do ecossistema do projeto."""

import json
import os


def cmd_status(args):
    target_dir = os.path.abspath(getattr(args, "dir", "."))
    print("=" * 80)
    print(f"🔍 [AIDD STATUS] Inspecionando Saúde do Ecossistema em: {target_dir}")
    print("=" * 80)

    plano_path = os.path.join(target_dir, "PLANO-EXECUCAO-ESTRUTURADO.json")
    if os.path.exists(plano_path):
        with open(plano_path, "r", encoding="utf-8") as f:
            plano = json.load(f)
        proj = plano.get("projeto", {})
        print(f"Projeto:       {proj.get('nome')} (v{proj.get('versao')})")
        print(f"Framework:     {proj.get('framework')}")
        print(f"Status:        {proj.get('status')}")
    else:
        print("Manifesto PLANO-EXECUCAO-ESTRUTURADO.json: Não localizado")

    modules_dir = os.path.join(target_dir, "src", "modules")
    if os.path.exists(modules_dir):
        mods = [
            m for m in os.listdir(modules_dir)
            if os.path.isdir(os.path.join(modules_dir, m)) and not m.startswith("__")
        ]
        print(f"Módulos Ativos ({len(mods)}): {', '.join(mods)}")
    else:
        print("Módulos Ativos: 0 (src/modules não encontrado)")

    gates_dir = os.path.join(target_dir, "scripts", "gates")
    if os.path.exists(gates_dir):
        gates = [g for g in os.listdir(gates_dir) if g.endswith(".py")]
        print(f"Quality Gates  ({len(gates)}): {', '.join(gates)}")

    db_path = os.path.join(target_dir, "suite.db")
    if os.path.exists(db_path):
        size_kb = os.path.getsize(db_path) / 1024
        print(f"Banco SQLite:  Ativo ({size_kb:.1f} KB)")