#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
02_aidd_master_pytest.py
Bateria 2 - Item 2.17
Roda a suite pytest completa de tools/aidd-master e confirma
o numero real de testes passando agora.
"""
import os
import sys
import subprocess
import time
import json
import re

REPO_ROOT    = r"C:\Users\trcnologia\Desktop\ecossistema-aidd"
MASTER_DIR   = os.path.join(REPO_ROOT, "tools", "aidd-master")
PYTHON       = sys.executable
BASELINE_PASS = 238
BASELINE_SKIP = 4

def main():
    print(f"{'='*70}")
    print("  ITEM: 2.17-pytest-suite-completa")
    print(f"  CMD : {PYTHON} -m pytest tests/ -q")
    print(f"  CWD : {MASTER_DIR}")
    print(f"{'='*70}")
    t0 = time.time()
    res = subprocess.run(
        [PYTHON, "-m", "pytest", "tests/", "-q", "--tb=short"],
        cwd=MASTER_DIR, capture_output=True, text=True, errors="replace",
        timeout=600
    )
    dur = round(time.time() - t0, 2)
    combined = (res.stdout or "") + (res.stderr or "")

    # Exibir ultimas linhas
    lines = combined.split("\n")
    for line in lines[-40:]:
        print(f"  | {line}")

    # Extrair numeros reais de passed/failed/skipped
    passed = failed = skipped = errors = 0
    for line in lines:
        m = re.search(r"(\d+) passed", line)
        if m: passed = int(m.group(1))
        m = re.search(r"(\d+) failed", line)
        if m: failed = int(m.group(1))
        m = re.search(r"(\d+) skipped", line)
        if m: skipped = int(m.group(1))
        m = re.search(r"(\d+) error", line)
        if m: errors = int(m.group(1))

    ok = res.returncode == 0
    regression = False
    notes = []
    if passed != BASELINE_PASS:
        notes.append(f"REGRESSAO_POSSIVEL: passed={passed} (baseline={BASELINE_PASS})")
        regression = True
    if skipped != BASELINE_SKIP:
        notes.append(f"SKIP_MUDOU: skipped={skipped} (baseline={BASELINE_SKIP})")
    if failed > 0:
        notes.append(f"FALHAS: {failed} testes falharam")
    if errors > 0:
        notes.append(f"ERROS: {errors} erros de coleta")

    print(f"\n{'='*70}")
    print("RESULTADO 2.17 - pytest suite tools/aidd-master")
    print(f"  exit_code : {res.returncode}")
    print(f"  duration  : {dur}s")
    print(f"  passed    : {passed} (baseline={BASELINE_PASS})")
    print(f"  failed    : {failed}")
    print(f"  skipped   : {skipped} (baseline={BASELINE_SKIP})")
    print(f"  errors    : {errors}")
    icon = "PASS" if (ok and not regression) else ("FAIL" if failed > 0 or errors > 0 else "PASS COM RESSALVAS")
    print(f"  VEREDITO  : {icon}")
    for n in notes:
        print(f"  NOTE      : {n}")

    result = {
        "item": "2.17-pytest-suite-completa",
        "exit_code": res.returncode,
        "ok": ok and not (failed > 0 or errors > 0),
        "duration": dur,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "errors": errors,
        "baseline_passed": BASELINE_PASS,
        "baseline_skipped": BASELINE_SKIP,
        "regression": regression,
        "notes": notes,
        "stdout_tail": "\n".join(lines[-30:]),
    }

    out_path = os.path.join(REPO_ROOT, "docs", "testes", "testes", "_resultados_pytest.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n[*] Resultado salvo: {out_path}")
    return 0 if result["ok"] else 1

if __name__ == "__main__":
    sys.exit(main())
