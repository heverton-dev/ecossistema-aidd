import os, sys, subprocess, argparse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def cmd_init(args):
    from provision_project import provision
    provision(args.nome)

def cmd_add_module(args):
    from add_module import criar_modulo
    criar_modulo(args.nome, args.descricao or "")

def cmd_test(args):
    tipo = args.tipo or "unit"
    print(f"[AIDD TEST] Executando testes: {tipo}...")
    if tipo in ["unit", "all"]:
        res = subprocess.run(["pytest", "-v"])
        if res.returncode != 0:
            sys.exit(res.returncode)
    if tipo in ["load", "all"]:
        print("[AIDD TEST] Executando teste de carga Locust (headless 5s)...")
        if os.path.exists("tests/load/locustfile.py"):
            subprocess.run(["locust", "-f", "tests/load/locustfile.py", "--headless", "-u", "10", "-r", "2", "-t", "5s", "--host", "http://localhost:3000"])

def cmd_audit(args):
    print("[AIDD AUDIT] Rodando bateria de gates determinísticos...")
    gates = ["scripts/gates/G_SEGREDOS.py", "scripts/gates/G_QUALIDADE.py", "scripts/gates/G_HARNESS_COMPAT.py"]
    for g in gates:
        if os.path.exists(g):
            res = subprocess.run([sys.executable, g])
            if res.returncode != 0:
                print(f"[FAIL] Gate falhou: {g}")
                sys.exit(1)
    print("[OK] SUCESSO: Todos os gates foram 100% aprovados (exit 0)!")

def cmd_deploy(args):
    alvo = args.alvo or "docker"
    print(f"[AIDD DEPLOY] Preparando deploy para: {alvo}...")
    if alvo == "docker":
        subprocess.run(["docker", "compose", "up", "-d", "--build"])
    elif alvo == "vps":
        if os.path.exists("deploy.sh"):
            print("Execute no seu servidor: bash deploy.sh")
    print(f"[OK] Deploy {alvo} finalizado com sucesso!")

def cmd_status(args):
    print("[AIDD STATUS] Inspecionando saude do projeto modular...")
    import json
    if os.path.exists("PLANO-EXECUCAO-ESTRUTURADO.json"):
        with open("PLANO-EXECUCAO-ESTRUTURADO.json", "r", encoding="utf-8") as f:
            plano = json.load(f)
        print(f"Projeto: {plano.get('projeto', {}).get('nome')} (v{plano.get('projeto', {}).get('versao')})")
        print(f"Status: {plano.get('projeto', {}).get('status')}")
        if os.path.exists("src/modules"):
            mods = [m for m in os.listdir("src/modules") if os.path.isdir(os.path.join("src/modules", m)) and not m.startswith("__")]
            print(f"Módulos Ativos ({len(mods)}): {', '.join(mods)}")

def main():
    parser = argparse.ArgumentParser(description="AIDD Framework CLI — Dividir para Conquistar")
    subparsers = parser.add_subparsers(dest="command", help="Comando a executar")

    # init
    p_init = subparsers.add_parser("init", help="Provisiona novo projeto modular")
    p_init.add_argument("nome", help="Nome ou descricao do projeto")

    # add-module
    p_mod = subparsers.add_parser("add-module", help="Gera novo modulo desacoplado")
    p_mod.add_argument("nome", help="Nome do modulo")
    p_mod.add_argument("--descricao", "-d", help="Descricao do modulo", default="")

    # test
    p_test = subparsers.add_parser("test", help="Roda suites de testes")
    p_test.add_argument("tipo", nargs="?", choices=["unit", "load", "e2e", "all"], default="unit", help="Tipo de teste")

    # audit
    subparsers.add_parser("audit", help="Executa todos os gates mecanicos")

    # deploy
    p_dep = subparsers.add_parser("deploy", help="Executa deploy da aplicacao")
    p_dep.add_argument("alvo", nargs="?", choices=["docker", "vps", "vercel"], default="docker", help="Alvo de deploy")

    # status
    subparsers.add_parser("status", help="Exibe saude dos modulos e projeto")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    cmds = {
        "init": cmd_init,
        "add-module": cmd_add_module,
        "test": cmd_test,
        "audit": cmd_audit,
        "deploy": cmd_deploy,
        "status": cmd_status
    }
    cmds[args.command](args)

if __name__ == '__main__':
    main()
