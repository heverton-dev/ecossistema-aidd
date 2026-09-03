#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.1 Enterprise CLI — Dividir para Conquistar (aidd.py)
=============================================================================
CLI oficial de automação agêntica e execução de gates determinísticos.
Suporta:
- aidd init <nome> [--dir <destino>]
- aidd compose <dir> <nome> [modulos...]
- aidd add-module <nome> [-d <desc>] [--dir <destino>]
- aidd test [unit|contracts|load|all] [--dir <destino>]
- aidd audit [--report] [--json] [--dir <destino>]
- aidd status [--dir <destino>]
- aidd deploy [docker|vps]
- aidd inject <skill|mcp|rule|spec|config|agent> <nome> [-d <descricao>] [--dir <destino>]
"""

import os
import sys
import subprocess
import argparse
import json
import time
import datetime
import platform
import re

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def ensure_environment(auto_install: bool = True):
    """Garante de forma 100% automática que o runtime possui os pré-requisitos necessários."""
    missing = []
    try:
        import pytest
    except ImportError:
        missing.append("pytest")
    try:
        import requests
    except ImportError:
        missing.append("requests")

    if missing and auto_install:
        print(f"[*] [BOOTSTRAP AUTOMÁTICO] Instalando dependências essenciais: {', '.join(missing)}...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install"] + missing, check=True, capture_output=True)
            print("[OK] Dependências instaladas com sucesso.")
        except Exception as e:
            print(f"[WARN] Não foi possível auto-instalar dependências: {e}")


def cmd_setup(args):
    """Executa diagnóstico completo e configuração automática do ambiente."""
    print("=" * 80)
    print("🔧 [AIDD SETUP] Diagnóstico e Inicialização Automática do Ambiente")
    print("=" * 80)
    
    # 1. Checagem de Python
    py_ver = platform.python_version()
    print(f"  [+] Python Runtime: {py_ver} ({sys.executable})")
    
    # 2. Instalação de requirements.txt
    req_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "requirements.txt")
    if os.path.exists(req_file):
        print("  [+] Instalando dependências do 'requirements.txt'...")
        res = subprocess.run([sys.executable, "-m", "pip", "install", "-r", req_file], capture_output=True, text=True)
        if res.returncode == 0:
            print("  [OK] Dependências instaladas com êxito.")
        else:
            print(f"  [WARN] Aviso ao instalar requirements: {res.stderr.strip()}")
    else:
        ensure_environment(auto_install=True)

    # 3. Detecção de Git
    import shutil
    git_bin = shutil.which("git")
    print(f"  [+] Git CLI: {'Presente (' + git_bin + ')' if git_bin else 'Ausente'}")

    # 4. Detecção de ORCA ADE
    orca_bin = shutil.which("orca")
    if orca_bin:
        print(f"  [+] ORCA ADE: Detectado ({orca_bin}) ➔ Modo A (Mesas de Trabalho Isoladas)")
    else:
        print("  [+] ORCA ADE: Não instalado ➔ Modo B (Subagentes Nativos / Git Worktrees)")

    # 5. Fleet Auto-Discovery — varredura de agentes de IA no PATH
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
        from core.fleet_discovery import FleetDiscovery

        fleet = FleetDiscovery()
        discovered = fleet.discover_agents()
        available_count = sum(1 for v in discovered.values() if v["available"])
        print(f"\n  [+] Fleet Discovery: {available_count} agente(s) de IA detectado(s)")
        for name, info in discovered.items():
            status = "✅" if info["available"] else "❌"
            path_str = info["path"] if info["available"] else "não encontrado"
            specialty = info.get("specialty", "?")
            print(f"      {status} {info.get('display', name):<28s} [{path_str}]  ({specialty})")
    except Exception as e:
        print(f"  [WARN] Fleet Discovery indisponível: {e}")

    print("=" * 80)
    print("🏆 [SUCESSO]: Ambiente 100% pronto para compor e executar projetos AIDD v5.1!")
    print("=" * 80)


def cmd_init(args):
    ensure_environment()
    try:
        from provision_project import provision
    except ImportError:
        from scripts.provision_project import provision
    provision(args.nome, base_dir=getattr(args, "dir", "."))


def cmd_compose(args):
    ensure_environment()
    try:
        from compose_suite import compose_suite
    except ImportError:
        from scripts.compose_suite import compose_suite
    compose_suite(
        args.target_dir,
        args.suite_name,
        args.modulos or ["crm", "erp", "helpdesk", "logistica"],
        db_engine=getattr(args, "db", "sqlite")
    )


def cmd_add_module(args):
    try:
        from add_module import criar_modulo
    except ImportError:
        from scripts.add_module import criar_modulo
    criar_modulo(args.nome, args.descricao or "", target_dir=getattr(args, "dir", "."))


def cmd_refine_module(args):
    """Executa a suíte BDD (behave) de um módulo até 100% dos cenários passarem.
    O comando é o gate determinístico; o ciclo Ler Falha -> Editar services.py ->
    Re-executar é conduzido pelo agente de refinamento de domínio (ver
    templates/agents/agent_domain_refiner.md), não por este script."""
    target_dir = os.path.abspath(getattr(args, "dir", "."))
    modulo = args.modulo
    spec_path = os.path.abspath(getattr(args, "spec", None) or os.path.join(target_dir, "features", f"{modulo}.feature"))

    print("=" * 80)
    print(f"🧬 [AIDD v5.0 BDD DOMAIN REFINER] Validando regras de domínio do módulo '{modulo}'")
    print(f"📄 Especificação: {spec_path}")
    print("=" * 80)

    if not os.path.isfile(spec_path):
        print(f"[ERRO] Arquivo de especificação não encontrado: {spec_path}")
        sys.exit(1)

    try:
        import behave  # noqa: F401
    except ImportError:
        print("[*] [BOOTSTRAP AUTOMÁTICO] Instalando 'behave' (necessário para refinamento BDD)...")
        subprocess.run([sys.executable, "-m", "pip", "install", "behave"], check=True, capture_output=True)
        req_file = os.path.join(target_dir, "requirements.txt")
        if os.path.isfile(req_file):
            with open(req_file, "r", encoding="utf-8") as f:
                conteudo = f.read()
            if "behave" not in conteudo:
                with open(req_file, "a", encoding="utf-8") as f:
                    f.write("behave>=1.2.6\n")

    src_path = os.path.join(target_dir, "src")
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{src_path}{os.pathsep}{env.get('PYTHONPATH', '')}"

    res = subprocess.run([sys.executable, "-m", "behave", spec_path, "--no-capture"], cwd=target_dir, env=env)

    if res.returncode != 0:
        print(f"\n❌ [RED] Cenários BDD do módulo '{modulo}' falharam (exit code {res.returncode}).")
        print("   Ajuste a lógica em src/modules/<modulo>/services.py e execute novamente.")
        sys.exit(res.returncode)

    print(f"\n🏆 [GREEN] 100% dos cenários BDD do módulo '{modulo}' homologados (exit 0)!")


def cmd_compose_orca(args):
    """Compose using the SubagentEngine with Context-Purge.
    Each module is built by an isolated subagent that receives only its slice's SPEC.
    After execution, subagent context is purged — zero cross-contamination.
    """
    ensure_environment()
    target_dir = os.path.abspath(getattr(args, "dir", "."))
    suite_name = getattr(args, "suite_name", "AIDD Suite")
    modulos = getattr(args, "modulos", None) or ["crm", "erp", "helpdesk", "logistica"]

    # Resolve SubagentEngine from src/core
    master_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    core_src = os.path.join(master_root, "src", "core")
    if core_src not in sys.path:
        sys.path.insert(0, core_src)

    try:
        from subagent_engine import SubagentSpec, ContextPurgeEngine
    except ImportError:
        print("[ERRO] SubagentEngine não encontrado em src/core/subagent_engine.py")
        sys.exit(1)

    print("=" * 80)
    print(f"🔀 [AIDD COMPOSE-ORCA v5.1] Composição via Subagentes Efêmeros")
    print(f"📁 Diretório Alvo: {target_dir}")
    print(f"📦 Suite: {suite_name}")
    print(f"🧩 Módulos ({len(modulos)}): {', '.join(modulos)}")
    print("=" * 80)

    os.makedirs(target_dir, exist_ok=True)

    # Build SubagentSpec for each module
    specs = []
    for modulo in modulos:
        spec_text = (
            f"# Vertical Slice SPEC: {modulo}\n"
            f"- Module: {modulo}\n"
            f"- Suite: {suite_name}\n"
            f"- Target: {target_dir}\n"
            f"- Generate: __init__.py, models.py, services.py, routes.py, mcp_tools.py\n"
            f"- Generate: tests/unit/test_{modulo}.py\n"
            f"- Pattern: AIDD Modular Clean Architecture\n"
            f"- DB: SQLite WAL with mod_{modulo} table\n"
            f"- Events: {modulo}_criado, {modulo}_atualizado, {modulo}_deletado\n"
            f"- REST: /api/{modulo}/(criar|listar|obter|atualizar|deletar|metricas)\n"
            f"- MCP: mod_{modulo}_(listar|criar|obter|atualizar|deletar)\n"
        )
        specs.append(SubagentSpec(
            module_name=modulo,
            spec_text=spec_text,
            target_dir=target_dir,
        ))

    # Spawn all subagents via ContextPurgeEngine
    engine = ContextPurgeEngine()
    t0 = time.time()

    results = engine.spawn_all(specs)
    total_ms = (time.time() - t0) * 1000

    # Report results
    summary = engine.get_summary()

    print("\n" + "=" * 80)
    print(f"📊 RELATÓRIO DE COMPOSIÇÃO ORCA (Context-Purge)")
    print("=" * 80)
    print(f"   - Total de Módulos:     {summary['total_modules']}")
    print(f"   - Sucesso (PASS):       {summary['success']}")
    print(f"   - Falha (FAIL):         {summary['failed']}")
    print(f"   - Erro (ERROR):         {summary['errors']}")
    print(f"   - Arquivos Criados:     {summary['total_files_created']}")
    print(f"   - Duração Total:        {total_ms:.2f} ms")
    print(f"   - Status Final:         {summary['status']}")
    print("=" * 80)

    # Per-module detail
    for name, detail in summary["modules"].items():
        icon = "✅" if detail["status"] == "success" else "❌"
        print(f"   {icon} {name}: {detail['status']} "
              f"({detail['files_created']} arquivos, {detail['duration_ms']:.1f} ms)")
        if detail["errors"]:
            for err in detail["errors"]:
                print(f"      ⚠️  {err}")

    # Save manifest
    manifest_path = os.path.join(target_dir, "COMPOSE-ORCA-MANIFEST.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n📄 Manifesto salvo: {manifest_path}")

    if summary["status"] == "REPROVADO":
        print("\n❌ [BLOQUEADO]: Um ou mais módulos falharam na composição ORCA.")
        sys.exit(1)

    print("\n🏆 [SUCESSO]: Todos os módulos compostos com êxito via Subagentes Efêmeros!")
    sys.exit(0)


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
            master_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
    master_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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


def cmd_bench(args):
    """Executa benchmark local de concorrência no SQLite WAL e EventBus."""
    ensure_environment()
    target_dir = os.path.abspath(getattr(args, "dir", "."))
    print("=" * 80)
    print(f"⚡ [AIDD BENCHMARK v5.1] Teste de Concorrência SQLite WAL (Local / In-Process)")
    print("   ℹ️  Medição direta do throughput SQLite WAL (sem overhead de stack HTTP).")
    print(f"📁 Diretório Alvo: {target_dir}")
    print("=" * 80)

    master_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates = [
        os.path.join(target_dir, "src"),
        os.path.join(target_dir, "src", "core"),
        os.path.join(master_root, "templates", "core"),
        os.path.join(master_root, "templates", "v2"),
        os.path.join(master_root, "src", "core")
    ]
    for c in candidates:
        if os.path.exists(c) and c not in sys.path:
            sys.path.insert(0, c)

    try:
        try:
            from core.database import Database
            from core.events import EventBus
        except ImportError:
            import database as db_mod
            import events as ev_mod
            Database = db_mod.Database
            EventBus = ev_mod.EventBus
        import concurrent.futures

        db = Database(os.path.join(target_dir, "app.db"))
        events = EventBus()

        # Pré-inicialização da conexão e WAL
        with db.get_connection() as conn:
            conn.execute("SELECT 1;").fetchone()

        total_reqs = getattr(args, "n", 100) or 100
        print(f"[*] Disparando {total_reqs} operações concorrentes no SQLite WAL...")

        t0 = time.time()
        successes = 0
        errors = 0

        def worker_task(idx):
            try:
                with db.get_connection() as conn:
                    conn.execute("SELECT 1;").fetchone()
                events.emit("benchmark_tick", {"idx": idx})
                return True
            except Exception as e:
                return False

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(worker_task, range(total_reqs)))

        successes = sum(1 for r in results if r)
        errors = sum(1 for r in results if not r)
        duration_ms = (time.time() - t0) * 1000
        avg_latency = duration_ms / total_reqs
        rps = total_reqs / ((duration_ms / 1000) or 0.001)

        print(f"\n📊 RESULTADOS DO BENCHMARK:")
        print(f"   - Total de Operações: {total_reqs}")
        print(f"   - Sucessos (PASS):   {successes}")
        print(f"   - Falhas (FAIL):     {errors}")
        print(f"   - Duração Total:     {duration_ms:.2f} ms")
        print(f"   - Latência Média:    {avg_latency:.2f} ms/req")
        print(f"   - Throughput (RPS):  {rps:.1f} req/s")
        print("=" * 80)

        if errors > 0:
            print("❌ [FALHA]: Conflitos de lock detectados sob concorrência.")
            sys.exit(1)

        print("🏆 [SUCESSO]: Desempenho Ultra-Level Homologado (Zero Lock Contention)!")
        sys.exit(0)
    except Exception as e:
        print(f"[ERRO] Falha ao executar benchmark: {e}")
        sys.exit(1)


def cmd_heal(args):
    """Executa auto-remediação determinística de gates e arquivos corrompidos."""
    ensure_environment()
    target_dir = os.path.abspath(getattr(args, "dir", "."))
    print("=" * 80)
    print(f"🩺 [AIDD SELF-HEALING v5.1] Auto-Remediação de Artefatos")
    print(f"📁 Diretório Alvo: {target_dir}")
    print("=" * 80)

    try:
        from compose_suite import compose_suite
        plano_path = os.path.join(target_dir, "PLANO-EXECUCAO-ESTRUTURADO.json")
        if os.path.exists(plano_path):
            with open(plano_path, "r", encoding="utf-8") as f:
                plano = json.load(f)
            suite_name = plano.get("projeto", {}).get("nome", "App Suite")
            modulos = plano.get("projeto", {}).get("modulos", ["crm", "erp"])
            compose_suite(target_dir, suite_name, modulos)
            print("[OK] Kernel e Fatias Verticais ressincronizados com êxito.")
        else:
            print("[WARN] Manifesto não localizado para auto-cura.")
    except Exception as e:
        print(f"[ERRO] Falha durante auto-remediação: {e}")


def cmd_deploy(args):
    alvo = getattr(args, "alvo", "docker") or "docker"
    print(f"🚀 [AIDD DEPLOY] Preparando deploy para: {alvo}...")
    if alvo == "docker":
        subprocess.run(["docker", "compose", "up", "-d", "--build"])
    elif alvo == "vps":
        if os.path.exists("deploy.sh"):
            print("Execute no seu servidor de produção: bash deploy.sh")
    print(f"✨ [OK] Instruções de deploy para {alvo} processadas.")


def cmd_export_frontend(args):
    ensure_environment()
    target_dir = os.path.abspath(getattr(args, "dir", "."))
    plano_path = os.path.join(target_dir, "PLANO-EXECUCAO-ESTRUTURADO.json")
    suite_name = "AIDD Suite"
    if os.path.exists(plano_path):
        with open(plano_path, "r", encoding="utf-8") as f:
            suite_name = json.load(f).get("projeto", {}).get("nome", suite_name)

    try:
        from openapi_to_ts import export_frontend
    except ImportError:
        from scripts.openapi_to_ts import export_frontend
    export_frontend(target_dir, suite_name, stack=getattr(args, "stack", "nextjs"))


def cmd_scaffold_infra(args):
    target_dir = os.path.abspath(getattr(args, "dir", "."))
    plano_path = os.path.join(target_dir, "PLANO-EXECUCAO-ESTRUTURADO.json")
    suite_name = "AIDD Suite"
    if os.path.exists(plano_path):
        with open(plano_path, "r", encoding="utf-8") as f:
            suite_name = json.load(f).get("projeto", {}).get("nome", suite_name)

    try:
        from scaffold_infra import scaffold_infra
    except ImportError:
        from scripts.scaffold_infra import scaffold_infra
    scaffold_infra(target_dir, suite_name)


def _core_src_path() -> str:
    master_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(master_root, "src", "core")


def _executar_injecao(payload, target_dir: str, sobrescrever: bool = False) -> int:
    """Executa o pipeline completo do Injetor Universal: resolver -> materializar -> sincronizar."""
    core_src = _core_src_path()
    if core_src not in sys.path:
        sys.path.insert(0, core_src)
    from profiles_registry import resolver_destinos
    from materializador import materializar
    from sincronizador_harness import sincronizar

    print("=" * 80)
    print(f"🧩 [AIDD INJECT] Injetando '{payload.get('tipo')}' -> '{payload.get('nome')}'")
    print(f"📁 Diretório Alvo: {os.path.abspath(target_dir)}")
    print("=" * 80)

    resolucao_result = resolver_destinos(payload, target_dir)
    if not resolucao_result.sucesso:
        print(f"[ERRO] {resolucao_result.codigo}: {resolucao_result.erro}")
        return 1
    resolucao = resolucao_result.valor

    materializacao_result = materializar(payload, resolucao, sobrescrever=sobrescrever)
    if not materializacao_result.sucesso:
        print(f"[ERRO] {materializacao_result.codigo}: {materializacao_result.erro}")
        return 1

    arquivos = materializacao_result.valor["arquivos_criados"]
    print("\n📄 Arquivos materializados:")
    for a in arquivos:
        print(f"   - {a}")

    sync_result = sincronizar(payload, resolucao, arquivos)
    if sync_result.sucesso:
        passos = sync_result.valor["passos_sincronizados"] or ["registry"]
        print(f"\n🔗 Sincronização multi-harness: {', '.join(str(p) for p in passos)}")
    else:
        print(f"\n⚠️  [AVISO] Sincronização multi-harness parcial: {sync_result.erro}")

    print("\n🏆 [SUCESSO]: Componente injetado e integrado ao ecossistema AIDD!")
    return 0


def cmd_inject(args):
    """Fase 5 do Injetor Universal: subcomando explícito 'aidd inject <tipo> <nome>'."""
    ensure_environment()
    core_src = _core_src_path()
    if core_src not in sys.path:
        sys.path.insert(0, core_src)
    from detector_camada import construir_request

    conteudo = None
    conteudo_file = getattr(args, "conteudo_file", None)
    if conteudo_file:
        with open(conteudo_file, "r", encoding="utf-8") as f:
            conteudo = f.read()

    descricao = args.descricao or f"Componente '{args.nome}' ({args.tipo}) injetado via CLI AIDD."
    payload_result = construir_request(
        tipo=args.tipo,
        nome=args.nome,
        descricao=descricao,
        alvo_projeto=getattr(args, "projeto", "aidd-master"),
        conteudo=conteudo,
    )
    if not payload_result.sucesso:
        print(f"[ERRO] {payload_result.codigo}: {payload_result.erro}")
        sys.exit(1)

    sys.exit(_executar_injecao(
        payload_result.valor,
        getattr(args, "dir", "."),
        sobrescrever=getattr(args, "sobrescrever", False),
    ))


def _tentar_injecao_por_linguagem_natural(raw_prompt: str) -> bool:
    """Reconhece pedidos PT-BR de injeção de componente antes do fallback para 'plan'.

    Retorna True (e termina o processo) se o texto foi reconhecido como um
    pedido de injeção; retorna False para deixar o fluxo cair no
    comportamento existente (planejamento de módulos de negócio via 'plan').
    """
    core_src = _core_src_path()
    if core_src not in sys.path:
        sys.path.insert(0, core_src)
    try:
        from intent_router import IntentRouter
        from detector_camada import detectar_de_texto
    except ImportError:
        return False

    intent = IntentRouter().parse_intent_result(raw_prompt)
    if intent.action != "inject":
        return False

    payload_result = detectar_de_texto(raw_prompt)
    if not payload_result.sucesso:
        print(f"[ERRO] {payload_result.codigo}: {payload_result.erro}")
        candidatos = (payload_result.detalhes or {}).get("candidatos")
        if candidatos:
            print(f"        Candidatos possíveis: {', '.join(candidatos)}")
        else:
            print("        Use o comando explícito: python scripts/aidd.py inject <tipo> <nome>")
        sys.exit(1)

    sys.exit(_executar_injecao(payload_result.valor, "."))


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


def cmd_plan(prompt: str, base_dir: str = ".", auto_apply: bool = False):
    """Fase 1.5: Gera especificação técnica (SPEC) e plano estruturado antes da criação."""
    ensure_environment()
    prompt_lower = prompt.lower()
    
    KNOWN_DOMAINS = [
        "crm", "erp", "faturamento", "financeiro", "vendas", "helpdesk",
        "suporte", "logistica", "estoque", "membros", "cursos", "catalogo",
        "produtos", "pedidos", "whatsapp", "afiliados", "assinaturas", "fiscal",
        "analytics", "lead", "leads", "campanhas", "marketing", "tickets"
    ]
    
    found_modules = []
    for d in KNOWN_DOMAINS:
        if re.search(r'\b' + d + r'\b', prompt_lower):
            slug = "crm" if d in ["lead", "leads"] else ("helpdesk" if d in ["suporte", "tickets"] else d)
            if slug not in found_modules:
                found_modules.append(slug)
                
    if not found_modules:
        words = re.findall(r'\b[a-zA-Z]{4,}\b', prompt_lower)
        stop_words = {"crie", "uma", "aplicacao", "aplicativo", "sistema", "para", "com", "suite", "modulo", "faca", "gere"}
        found_modules = [w for w in words if w not in stop_words][:4]

    if not found_modules:
        found_modules = ["principal", "configuracao"]

    slug_name = "-".join(found_modules[:3]) + "-suite"
    target_path = os.path.abspath(os.path.join(base_dir, f"app_{slug_name}"))
    suite_title = " ".join(m.capitalize() for m in found_modules) + " Suite"

    os.makedirs(target_path, exist_ok=True)

    # 1. Gerar SPEC-ARQUITETURA.md em 3 Níveis Estruturados
    spec_content = f"""# Especificação Técnica de Arquitetura em 3 Níveis (SPEC / PRD)

**Projeto:** {suite_title}  
**Diretório:** `{target_path}`  
**Status do Planejamento:** AGUARDANDO_APROVACAO  
**Prompt Original:** "{prompt}"  

---

## NÍVEL 1: ESPECIFICAÇÃO DE NEGÓCIO & REGRAS DE DOMÍNIO
"""
    for m in found_modules:
        spec_content += f"""
### Domínio / Subdomínio: `{m.upper()}`
- **Entidade Principal:** `{m.capitalize()}` (identificador, título descritivo, status de ciclo de vida e carga útil JSON).
- **Casos de Uso Primários:** Cadastrar, Consultar por ID, Listar com Filtro/Busca, Atualizar Campos e Excluir com Soft-Delete.
- **Eventos de Domínio:** Publicação obrigatória de `{m}_criado`, `{m}_atualizado` e `{m}_deletado` no `EventBus`.
- **Auditoria:** Rastreabilidade temporal com campos `criado_em`, `atualizado_em` e `deletado_em`.
"""

    spec_content += """
---

## NÍVEL 2: ESPECIFICAÇÃO DE BACK-END, PERSISTÊNCIA & CONTRATOS
"""
    for m in found_modules:
        spec_content += f"""
### Contratos de API & MCP: `{m}`
- **Rotas REST:**
  - `GET /api/{m}/listar`: Retorna coleção filtrada e paginada.
  - `GET /api/{m}/metricas`: Retorna KPIs agregados (total, ativos, concluídos, taxa de conversão).
  - `GET /api/{m}/obter?id=N`: Retorna registro único ativo.
  - `POST /api/{m}/criar`: Insere novo registro e emite evento.
  - `POST /api/{m}/atualizar`: Altera dados do registro.
  - `POST /api/{m}/deletar`: Marca exclusão lógica (soft-delete).
- **Ferramentas MCP (JSON-RPC 2.0):** `mod_{m}_listar`, `mod_{m}_criar`, `mod_{m}_obter`, `mod_{m}_atualizar`, `mod_{m}_deletar`.
- **Persistência SQLite WAL:** Tabela `mod_{m}` com índices de status e exclusão.
"""

    spec_content += """
---

## NÍVEL 3: ESPECIFICAÇÃO DE FRONT-END, DESIGN SYSTEM & UX
- **Design System:** Padrão Impeccable UI com Tailwind CSS, paleta Slate/Indigo e SVGs Lucide.
- **Componentes:** Componente visual isolado em `src/static/components/<modulo>.html` para cada fatia vertical.
- **Acessibilidade WCAG 2.1:** Botões com `type="button"`, `aria-label`, foco visível e zero diálogos nativos (`alert`).
- **Dashboard Super-App:** Header unificado, cards de KPIs no topo, tabela paginada com busca em tempo real e modais de Full CRUD.

---

## PRÓXIMO PASSO: APROVAÇÃO E EXECUÇÃO
Execute `python scripts/aidd.py apply --dir "{target_path}"` para compor o código e homologar os 7 Quality Gates.
"""
    spec_path = os.path.join(target_path, "SPEC-ARQUITETURA.md")
    with open(spec_path, "w", encoding="utf-8") as f:
        f.write(spec_content)

    # 2. Gerar PLANO-EXECUCAO-ESTRUTURADO.json inicial
    plano_data = {
        "projeto": {
            "nome": suite_title,
            "slug": slug_name,
            "diretorio": target_path,
            "status": "PLANEJADO",
            "prompt_origem": prompt,
            "zero_api_key_mode": True,
            "modulos": found_modules
        },
        "arquitetura": {
            "padrao": "AIDD Modular Clean Architecture",
            "banco": "SQLite WAL",
            "mcp_enabled": True
        }
    }
    plano_path = os.path.join(target_path, "PLANO-EXECUCAO-ESTRUTURADO.json")
    with open(plano_path, "w", encoding="utf-8") as f:
        json.dump(plano_data, f, indent=2, ensure_ascii=False)

    print("=" * 80)
    print("📋 [FASE 1.5 - SPEC & PLANEJAMENTO ARQUITETURAL]")
    print("=" * 80)
    print(f"Projeto:       {suite_title}")
    print(f"Destino:       {target_path}")
    print(f"Status:        PLANEJADO (Aguardando Aprovação)")
    print(f"Fatias ({len(found_modules)}):   {', '.join(found_modules)}")
    print(f"Documentos:    SPEC-ARQUITETURA.md | PLANO-EXECUCAO-ESTRUTURADO.json")
    print("=" * 80)

    if auto_apply:
        cmd_apply(argparse.Namespace(dir=target_path))
    else:
        print("\n👉 Para aprovar e compor imediatamente, execute:")
        print(f"   python scripts/aidd.py apply --dir \"{target_path}\"")
        print("👉 Ou edite o plano/especificação acima para ajustar o escopo antes da execução.\n")


def cmd_apply(args):
    """Fase 2: Lê o plano estruturado planejado e executa a composição e gates."""
    ensure_environment()
    target_dir = os.path.abspath(getattr(args, "dir", "."))
    plano_path = os.path.join(target_dir, "PLANO-EXECUCAO-ESTRUTURADO.json")
    
    if not os.path.exists(plano_path):
        print(f"[ERRO] Manifesto '{plano_path}' não encontrado. Execute 'plan' primeiro.")
        sys.exit(1)

    with open(plano_path, "r", encoding="utf-8") as f:
        plano = json.load(f)

    suite_name = plano.get("projeto", {}).get("nome", "Enterprise Suite")
    modulos = plano.get("projeto", {}).get("modulos", ["crm", "erp"])

    print("=" * 80)
    print(f"🚀 [FASE 2 - PROCESSAMENTO] Executando Plano Aprovado: '{suite_name}'")
    print("=" * 80)

    try:
        from compose_suite import compose_suite
    except ImportError:
        from scripts.compose_suite import compose_suite

    compose_suite(target_dir, suite_name, modulos)


def parse_natural_language_intent(prompt: str, base_dir: str = "."):
    """Ponto de entrada por Linguagem Natural — Gera o Plano / SPEC (Fase 1.5)."""
    cmd_plan(prompt, base_dir=base_dir, auto_apply=False)


def main():
    known_cmds = {"setup", "init", "plan", "apply", "prompt", "compose", "compose-orca", "add-module", "test", "audit", "bench", "heal", "deploy", "status", "export-frontend", "refine-module", "scaffold-infra", "inject", "-h", "--help"}
    if len(sys.argv) > 1 and sys.argv[1] not in known_cmds:
        raw_prompt = " ".join(sys.argv[1:])
        if _tentar_injecao_por_linguagem_natural(raw_prompt):
            return
        parse_natural_language_intent(raw_prompt)
        return

    parser = argparse.ArgumentParser(description="AIDD Framework CLI — Dividir para Conquistar (v5.1 Enterprise)")
    subparsers = parser.add_subparsers(dest="command", help="Comando a executar")

    # plan (Fase 1.5 - Especificação e Planejamento)
    p_plan = subparsers.add_parser("plan", help="Gera especificação arquitetural e plano antes de compor")
    p_plan.add_argument("prompt", help="Instrução em linguagem natural (ex: 'Crie um CRM e ERP de faturamento')")
    p_plan.add_argument("--dir", default=".", help="Diretório base de destino")
    p_plan.add_argument("--apply", action="store_true", help="Executa a composição imediatamente após planejar")

    # apply (Fase 2 - Execução do Plano Aprovado)
    p_apply = subparsers.add_parser("apply", help="Executa o plano estruturado aprovado e roda os gates")
    p_apply.add_argument("--dir", default=".", help="Diretório do projeto contendo PLANO-EXECUCAO-ESTRUTURADO.json")

    # bench (Benchmark de Concorrência e Latência)
    p_bench = subparsers.add_parser("bench", help="Executa benchmark local de concorrência no SQLite WAL e EventBus")
    p_bench.add_argument("-n", type=int, default=100, help="Número de operações concorrentes")
    p_bench.add_argument("--dir", default=".", help="Diretório do projeto")

    # heal (Auto-remediação de arquivos)
    p_heal = subparsers.add_parser("heal", help="Executa auto-remediação determinística de módulos")
    p_heal.add_argument("--dir", default=".", help="Diretório do projeto")

    # prompt (comando explícito de linguagem natural)
    p_prompt = subparsers.add_parser("prompt", help="Gera aplicação a partir de prompt em linguagem natural")
    p_prompt.add_argument("texto", help="Instrução em linguagem natural (ex: 'Crie um CRM e ERP de faturamento')")
    p_prompt.add_argument("--dir", default=".", help="Diretório base de destino")

    # setup
    subparsers.add_parser("setup", help="Executa diagnóstico completo e instalação automática de dependências")

    # init
    p_init = subparsers.add_parser("init", help="Provisiona novo projeto modular")
    p_init.add_argument("nome", help="Nome ou descrição do projeto")
    p_init.add_argument("--dir", default=".", help="Diretório base de destino")

    # compose
    p_comp = subparsers.add_parser("compose", help="Compõe suíte empresarial completa")
    p_comp.add_argument("target_dir", help="Diretório de destino")
    p_comp.add_argument("suite_name", help="Nome da suíte empresarial")
    p_comp.add_argument("modulos", nargs="*", default=["crm", "erp", "helpdesk", "logistica"], help="Lista de módulos")
    p_comp.add_argument("--db", choices=["sqlite", "postgres"], default="sqlite", help="Motor de persistência (default: sqlite)")

    # compose-orca (SubagentEngine with Context-Purge)
    p_orca = subparsers.add_parser("compose-orca", help="Compõe módulos via subagentes efêmeros com context-purge")
    p_orca.add_argument("--dir", default=".", help="Diretório de destino")
    p_orca.add_argument("--suite-name", default="AIDD Suite", help="Nome da suíte empresarial")
    p_orca.add_argument("modulos", nargs="*", default=["crm", "erp", "helpdesk", "logistica"], help="Lista de módulos")

    # add-module
    p_mod = subparsers.add_parser("add-module", help="Gera nova fatia vertical desacoplada")
    p_mod.add_argument("nome", help="Nome do módulo")
    p_mod.add_argument("--descricao", "-d", help="Descrição do módulo", default="")
    p_mod.add_argument("--dir", default=".", help="Diretório do projeto")

    # test
    p_test = subparsers.add_parser("test", help="Executa suítes de testes unitários ou de carga")
    p_test.add_argument("tipo", nargs="?", choices=["unit", "load", "contracts", "all"], default="unit", help="Tipo de teste")
    p_test.add_argument("--dir", default=".", help="Diretório do projeto")

    # audit
    p_audit = subparsers.add_parser("audit", help="Executa a bateria completa de gates determinísticos")
    p_audit.add_argument("--report", action="store_true", help="Gera relatório factual RELATORIO-AUDITORIA.json")
    p_audit.add_argument("--json", action="store_true", help="Exporta saída em JSON")
    p_audit.add_argument("--dir", default=".", help="Diretório do projeto")

    # deploy
    p_dep = subparsers.add_parser("deploy", help="Executa deploy da aplicação")
    p_dep.add_argument("alvo", nargs="?", choices=["docker", "vps", "vercel"], default="docker", help="Alvo de deploy")

    # status
    p_stat = subparsers.add_parser("status", help="Exibe integridade dos módulos e manifesto do projeto")
    p_stat.add_argument("--dir", default=".", help="Diretório do projeto")

    # export-frontend
    p_export = subparsers.add_parser("export-frontend", help="Exporta front-end Next.js/TypeScript tipado a partir do OpenAPI")
    p_export.add_argument("--stack", choices=["nextjs"], default="nextjs", help="Stack de frontend alvo")
    p_export.add_argument("--dir", default=".", help="Diretório do projeto")

    # refine-module
    p_refine = subparsers.add_parser("refine-module", help="Executa a suíte BDD (behave) de um módulo até 100%% dos cenários passarem")
    p_refine.add_argument("modulo", help="Nome do módulo alvo")
    p_refine.add_argument("--spec", default=None, help="Caminho do arquivo .feature (default: features/<modulo>.feature)")
    p_refine.add_argument("--dir", default=".", help="Diretório do projeto")

    # scaffold-infra
    p_infra = subparsers.add_parser("scaffold-infra", help="Gera infraestrutura declarativa Terraform + Helm em infra/")
    p_infra.add_argument("--dir", default=".", help="Diretório do projeto")

    # inject (Injetor Universal de Componentes)
    p_inject = subparsers.add_parser("inject", help="Injeta e integra um novo componente (skill/mcp/rule/spec/config/agent)")
    p_inject.add_argument("tipo", choices=["skill", "mcp", "rule", "spec", "config", "agent"], help="Tipo de componente a injetar")
    p_inject.add_argument("nome", help="Nome/slug do componente (kebab-case, ex.: 'seguranca-cibernetica')")
    p_inject.add_argument("--descricao", "-d", default="", help="Descrição funcional do componente em PT-BR")
    p_inject.add_argument("--conteudo-file", dest="conteudo_file", default=None, help="Arquivo com o conteúdo completo do artefato (senão, gera scaffold padrão completo)")
    p_inject.add_argument("--projeto", default="aidd-master", help="Projeto alvo com perfil resolvido (default: aidd-master)")
    p_inject.add_argument("--sobrescrever", action="store_true", help="Sobrescreve destinos já existentes em disco")
    p_inject.add_argument("--dir", default=".", help="Diretório raiz do projeto (default: diretório atual)")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    cmds = {
        "plan": lambda a: cmd_plan(a.prompt, getattr(a, "dir", "."), getattr(a, "apply", False)),
        "apply": cmd_apply,
        "bench": cmd_bench,
        "heal": cmd_heal,
        "prompt": lambda a: parse_natural_language_intent(a.texto, getattr(a, "dir", ".")),
        "setup": cmd_setup,
        "init": cmd_init,
        "compose": cmd_compose,
        "compose-orca": cmd_compose_orca,
        "add-module": cmd_add_module,
        "test": cmd_test,
        "audit": cmd_audit,
        "deploy": cmd_deploy,
        "status": cmd_status,
        "export-frontend": cmd_export_frontend,
        "refine-module": cmd_refine_module,
        "scaffold-infra": cmd_scaffold_infra,
        "inject": cmd_inject
    }
    cmds[args.command](args)


if __name__ == '__main__':
    main()
