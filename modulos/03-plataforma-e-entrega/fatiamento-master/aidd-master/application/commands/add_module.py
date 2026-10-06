# -*- coding: utf-8 -*-
"""Use Case: add-module / refine-module — fatias verticais e refinamento BDD."""

import os
import subprocess
import sys


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