# -*- coding: utf-8 -*-
"""Use Case: test — execução de baterias de testes (unit/contracts/load/all)."""

import os
import subprocess
import sys


def cmd_test(args):
    target_dir = os.path.abspath(getattr(args, "dir", "."))
    tipo = getattr(args, "tipo", "unit") or "unit"
    print("=" * 80)
    print(f"🧪 [AIDD v5.1 TEST] Executando testes: '{tipo}' em {target_dir}")
    print("=" * 80)

    src_path = os.path.join(target_dir, "src")
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{src_path}{os.pathsep}{env.get('PYTHONPATH', '')}"

    if tipo in ["unit", "all"]:
        tests_dir = os.path.join(target_dir, "tests", "unit")
        if not os.path.exists(tests_dir):
            tests_dir = os.path.join(target_dir, "tests")

        res = subprocess.run([sys.executable, "-m", "pytest", "-v", tests_dir], cwd=target_dir, env=env)
        if res.returncode != 0:
            print(f"\n❌ [FAIL] Testes unitários falharam (exit code {res.returncode})")
            sys.exit(res.returncode)

    if tipo in ["contracts", "all"]:
        gate_contracts = os.path.join(target_dir, "scripts", "gates", "G_CONTRACTS.py")
        if not os.path.isfile(gate_contracts):
            master_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            gate_contracts = os.path.join(master_root, "scripts", "gates", "G_CONTRACTS.py")

        if os.path.exists(gate_contracts):
            res = subprocess.run([sys.executable, gate_contracts, "--dir", target_dir], cwd=target_dir, env=env)
            if res.returncode != 0:
                print(f"\n❌ [FAIL] Gate de contratos falhou (exit code {res.returncode})")
                sys.exit(res.returncode)

    if tipo in ["load", "all"]:
        locust_file = os.path.join(target_dir, "tests", "load", "locustfile.py")
        if os.path.exists(locust_file):
            print("[*] Executando teste de carga Locust (headless 5s)...")
            subprocess.run([
                "locust", "-f", locust_file, "--headless", "-u", "10", "-r", "2", "-t", "5s", "--host", "http://localhost:3000"
            ], cwd=target_dir)

    print("\n🏆 [SUCESSO]: Bateria de testes executada com êxito!")