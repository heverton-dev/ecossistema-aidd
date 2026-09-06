# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — CLI UNIFICADA DO META-REPOSITÓRIO
=============================================================================
Ponto único de entrada e orquestração do ecossistema-aidd.
Roteia comandos para as 4 ferramentas integradas:
  - forge      -> tools/aidd-forge
  - generate   -> tools/aidd-generator
  - master     -> tools/aidd-master
  - enterprise -> tools/aidd-enterprise
  - audit      -> gates/G_ECOSSISTEMA_INTEGRIDADE.py
  - status     -> Resumo do status do ecossistema
"""

import argparse
import os
import sys
import subprocess

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(ROOT_DIR, "tools")

def print_banner():
    print("=" * 72)
    print(" [ECOSSISTEMA AIDD] Meta-Orquestrador Unificado de Engenharia Agêntica")
    print("=" * 72)

def run_command(cmd, cwd, env=None):
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    res = subprocess.run(cmd, cwd=cwd, env=merged_env)
    return res.returncode

def cmd_forge(args):
    forge_dir = os.path.join(TOOLS_DIR, "aidd-forge")
    env = {"PYTHONPATH": forge_dir}
    cmd = [sys.executable, "-m", "aidd_forge.cli"] + args
    return run_command(cmd, cwd=forge_dir, env=env)

def cmd_generate(args):
    gen_dir = os.path.join(TOOLS_DIR, "aidd-generator")
    pipeline_script = os.path.join(gen_dir, "scripts", "pipeline_completo.py")
    env = {"PYTHONPATH": gen_dir}
    cmd = [sys.executable, pipeline_script] + args
    return run_command(cmd, cwd=gen_dir, env=env)

def cmd_master(args):
    master_dir = os.path.join(TOOLS_DIR, "aidd-master")
    aidd_script = os.path.join(master_dir, "scripts", "aidd.py")
    env = {"PYTHONPATH": master_dir}
    cmd = [sys.executable, aidd_script] + args
    return run_command(cmd, cwd=master_dir, env=env)

def cmd_enterprise(args):
    ent_dir = os.path.join(TOOLS_DIR, "aidd-enterprise")
    aidd_script = os.path.join(ent_dir, "scripts", "aidd.py")
    env = {"PYTHONPATH": ent_dir}
    cmd = [sys.executable, aidd_script] + args
    return run_command(cmd, cwd=ent_dir, env=env)

def cmd_components(args):
    sys.path.insert(0, os.path.join(ROOT_DIR, "scripts"))
    import gestor_componentes

    if not args or args[0] not in ("sync", "verify"):
        print("Erro: uso 'python ecossistema.py components sync|verify --tipo <tipo|todos> [--ferramenta <nome>] [--dry-run]'")
        return 1

    acao = args[0]
    resto = args[1:]

    parser = argparse.ArgumentParser(prog=f"ecossistema.py components {acao}")
    parser.add_argument("--tipo", required=True)
    parser.add_argument("--ferramenta", default=None)
    if acao == "sync":
        parser.add_argument("--dry-run", action="store_true")
    args_ns = parser.parse_args(resto)

    try:
        if acao == "sync":
            return gestor_componentes._cmd_sync(args_ns)
        return gestor_componentes._cmd_verify(args_ns)
    except ValueError as exc:
        print(f"Erro: {exc}")
        return 1


def cmd_orchestrate(args):
    parser = argparse.ArgumentParser(
        prog="ecossistema.py orchestrate",
        description="Gera e (opcionalmente) executa um Flight Plan a partir de um plano ORCA.",
    )
    parser.add_argument("plano", help="Diretorio do plano (ex: docs/planos/skill-gerador-planos-auditoria)")
    parser.add_argument("--dry-run", action="store_true", help="Apenas gera e imprime o Flight Plan, sem tocar em git ou spawnar agentes.")
    parser.add_argument("--resume", action="store_true", help="Retoma um Flight Plan previamente iniciado (crash recovery).")
    parser.add_argument("--yes", action="store_true", help="Nao pede confirmacao interativa do Plano de Voo.")
    parser.add_argument("--stream", action="store_true", help="Exibe a saida dos agentes em tempo real no console.")
    parser.add_argument(
        "--harness", default=None,
        choices=["mimo", "opencode", "claude", "agy"],
        help="Harness de destino (se omitido, pergunta interativamente)",
    )
    parser.add_argument(
        "--profiles", default=None,
        help="Caminho para harness_profiles.json (default: .orca/harness_profiles.json.example)",
    )
    ns = parser.parse_args(args)

    orchestrator_root = os.path.join(
        ROOT_DIR, "componentes", "compartilhado", "skills", "orca-plan-orchestrator"
    )
    sys.path.insert(0, orchestrator_root)

    from scripts.flight_plan import gerar_plano_de_voo, renderizar_plano_de_voo
    from scripts.orchestrator_engine import executar_orquestracao

    profiles_path = ns.profiles
    if profiles_path is None:
        profiles_path = os.path.join(
            ROOT_DIR, "componentes", "compartilhado", "skills",
            "orca-plan-orchestrator", ".orca", "harness_profiles.json.example",
        )

    harness_escolhido = ns.harness
    if harness_escolhido is None:
        if sys.stdin.isatty():
            import shutil
            candidatos = ["claude", "agy", "mimo", "opencode"]
            print("\n[ORCA ADE] Seleção Interativa de Harness:")
            disponiveis = []
            for idx, h in enumerate(candidatos, 1):
                caminho = shutil.which(h)
                tag = f"[INSTALADO: {caminho}]" if caminho else "[NÃO DETECTADO NO PATH]"
                print(f"  {idx}) {h:<10} {tag}")
                disponiveis.append(h)
            try:
                escolha = input("\nEscolha o número do harness executor (default: 1 - claude): ").strip()
                if escolha in ("1", "claude", ""):
                    harness_escolhido = "claude"
                elif escolha in ("2", "agy"):
                    harness_escolhido = "agy"
                elif escolha in ("3", "mimo"):
                    harness_escolhido = "mimo"
                elif escolha in ("4", "opencode"):
                    harness_escolhido = "opencode"
                else:
                    print(f"[ERRO] Escolha inválida '{escolha}'. Abortado.")
                    return 1
            except (EOFError, KeyboardInterrupt):
                print("\n[CANCELADO] Seleção cancelada pelo usuário.")
                return 1
        else:
            harness_escolhido = "claude" if shutil.which("claude") else "mimo"
            print(f"[ORCA ADE] Stdin não interativo. Harness auto-selecionado: {harness_escolhido}")

    print(f"[ORCA ADE] Harness Executor selecionado: {harness_escolhido}")

    if ns.dry_run:
        try:
            data = gerar_plano_de_voo(ns.plano, profiles_path, harness=harness_escolhido)
        except (FileNotFoundError, ValueError, KeyError) as exc:
            print(f"Erro ao gerar Flight Plan: {exc}")
            return 1
        print(renderizar_plano_de_voo(data))
        print("[DRY-RUN] Flight Plan gerado com sucesso. Nenhuma acao executada.")
        return 0

    try:
        return executar_orquestracao(
            ns.plano, profiles_path, harness=harness_escolhido, resume=ns.resume, yes=ns.yes, stream=ns.stream,
        )
    except (FileNotFoundError, ValueError, KeyError, RuntimeError) as exc:
        print(f"Erro na orquestracao: {exc}")
        return 1


def cmd_plan(args):
    script = os.path.join(ROOT_DIR, "scripts", "gerenciador_planos.py")
    return run_command([sys.executable, script] + args, cwd=ROOT_DIR)

def cmd_audit(args):
    gates = [
        "G_ECOSSISTEMA_INTEGRIDADE.py",
        "G_DRIFT_NUCLEO_COMPARTILHADO.py",
        "G_HARNESS_COMPAT.py",
        "G_SEGREDOS.py",
        "G_CLI_HELP_CONSISTENCIA.py",
        "G_COMPONENTE_AGNOSTICO.py",
    ]
    for gate in gates:
        gate_script = os.path.join(ROOT_DIR, "gates", gate)
        codigo = run_command([sys.executable, gate_script] + args, cwd=ROOT_DIR)
        if codigo != 0:
            return codigo
    return 0

def cmd_status(args):
    if "--testes" in args:
        sys.path.insert(0, os.path.join(ROOT_DIR, "scripts", "manutencao"))
        from gerar_status_testes import gerar
        gerar()
        return 0

    print_banner()
    print("\nFerramentas Integradas em tools/:")
    tools = [
        ("aidd-forge", "Bootstrap, governança, fatiamento e context-purge"),
        ("aidd-generator", "Fábrica autônoma de software (Pipeline 8 fases)"),
        ("aidd-master", "Suíte Modular com Fatias Verticais e SQLite WAL"),
        ("aidd-enterprise", "Missão crítica, conformidade SHA-256 e Zero-Trust")
    ]
    for name, desc in tools:
        path = os.path.join(TOOLS_DIR, name)
        status = "[OK] Instalado" if os.path.isdir(path) else "[FALTA] Não encontrado"
        print(f"  - {name:<24} {status:<16} {desc}")

    print("\nSkills Universais:")
    skills_list = [
        "aidd-forge-runner",
        "aidd-generator-runner",
        "aidd-master-runner",
        "aidd-enterprise-runner",
        "orca-plan-orchestrator",
        "planos-auditoria-runner",
        "componentes-runner"
    ]
    for skill in skills_list:
        path = os.path.join(ROOT_DIR, "skills", skill, "SKILL.md")
        status = "[OK]" if os.path.exists(path) else "[AUSENTE]"
        print(f"  - {skill:<26} {status}")

    print("\nSlash Commands Ativos:")
    print("  /forge [caminho]        -> Dispara aidd-forge")
    print("  /generate <ideia>       -> Dispara aidd-generator")
    print("  /master <modulo>        -> Dispara aidd-master")
    print("  /enterprise <tipo> <nome> -> Dispara aidd-enterprise")
    print("  /orchestrate [plano]    -> Dispara orca-plan-orchestrator")
    print("  /plan <nome>            -> Dispara planos-auditoria-runner")
    print("-" * 72)
    return 0

def print_help():
    print_banner()
    print("""
Uso: python ecossistema.py <comando> [argumentos...]

Comandos disponíveis:
  forge <args>        Executa operações do aidd-forge (ex: forge init [pasta])
  generate <args>     Executa o pipeline do aidd-generator (ex: generate "Minha Ideia")
  master <args>       Executa comandos do aidd-master (ex: master add-module faturamento)
  enterprise <args>   Executa comandos do aidd-enterprise (ex: enterprise inject skill auth)
  components sync|verify --tipo <tipo|todos> [--ferramenta <nome>] [--dry-run]
                      Sincroniza/verifica distribuicao fisica multi-harness de
                      componentes (gates/manifesto_harnesses.json)
  orchestrate <plano> [--dry-run] [--resume] [--yes]
                      [--harness {mimo,opencode,claude,agy}]
                      [--profiles <path>]
                      Gera Flight Plan a partir de um plano ORCA e opcionalmente
                      executa a orquestracao multi-agente.
  plan init|check-fences <args>
                      Gerenciador determinístico de iniciativas de planos em docs/planos/
  audit               Executa o Meta-Quality Gate de Integridade
  status              Exibe o status do ecossistema e ferramentas integradas
  status --testes     Roda pytest real em cada ferramenta e atualiza
                      PLANO-EXECUCAO-ESTRUTURADO.json com a contagem medida
  help                Exibe esta ajuda
""")

def main():
    if len(sys.argv) < 2:
        print_help()
        sys.exit(0)

    cmd = sys.argv[1].lower()
    args = sys.argv[2:]

    dispatch = {
        "forge": cmd_forge,
        "generate": cmd_generate,
        "master": cmd_master,
        "enterprise": cmd_enterprise,
        "components": cmd_components,
        "orchestrate": cmd_orchestrate,
        "plan": cmd_plan,
        "audit": cmd_audit,
        "status": cmd_status,
        "help": lambda a: print_help() or 0,
        "--help": lambda a: print_help() or 0,
        "-h": lambda a: print_help() or 0
    }

    if cmd in dispatch:
        exit_code = dispatch[cmd](args)
        sys.exit(exit_code or 0)
    else:
        print(f"Erro: comando desconhecido '{cmd}'. Digite 'python ecossistema.py help' para ver as opções.")
        sys.exit(1)

if __name__ == "__main__":
    main()