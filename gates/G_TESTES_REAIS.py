# -*- coding: utf-8 -*-
"""
 =============================================================================
 ECOSSISTEMA AIDD — QUALITY GATE: G_TESTES_REAIS
 =============================================================================
 Roda pytest de verdade em cada tools/<ferramenta> e falha (exit 1) se
 qualquer suíte tiver failed > 0. Diferente dos demais gates que auditam
 estrutura/AST/regex, este gate executa os testes reais.

 Complementa o item 2 (telemetria) ao garantir que a saúde dos testes é
 verificada ao vivo, não por JSON estático.

 Uso:
   python gates/G_TESTES_REAIS.py
       exit 0 = todas as suítes passaram (failed=0). exit 1 = falha em
       pelo menos uma suíte.
"""

import os
import re
import subprocess
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(ROOT_DIR, "tools")

FERRAMENTAS = [
    "aidd-forge",
    "aidd-generator",
    "aidd-master",
    "aidd-enterprise",
    "aidd-ops",
]


def _rodar_pytest(diretorio):
    """Executa pytest -q --tb=no e retorna (exit_code, stdout_text)."""
    resultado = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--tb=no"],
        cwd=diretorio,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=900,
    )
    return resultado.returncode, resultado.stdout + resultado.stderr


def _parsear_resultado(texto):
    """Extrai passed/failed/skipped do output do pytest -q."""
    passed = failed = skipped = 0

    # Formato típico do pytest -q: "212 passed, 2 failed, 4 skipped in Xs"
    m = re.search(r'(\d+)\s+passed', texto)
    if m:
        passed = int(m.group(1))
    m = re.search(r'(\d+)\s+failed', texto)
    if m:
        failed = int(m.group(1))
    m = re.search(r'(\d+)\s+skipped', texto)
    if m:
        skipped = int(m.group(1))

    # Fallback: "no tests ran" ou output vazio
    if "no tests ran" in texto.lower():
        return 0, 0, 0

    return passed, failed, skipped


def executar():
    print("=" * 70)
    print(" [GATE] G_TESTES_REAIS — Execução real de pytest por ferramenta")
    print("=" * 70)
    print()

    resultados = []
    falhou = False

    for ferramenta in FERRAMENTAS:
        dir_ferramenta = os.path.join(TOOLS_DIR, ferramenta)
        if not os.path.isdir(dir_ferramenta):
            print(f"  [{ferramenta}] DIRETÓRIO AUSENTE — ignorado")
            resultados.append((ferramenta, "AUSENTE", 0, 0, 0))
            continue

        print(f"  [{ferramenta}] Rodando pytest...", end=" ", flush=True)
        try:
            exit_code, output = _rodar_pytest(dir_ferramenta)
        except subprocess.TimeoutExpired:
            print("TIMEOUT (900s)")
            resultados.append((ferramenta, "TIMEOUT", 0, 0, 0))
            falhou = True
            continue
        except Exception as e:
            print(f"ERRO: {e}")
            resultados.append((ferramenta, "ERRO", 0, 0, 0))
            falhou = True
            continue

        passed, failed, skipped = _parsear_resultado(output)

        if failed > 0:
            print(f"FALHOU ({passed} passed, {failed} failed, {skipped} skipped)")
            falhou = True
        elif passed == 0 and skipped == 0:
            print("SEM TESTES (0 resultados)")
        else:
            print(f"OK ({passed} passed, {failed} failed, {skipped} skipped)")

        resultados.append((ferramenta, "OK" if failed == 0 else "FALHA", passed, failed, skipped))

    # Resumo
    print()
    print("-" * 70)
    print(" RESUMO G_TESTES_REAIS")
    print("-" * 70)

    total_passed = sum(p for _, _, p, _, _ in resultados)
    total_failed = sum(f for _, _, _, f, _ in resultados)
    total_skipped = sum(s for _, _, _, _, s in resultados)

    for ferramenta, status, passed, failed, skipped in resultados:
        if status == "AUSENTE":
            icon = "SKIP"
        elif status == "TIMEOUT" or status == "ERRO":
            icon = "FALHA"
        elif failed > 0:
            icon = "FALHA"
        else:
            icon = " OK "
        print(f"  [{icon}] {ferramenta:<24} {passed:>4} passed, {failed:>2} failed, {skipped:>2} skipped")

    print("-" * 70)
    print(f"  TOTAL: {total_passed} passed, {total_failed} failed, {total_skipped} skipped")
    print()

    if falhou:
        print(" [FALHA] Quality Gate G_TESTES_REAIS REPROVADO — pelo menos 1 suíte com falhas reais!")
        print("  Ação necessária: corrija os testes que falham antes de marcar audit como verde.")
        print("=" * 70)
        return 1

    print(" [SUCESSO] Quality Gate G_TESTES_REAIS APROVADO — todas as suítes passaram!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(executar())
