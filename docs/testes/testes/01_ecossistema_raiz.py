# -*- coding: utf-8 -*-
"""
Bateria 1 — Orquestração Raiz (ecossistema.py + Meta-Quality Gates)
Executa de forma determinística os 7 itens da Definição de Pronto, capturando
exit codes, tempos de execução, saídas brutas e validações de integridade.
"""

import json
import os
import subprocess
import sys
import time

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

def run_cmd(cmd_list, cwd=ROOT_DIR, env=None):
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    t0 = time.time()
    p = subprocess.run(
        cmd_list,
        cwd=cwd,
        env=merged_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    dt = time.time() - t0
    return {
        "cmd": " ".join(cmd_list),
        "returncode": p.returncode,
        "stdout": p.stdout,
        "stderr": p.stderr,
        "duration_sec": round(dt, 3)
    }

def main():
    print(f"=== INICIANDO BATERIA 1 — ECOSSISTEMA RAIZ EM: {ROOT_DIR} ===")
    results = {}

    # 1. python ecossistema.py status
    print("[1/7] Testando: python ecossistema.py status...")
    r1 = run_cmd([sys.executable, "ecossistema.py", "status"])
    ok_tools = (
        "aidd-forge" in r1["stdout"] and "[OK] Instalado" in r1["stdout"] and
        "aidd-generator" in r1["stdout"] and
        "aidd-master" in r1["stdout"] and
        "aidd-enterprise" in r1["stdout"]
    )
    ok_skills = (
        "aidd-forge-runner" in r1["stdout"] and "[OK]" in r1["stdout"] and
        "aidd-generator-runner" in r1["stdout"] and
        "aidd-master-runner" in r1["stdout"] and
        "aidd-enterprise-runner" in r1["stdout"]
    )
    r1["passed"] = (r1["returncode"] == 0) and ok_tools and ok_skills
    results["item_1_status"] = r1
    print(f"  -> Exit {r1['returncode']}, Passou: {r1['passed']}, Tempo: {r1['duration_sec']}s")

    # 2. python ecossistema.py status --testes
    print("[2/7] Testando: python ecossistema.py status --testes (execucao de suites pytest)...")
    plano_path = os.path.join(ROOT_DIR, "PLANO-EXECUCAO-ESTRUTURADO.json")
    mtime_before = os.path.getmtime(plano_path) if os.path.exists(plano_path) else 0
    r2 = run_cmd([sys.executable, "ecossistema.py", "status", "--testes"])
    mtime_after = os.path.getmtime(plano_path) if os.path.exists(plano_path) else 0
    plano_updated = mtime_after > mtime_before
    r2["passed"] = (r2["returncode"] == 0) and plano_updated
    r2["plano_updated"] = plano_updated
    results["item_2_status_testes"] = r2
    print(f"  -> Exit {r2['returncode']}, Plano atualizado: {plano_updated}, Passou: {r2['passed']}, Tempo: {r2['duration_sec']}s")

    # 3. python ecossistema.py audit + 6 gates isolados
    print("[3/7] Testando: python ecossistema.py audit e cada gate isoladamente...")
    r3_audit = run_cmd([sys.executable, "ecossistema.py", "audit"])
    gates = [
        "G_ECOSSISTEMA_INTEGRIDADE.py",
        "G_DRIFT_NUCLEO_COMPARTILHADO.py",
        "G_HARNESS_COMPAT.py",
        "G_SEGREDOS.py",
        "G_CLI_HELP_CONSISTENCIA.py",
        "G_COMPONENTE_AGNOSTICO.py",
    ]
    isolated_gates = {}
    all_isolated_passed = True
    for g in gates:
        gate_script = os.path.join(ROOT_DIR, "gates", g)
        r_g = run_cmd([sys.executable, gate_script])
        r_g["passed"] = (r_g["returncode"] == 0)
        isolated_gates[g] = r_g
        if not r_g["passed"]:
            all_isolated_passed = False
        print(f"     * Gate isolado {g}: Exit {r_g['returncode']}, Passou: {r_g['passed']}, Tempo: {r_g['duration_sec']}s")
    
    r3_audit["passed"] = (r3_audit["returncode"] == 0) and all_isolated_passed
    results["item_3_audit"] = {
        "unified_audit": r3_audit,
        "isolated_gates": isolated_gates,
        "passed": r3_audit["passed"]
    }
    print(f"  -> Audit unificado: Exit {r3_audit['returncode']}, Passou: {r3_audit['passed']}, Tempo: {r3_audit['duration_sec']}s")

    # 4. python ecossistema.py components verify --tipo todos
    print("[4/7] Testando: python ecossistema.py components verify --tipo todos...")
    r4 = run_cmd([sys.executable, "ecossistema.py", "components", "verify", "--tipo", "todos"])
    r4["passed"] = (r4["returncode"] == 0)
    results["item_4_components_verify"] = r4
    print(f"  -> Exit {r4['returncode']}, Passou: {r4['passed']}, Tempo: {r4['duration_sec']}s")

    # 5. python ecossistema.py components sync --tipo todos --dry-run
    print("[5/7] Testando: python ecossistema.py components sync --tipo todos --dry-run...")
    git_before = run_cmd(["git", "status", "--porcelain"])
    r5 = run_cmd([sys.executable, "ecossistema.py", "components", "sync", "--tipo", "todos", "--dry-run"])
    git_after = run_cmd(["git", "status", "--porcelain"])
    diff_status = (git_before["stdout"].strip() == git_after["stdout"].strip())
    r5["passed"] = (r5["returncode"] == 0) and diff_status
    r5["dry_run_clean"] = diff_status
    results["item_5_components_sync_dryrun"] = r5
    print(f"  -> Exit {r5['returncode']}, Dry-run limpo: {diff_status}, Passou: {r5['passed']}, Tempo: {r5['duration_sec']}s")

    # 6. python ecossistema.py help, --help, -h
    print("[6/7] Testando comandos de ajuda (help, --help, -h)...")
    r6_help = run_cmd([sys.executable, "ecossistema.py", "help"])
    r6_long = run_cmd([sys.executable, "ecossistema.py", "--help"])
    r6_short = run_cmd([sys.executable, "ecossistema.py", "-h"])
    help_ok = (
        r6_help["returncode"] == 0 and "Uso: python ecossistema.py" in r6_help["stdout"] and
        r6_long["returncode"] == 0 and "Uso: python ecossistema.py" in r6_long["stdout"] and
        r6_short["returncode"] == 0 and "Uso: python ecossistema.py" in r6_short["stdout"]
    )
    results["item_6_help"] = {
        "help": r6_help,
        "--help": r6_long,
        "-h": r6_short,
        "passed": help_ok
    }
    print(f"  -> Help trio: Exit codes ({r6_help['returncode']}, {r6_long['returncode']}, {r6_short['returncode']}), Passou: {help_ok}")

    # 7. python ecossistema.py comando-invalido-xyz
    print("[7/7] Testando comando invalido...")
    r7 = run_cmd([sys.executable, "ecossistema.py", "comando-invalido-xyz"])
    r7_passed = (r7["returncode"] == 1) and ("Erro: comando desconhecido" in (r7["stdout"] + r7["stderr"]))
    r7["passed"] = r7_passed
    results["item_7_invalid_cmd"] = r7
    print(f"  -> Exit {r7['returncode']}, Passou: {r7['passed']}, Tempo: {r7['duration_sec']}s")

    overall_passed = all(
        results[k]["passed"] if "passed" in results[k] else False
        for k in results
    )

    results["overall_passed"] = overall_passed

    out_json = os.path.join(ROOT_DIR, "docs", "testes", "relatorios", "01_ecossistema_raiz_resultado.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 72)
    print(f"VEREDITO GERAL DA BATERIA 1: {'APROVADA (PASS)' if overall_passed else 'REPROVADA (FAIL)'}")
    print(f"Dados brutos gravados em: {out_json}")
    print("=" * 72)

    return 0 if overall_passed else 1

if __name__ == "__main__":
    sys.exit(main())
