#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.1 Enterprise — GATE ORCHESTRATOR WITH AUTO-HEALING (run_all.py)
=============================================================================
Executa todos os gates determinísticos em sequência. Se um gate falhar,
executa scripts/autofix.py primeiro e re-tenta. Se ainda falhar, exit 1.

Gates na ordem de execução:
  1. G_ESTRUTURA      — Validação estrutural do projeto
  2. G_SEGREDOS       — Varredura de segredos e credenciais
  3. G_SEGURANCA      — Auditoria de segurança e compliance
  4. G_TESTES         — Testes unitários e healthcheck
  5. G_QUALIDADE      — Métricas de qualidade de código
  6. G_CONTRACTS      — Validação de contratos OpenAPI
  7. G_CHAOS          — Testes de caos e resiliência
  8. G_HARNESS_COMPAT — Compatibilidade do harness
  9. G_ARQUITETURA    — Linter AST de Bounded Context
  10. G_INJECT         — Injetor Universal de Componentes (Skills/MCPs/Rules/Specs/Configs/Agents)
"""

import os
import sys
import subprocess
import argparse
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Todos os gates disponíveis em ordem
ALL_GATES = [
    "G_ESTRUTURA",
    "G_SEGREDOS",
    "G_SEGURANCA",
    "G_TESTES",
    "G_QUALIDADE",
    "G_CONTRACTS",
    "G_CHAOS",
    "G_HARNESS_COMPAT",
    "G_ARQUITETURA",
    "G_INJECT",
]

GATE_SCRIPTS = {
    "G_ESTRUTURA": "G_ESTRUTURA.py",
    "G_SEGREDOS": "G_SEGREDOS.py",
    "G_SEGURANCA": "G_SEGURANCA.py",
    "G_TESTES": "G_TESTES.py",
    "G_QUALIDADE": "G_QUALIDADE.py",
    "G_CONTRACTS": "G_CONTRACTS.py",
    "G_CHAOS": "G_CHAOS.py",
    "G_HARNESS_COMPAT": "G_HARNESS_COMPAT.py",
    "G_ARQUITETURA": "G_ARQUITETURA.py",
    "G_INJECT": "G_INJECT.py",
}


def run_gate(gate_name: str, script_path: str, root_dir: str) -> int:
    """Executa um único gate e retorna o exit code."""
    cmd = [sys.executable, script_path, "--dir", root_dir]
    try:
        result = subprocess.run(cmd, timeout=300)
        return result.returncode
    except subprocess.TimeoutExpired:
        print(f"  ⏰ TIMEOUT: {gate_name} excedeu 300 segundos")
        return 1
    except FileNotFoundError:
        print(f"  ❌ ERRO: Script não encontrado: {script_path}")
        return 1
    except Exception as e:
        print(f"  ❌ ERRO ao executar {gate_name}: {e}")
        return 1


def run_autofix(root_dir: str, scripts_dir: str) -> bool:
    """Executa autofix.py e retorna True se rodou sem erros."""
    autofix_path = os.path.join(scripts_dir, "autofix.py")
    if not os.path.isfile(autofix_path):
        print("  ⏭️  autofix.py não encontrado — pulando auto-correção")
        return False

    print("  🔧 Executando autofix.py antes de re-tentar...")
    try:
        result = subprocess.run(
            [sys.executable, autofix_path, "--dir", root_dir],
            timeout=180
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("  ⏰ autofix.py excedeu timeout")
        return False
    except Exception as e:
        print(f"  ❌ Erro ao executar autofix: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="run_all.py — Gate Orchestrator AIDD v5.1 com Auto-Healing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python scripts/run_all.py --dir .
  python scripts/run_all.py --dir . --gates G_ESTRUTURA,G_SEGURANCA
  python scripts/run_all.py --gates G_ARQUITETURA
        """
    )
    parser.add_argument("--dir", default=".", help="Diretório raiz do projeto")
    parser.add_argument(
        "--gates",
        default=None,
        help="Lista de gates separados por vírgula (padrão: todos). "
             f"Disponíveis: {', '.join(ALL_GATES)}"
    )
    args = parser.parse_args()

    root_dir = os.path.abspath(args.dir)
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    gates_dir = os.path.join(scripts_dir, "gates")

    # Determinar quais gates executar
    if args.gates:
        selected = [g.strip() for g in args.gates.split(",")]
        invalid = [g for g in selected if g not in ALL_GATES]
        if invalid:
            print(f"❌ Gates inválidos: {', '.join(invalid)}")
            print(f"   Gates disponíveis: {', '.join(ALL_GATES)}")
            sys.exit(1)
        gates_to_run = selected
    else:
        gates_to_run = ALL_GATES

    # Banner
    print("=" * 80)
    print("🚀  AIDD v5.1 — GATE ORCHESTRATOR: Executando todos os Quality Gates")
    print(f"📁  Diretório Alvo: {root_dir}")
    print(f"🔧  Auto-Healing: ATIVADO (autofix.py antes de re-tentar)")
    print(f"📋  Gates a executar: {len(gates_to_run)}")
    print("=" * 80)

    results = {}
    start_time = time.time()

    for gate_name in gates_to_run:
        script_file = GATE_SCRIPTS[gate_name]
        script_path = os.path.join(gates_dir, script_file)

        if not os.path.isfile(script_path):
            print(f"\n⏭️  [{gate_name}] Script não encontrado: {script_path} — pulando")
            results[gate_name] = "SKIPPED"
            continue

        print(f"\n{'─' * 80}")
        print(f"▶️  EXECUTANDO: {gate_name}")
        print(f"{'─' * 80}")

        exit_code = run_gate(gate_name, script_path, root_dir)

        if exit_code == 0:
            print(f"\n✅ [{gate_name}] PASSOU")
            results[gate_name] = "PASS"
        else:
            print(f"\n❌ [{gate_name}] FALHOU (exit {exit_code})")

            # Auto-healing: tentar autofix e re-executar
            print(f"  🔄 Iniciando ciclo de auto-healing para {gate_name}...")
            autofix_ok = run_autofix(root_dir, scripts_dir)

            if autofix_ok:
                print(f"  🔁 Re-executando {gate_name} após autofix...")
                exit_code_retry = run_gate(gate_name, script_path, root_dir)

                if exit_code_retry == 0:
                    print(f"\n✅ [{gate_name}] PASSOU (após auto-healing)")
                    results[gate_name] = "PASS (healed)"
                else:
                    print(f"\n❌ [{gate_name}] FALHOU novamente (exit {exit_code_retry})")
                    results[gate_name] = "FAIL"
            else:
                print(f"  ⚠️  autofix não pôde corrigir — {gate_name} permanece FALHO")
                results[gate_name] = "FAIL"

    elapsed = time.time() - start_time

    # Relatório final
    print("\n" + "=" * 80)
    print("📊  RELATÓRIO FINAL DO GATE ORCHESTRATOR")
    print("=" * 80)

    passed_count = 0
    failed_count = 0
    skipped_count = 0

    for gate_name in gates_to_run:
        status = results.get(gate_name, "UNKNOWN")
        if status.startswith("PASS"):
            symbol = "✅"
            passed_count += 1
        elif status == "FAIL":
            symbol = "❌"
            failed_count += 1
        else:
            symbol = "⏭️"
            skipped_count += 1
        print(f"  {symbol} {gate_name:<20} {status}")

    print(f"\n  ⏱️  Tempo total: {elapsed:.1f}s")
    print(f"  ✅ Aprovados: {passed_count}")
    print(f"  ❌ Reprovados: {failed_count}")
    if skipped_count:
        print(f"  ⏭️  Pulados: {skipped_count}")
    print("=" * 80)

    if failed_count > 0:
        print("🚫 [BLOQUEADO]: Existem gates reprovados. Pipeline bloqueado.")
        sys.exit(1)
    else:
        print("🏆 [APROVADO]: Todos os gates passaram! Pipeline liberado para produção.")
        sys.exit(0)


if __name__ == "__main__":
    main()
