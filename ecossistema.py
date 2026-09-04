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
  - enterprise -> tools/aidd-master-enterprise
  - audit      -> gates/G_ECOSSISTEMA_INTEGRIDADE.py
  - status     -> Resumo do status do ecossistema
"""

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
    ent_dir = os.path.join(TOOLS_DIR, "aidd-master-enterprise")
    aidd_script = os.path.join(ent_dir, "scripts", "aidd.py")
    env = {"PYTHONPATH": ent_dir}
    cmd = [sys.executable, aidd_script] + args
    return run_command(cmd, cwd=ent_dir, env=env)

def cmd_audit(args):
    gates = [
        "G_ECOSSISTEMA_INTEGRIDADE.py",
        "G_DRIFT_NUCLEO_COMPARTILHADO.py",
        "G_HARNESS_COMPAT.py",
        "G_SEGREDOS.py",
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
        ("aidd-master-enterprise", "Missão crítica, conformidade SHA-256 e Zero-Trust")
    ]
    for name, desc in tools:
        path = os.path.join(TOOLS_DIR, name)
        status = "[OK] Instalado" if os.path.isdir(path) else "[FALTA] Não encontrado"
        print(f"  - {name:<24} {status:<16} {desc}")

    print("\nSkills Universais:")
    for skill in ["aidd-forge-runner", "aidd-generator-runner", "aidd-master-runner", "aidd-enterprise-runner"]:
        path = os.path.join(ROOT_DIR, "skills", skill, "SKILL.md")
        status = "[OK]" if os.path.exists(path) else "[AUSENTE]"
        print(f"  - {skill:<26} {status}")

    print("\nSlash Commands Ativos:")
    print("  /forge [caminho]        -> Dispara aidd-forge")
    print("  /generate <ideia>       -> Dispara aidd-generator")
    print("  /master <modulo>        -> Dispara aidd-master")
    print("  /enterprise <tipo> <nome> -> Dispara aidd-master-enterprise")
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
  enterprise <args>   Executa comandos do aidd-master-enterprise (ex: enterprise inject skill auth)
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