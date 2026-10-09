# -*- coding: utf-8 -*-
"""Use Case: audit — bateria completa de gates determinísticos."""

import datetime
import json
import os
import platform
import subprocess
import sys
import time


def cmd_audit(args):
    target_dir = os.path.abspath(getattr(args, "dir", "."))
    print("=" * 80)
    print(f"🛡️  [AIDD v5.1 ENTERPRISE AUDIT] Bateria Completa de Gates Determinísticos")
    print(f"📁 Diretório Alvo: {target_dir}")
    print("=" * 80)

    gates = [
        ("G_ESTRUTURA", "Layout do Projeto, Clean Architecture e Manifestos"),
        ("G_QUALIDADE", "Sintaxe Estática, Compilação e Anti-Stubs"),
        ("G_TESTES", "Execução Obrigatória da Suíte de Testes Unitários"),
        ("G_CONTRACTS", "Conformidade OpenAPI 3.1 e Model Context Protocol (MCP)"),
        ("G_SEGREDOS", "Varredura de Entropia de Shannon e Credenciais Hardcoded"),
        ("G_HARNESS_COMPAT", "Compatibilidade Multi-Harness e Portabilidade")
    ]

    gates_dir = os.path.join(target_dir, "scripts", "gates")
    # Fallback para pasta global do aidd-master
    master_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    fallback_gates_dir = os.path.join(master_root, "scripts", "gates")

    # Verifica se G_SEGURANCA existe
    sec_gate_path = os.path.join(gates_dir, "G_SEGURANCA.py")
    if not os.path.isfile(sec_gate_path):
        sec_gate_path = os.path.join(fallback_gates_dir, "G_SEGURANCA.py")
    if os.path.isfile(sec_gate_path):
        gates.append(("G_SEGURANCA", "Auditoria OWASP, Criptografia JWT e Blindagem Militar"))

    relatorio = {
        "metadata": {
            "timestamp": datetime.datetime.now().isoformat(),
            "target_dir": target_dir,
            "python_version": platform.python_version(),
            "sistema_operacional": platform.platform(),
            "framework": "AIDD Master Enterprise"
        },
        "gates": [],
        "resumo": {
            "total": len(gates),
            "aprovados": 0,
            "falhas": 0,
            "duracao_total_ms": 0.0,
            "status_geral": "PENDENTE"
        }
    }

    t0_global = time.time()
    has_failure = False

    for gate_name, gate_desc in gates:
        gate_file = os.path.join(gates_dir, f"{gate_name}.py")
        if not os.path.isfile(gate_file):
            gate_file = os.path.join(fallback_gates_dir, f"{gate_name}.py")

        print(f"\n▶️  Executando Gate: [{gate_name}] — {gate_desc}...")

        if not os.path.isfile(gate_file):
            print(f"  ❌ [FAIL] Arquivo do gate não encontrado: {gate_file}")
            relatorio["gates"].append({
                "gate": gate_name,
                "descricao": gate_desc,
                "status": "FAIL",
                "exit_code": 1,
                "duracao_ms": 0.0,
                "erro": "Arquivo do gate ausente"
            })
            relatorio["resumo"]["falhas"] += 1
            has_failure = True
            continue

        t0_gate = time.time()
        res = subprocess.run([sys.executable, gate_file, "--dir", target_dir], cwd=target_dir, capture_output=True, text=True, errors="replace")
        duracao_gate = round((time.time() - t0_gate) * 1000, 2)

        # Exibe saída do gate
        if res.stdout:
            print(res.stdout.strip())
        if res.stderr:
            print(res.stderr.strip())

        status = "PASS" if res.returncode == 0 else "FAIL"
        relatorio["gates"].append({
            "gate": gate_name,
            "descricao": gate_desc,
            "status": status,
            "exit_code": res.returncode,
            "duracao_ms": duracao_gate,
            "saida_resumida": res.stdout[-400:] if res.stdout else ""
        })

        if res.returncode == 0:
            relatorio["resumo"]["aprovados"] += 1
        else:
            relatorio["resumo"]["falhas"] += 1
            has_failure = True

    duracao_total = round((time.time() - t0_global) * 1000, 2)
    relatorio["resumo"]["duracao_total_ms"] = duracao_total
    relatorio["resumo"]["status_geral"] = "APROVADO" if not has_failure else "REPROVADO"

    # Salva relatório técnico factual se solicitado (--report ou --json)
    if getattr(args, "report", False) or getattr(args, "json", False):
        rep_file = os.path.join(target_dir, "RELATORIO-AUDITORIA.json")
        with open(rep_file, "w", encoding="utf-8") as f:
            json.dump(relatorio, f, ensure_ascii=False, indent=2)
        print(f"\n📄 [FACTUAL REPORT] Relatório salvo com sucesso em: {rep_file}")

    print("\n" + "=" * 80)
    print(f"📊 PAINEL CONSOLIDADO DE AUDITORIA AIDD v5.1:")
    print(f"   - Total de Gates:     {relatorio['resumo']['total']}")
    print(f"   - Aprovados (PASS):   {relatorio['resumo']['aprovados']}")
    print(f"   - Falhas (FAIL):      {relatorio['resumo']['falhas']}")
    print(f"   - Duração Total:      {duracao_total:.2f} ms")
    print(f"   - Status Final:       {relatorio['resumo']['status_geral']}")
    print("=" * 80)

    if has_failure:
        print("❌ [BLOQUEADO]: O projeto NÃO passou em todos os gates determinísticos.")
        sys.exit(1)

    print("🏆 [HOMOLOGAÇÃO APROVADA]: Projeto 100% aderente às Regras Anti-Fail AIDD v5.1!")
    sys.exit(0)