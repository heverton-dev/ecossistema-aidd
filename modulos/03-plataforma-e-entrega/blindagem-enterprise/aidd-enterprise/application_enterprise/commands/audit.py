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

    def _achar_raiz_repo(inicio: str) -> str:
        curr = os.path.abspath(inicio)
        while os.path.dirname(curr) != curr:
            if os.path.isfile(os.path.join(curr, "ecossistema.py")):
                return curr
            curr = os.path.dirname(curr)
        return os.path.abspath(inicio)

    repo_root = _achar_raiz_repo(__file__)
    pastas_gates_candidatas = [
        os.path.join(target_dir, "scripts", "gates"),
        os.path.join(target_dir, "gates"),
        os.path.join(repo_root, "modulos", "04-nucleo-compartilhado", "gates"),
        os.path.join(repo_root, "componentes", "compartilhado", "gates"),
        os.path.join(repo_root, "gates"),
    ]

    def _resolver_gate(nome: str) -> str | None:
        for p in pastas_gates_candidatas:
            arq = os.path.join(p, f"{nome}.py")
            if os.path.isfile(arq):
                return arq
        return None

    # Verifica se G_SEGURANCA existe
    sec_gate_path = _resolver_gate("G_SEGURANCA")
    if sec_gate_path:
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
        gate_file = _resolver_gate(gate_name)

        print(f"\n▶️  Executando Gate: [{gate_name}] — {gate_desc}...")

        if not gate_file or not os.path.isfile(gate_file):
            print(f"  ❌ [FAIL] Arquivo do gate não encontrado ou não recebe --dir: {gate_name}.py")
            relatorio["gates"].append({
                "gate": gate_name,
                "descricao": gate_desc,
                "status": "FAIL",
                "exit_code": 1,
                "duracao_ms": 0.0,
                "erro": "Arquivo do gate ausente ou incompatível com --dir"
            })
            relatorio["resumo"]["falhas"] += 1
            has_failure = True
            continue

        t0_gate = time.time()
        try:
            cmd_args = [sys.executable, gate_file]
            try:
                with open(gate_file, "r", encoding="utf-8", errors="ignore") as gf:
                    conteudo_gate = gf.read()
                if "--dir" in conteudo_gate:
                    cmd_args.extend(["--dir", target_dir])
            except Exception:
                pass

            res = subprocess.run(
                cmd_args,
                cwd=target_dir,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=60,
            )
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
        except subprocess.TimeoutExpired:
            duracao_gate = round((time.time() - t0_gate) * 1000, 2)
            print(f"  ❌ [FAIL] Timeout rígido atingido no gate [{gate_name}] (> 60s)")
            relatorio["gates"].append({
                "gate": gate_name,
                "descricao": gate_desc,
                "status": "FAIL",
                "exit_code": 124,
                "duracao_ms": duracao_gate,
                "erro": "Timeout expirado (10s)",
                "saida_resumida": "Execução interrompida após 10s de timeout."
            })
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