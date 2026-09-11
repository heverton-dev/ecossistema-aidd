# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — CLI UNIFICADA DO META-REPOSITÓRIO
=============================================================================
Ponto único de entrada e orquestração do ecossistema-aidd.
Roteia comandos para as 5 ferramentas integradas:
  - forge      -> tools/aidd-forge
  - generate   -> tools/aidd-generator
  - master     -> tools/aidd-master
  - enterprise -> tools/aidd-enterprise
  - aidd-ops   -> tools/aidd-ops (MVP Fases 1-3: Intake, Curadoria, Sizing)
  - audit      -> gates/G_ECOSSISTEMA_INTEGRIDADE.py
  - status     -> Resumo do status do ecossistema
"""

import click
import os
import shutil
import sys
import subprocess
import types

from dotenv import load_dotenv

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(ROOT_DIR, "tools")

# Carrega .env da raiz do ecossistema para os.environ (nunca sobrescreve variavel ja
# exportada no shell — override=False). Cobre esta CLI e todo subprocesso disparado por
# run_command() (forge/generate/master/enterprise/ops), que herda os.environ.copy().
# NAO cobre MCP servers de terceiros lancados diretamente pelo harness (.mcp.json,
# opencode.jsonc etc.) — esses expandem ${VAR} a partir do proprio ambiente do harness,
# nao deste processo. Ver gates/dependencias_externas.json e .env.example.
load_dotenv(os.path.join(ROOT_DIR, ".env"), override=False)

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

def cmd_ops(args):
    ops_dir = os.path.join(TOOLS_DIR, "aidd-ops")
    pipeline_script = os.path.join(ops_dir, "scripts", "pipeline_ops.py")
    env = {"PYTHONPATH": ops_dir}
    cmd = [sys.executable, pipeline_script] + args
    return run_command(cmd, cwd=ops_dir, env=env)

def cmd_bridge(args):
    bridge_dir = os.path.join(TOOLS_DIR, "aidd-bridge")
    env = {"PYTHONPATH": bridge_dir}
    cmd = [sys.executable, "-m", "aidd_bridge.cli"] + args
    return run_command(cmd, cwd=os.getcwd(), env=env)

def cmd_components(args):
    sys.path.insert(0, os.path.join(ROOT_DIR, "scripts"))
    import gestor_componentes

    @click.group(name="components")
    def comp_cli():
        """Sincroniza/verifica distribuicao fisica multi-harness de componentes."""
        pass

    @comp_cli.command("sync")
    @click.option("--tipo", required=True, help="Tipo de componente ou 'todos'")
    @click.option("--ferramenta", default=None, help="Nome da ferramenta alvo")
    @click.option("--dry-run", is_flag=True, default=False, help="Modo simulacao sem escrita")
    @click.option("--force", is_flag=True, default=False,
                  help="Restaura destinos divergentes e orfaos a partir da fonte")
    def sync_cmd(tipo, ferramenta, dry_run, force):
        if force:
            ns = types.SimpleNamespace(tipo=tipo, ferramenta=ferramenta)
            return gestor_componentes._cmd_force_sync(ns)
        ns = types.SimpleNamespace(tipo=tipo, ferramenta=ferramenta, dry_run=dry_run)
        return gestor_componentes._cmd_sync(ns)

    @comp_cli.command("verify")
    @click.option("--tipo", required=True, help="Tipo de componente ou 'todos'")
    @click.option("--ferramenta", default=None, help="Nome da ferramenta alvo")
    def verify_cmd(tipo, ferramenta):
        ns = types.SimpleNamespace(tipo=tipo, ferramenta=ferramenta)
        return gestor_componentes._cmd_verify(ns)

    try:
        rv = comp_cli.main(args=args, prog_name="ecossistema.py components", standalone_mode=False)
        return rv or 0
    except click.ClickException as exc:
        exc.show()
        return 1
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 0
    except ValueError as exc:
        print(f"Erro: {exc}")
        return 1


def cmd_dependencia(args):
    sys.path.insert(0, os.path.join(ROOT_DIR, "scripts"))
    import gestor_dependencias

    @click.group(name="dependencia")
    def dep_cli():
        """Instala/registra skills e MCPs de terceiros."""
        pass

    @dep_cli.command("bootstrap")
    @click.option("--tipo", type=click.Choice(["skills", "mcps", "todos"]), default="todos")
    @click.option("--dry-run", is_flag=True, default=False)
    def bootstrap_cmd(tipo, dry_run):
        ns = types.SimpleNamespace(acao="bootstrap", tipo=tipo, dry_run=dry_run)
        return gestor_dependencias._cmd_bootstrap(ns)

    @dep_cli.command("add-skill")
    @click.option("--nome", required=True)
    @click.option("--pacote", required=True)
    @click.option("--instalar", required=True)
    @click.option("--verificar", required=True)
    @click.option("--gitignore", default="")
    def add_skill_cmd(nome, pacote, instalar, verificar, gitignore):
        ns = types.SimpleNamespace(acao="add-skill", nome=nome, pacote=pacote, instalar=instalar, verificar=verificar, gitignore=gitignore)
        return gestor_dependencias._cmd_add_skill(ns)

    @dep_cli.command("add-mcp")
    @click.option("--nome", required=True)
    @click.option("--pacote", required=True)
    @click.option("--tipo", type=click.Choice(["stdio", "remote"]), default="stdio")
    @click.option("--comando", default=None)
    @click.option("--args", default="")
    @click.option("--env", default="")
    @click.option("--url", default=None)
    @click.option("--harnesses", default="claude-code")
    def add_mcp_cmd(nome, pacote, tipo, comando, args, env, url, harnesses):
        ns = types.SimpleNamespace(
            acao="add-mcp", nome=nome, pacote=pacote, tipo=tipo, comando=comando,
            args=args, env=env, url=url, harnesses=harnesses,
        )
        return gestor_dependencias._cmd_add_mcp(ns)

    @dep_cli.command("list")
    def list_cmd():
        ns = types.SimpleNamespace(acao="list")
        return gestor_dependencias._cmd_list(ns)

    @dep_cli.command("verify")
    def verify_cmd():
        ns = types.SimpleNamespace(acao="verify")
        return gestor_dependencias._cmd_verify(ns)

    try:
        rv = dep_cli.main(args=args, prog_name="ecossistema.py dependencia", standalone_mode=False)
        return rv or 0
    except click.ClickException as exc:
        exc.show()
        return 1
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 0




def cmd_orchestrate(args):
    @click.command(
        name="orchestrate",
        context_settings={"help_option_names": ["-h", "--help"]},
    )
    @click.argument("plano", required=True)
    @click.option("--dry-run", is_flag=True, default=False, help="Apenas gera e imprime o Flight Plan, sem tocar em git ou spawnar agentes.")
    @click.option("--resume", is_flag=True, default=False, help="Retoma um Flight Plan previamente iniciado (crash recovery).")
    @click.option("--yes", is_flag=True, default=False, help="Nao pede confirmacao interativa do Plano de Voo.")
    @click.option("--stream", is_flag=True, default=False, help="Exibe a saida dos agentes em tempo real no console.")
    @click.option("--interactive", is_flag=True, default=True, help="Executa as worktrees em modo interativo com terminal conectado ao usuario (padrao).")
    @click.option("--dangerously-force-headless", is_flag=True, default=False, help="AVISO: Forca execucao headless desassistida (alto risco de consumo de tokens).")
    @click.option(
        "--ambiente", default=None,
        type=click.Choice(["orca", "subagent", "gitworktree"]),
        help="Ambiente de execucao: 'orca' (aplicativo ORCA real, via orca-cli — worktree/terminal "
             "de verdade), 'subagent' (Agent tool da sessao atual, sem worktree, contexto "
             "compartilhado) ou 'gitworktree' (motor nativo deste projeto — git worktree + "
             "harness spawnado direto, sem precisar do app ORCA instalado). "
             "Se omitido, pergunta interativamente.",
    )
    @click.option(
        "--harness", default=None,
        type=click.Choice(["mimo", "opencode", "claude", "agy"]),
        help="Harness padrao para ambiente orca/gitworktree (se omitido, pergunta interativamente)",
    )
    @click.option(
        "--harness-map", default=None,
        help="Mapeamento customizado por frente pra ambiente orca/gitworktree (ex: frente1=claude,frente2=agy)",
    )
    @click.option(
        "--profiles", default=None,
        help="Caminho para harness_profiles.json (default: .orca/harness_profiles.json.example)",
    )
    @click.option(
        "--subagent-type", default="general-purpose",
        help="Subagent type padrao pra ambiente subagent (default: general-purpose)",
    )
    @click.option(
        "--model", default=None,
        help="Override de modelo padrao pra ambiente subagent (se omitido, usa o default da sessao)",
    )
    @click.option(
        "--repo-path", default=None,
        help="Caminho do repositorio real para ambiente orca (default: raiz do monorepo)",
    )
    @click.option(
        "--parent-worktree", default=None,
        help="Selector --parent-worktree do app ORCA real (default: 'active') — mesa SEMPRE filha, "
             "nunca solta ('--no-parent' nao e suportado por design).",
    )
    @click.option(
        "--from-flight-plan", default=None,
        help="Caminho pra um Flight Plan JSON ja compilado (possivelmente editado a mao) — "
             "pula a recompilacao e usa esse arquivo como fonte da verdade antes de confirmar.",
    )
    def orchestrate_cli(plano, dry_run, resume, yes, stream, interactive, dangerously_force_headless, ambiente, harness, harness_map, profiles, subagent_type, model, repo_path, parent_worktree, from_flight_plan):
        orchestrator_root = os.path.join(
            ROOT_DIR, "componentes", "compartilhado", "skills", "orca-plan-orchestrator"
        )
        sys.path.insert(0, orchestrator_root)

        from pathlib import Path
        from scripts.plan_parser import parse_plan
        from scripts.flight_plan import gerar_plano_de_voo, renderizar_plano_de_voo
        from scripts.subagent_plan import compilar_plano_subagentes, renderizar_plano_subagentes
        from scripts.orca_real_plan import compilar_plano_orca, renderizar_plano_orca, PARENT_WORKTREE_PADRAO
        from scripts.plan_io import salvar_plano_de_voo, carregar_plano_de_voo
        from scripts.orchestrator_engine import executar_orquestracao
        from scripts.state_engine import load_state

        plano_dir = Path(ROOT_DIR) / plano if not os.path.isabs(plano) else Path(plano)
        flight_plan_path = plano_dir / ".orca-flight-plan.json"

        if ambiente is None:
            if sys.stdin.isatty() and not yes and not dry_run and not dangerously_force_headless:
                print("\n" + "=" * 65)
                print("  ORCA ADE — AMBIENTE DE EXECUÇÃO")
                print("=" * 65)
                print("""
  1) ORCA (aplicativo real, via orca-cli)
     Worktree e terminal de verdade dentro do app ORCA instalado.
     Mesa sempre criada como filha da mesa ativa (nunca solta).
     Recomendado quando o app ORCA esta instalado e voce quer
     acompanhar/monitorar cada frente pela interface do ORCA.

  2) Subagentes (Agent tool desta sessão)
     Sem worktree, sem terminal separado. Roda dentro do contexto da
     conversa atual via subagente. SEM isolamento de arquivo — evite
     se frentes distintas tocarem os mesmos arquivos.

  3) Git Worktree nativo (motor deste projeto, sem o app ORCA)
     Isolamento de arquivo real via git worktree puro + harness
     spawnado direto por este CLI. Recomendado quando o app ORCA nao
     esta instalado e Subagentes gastaria tokens demais/contexto
     compartilhado nao serve.
""")
                try:
                    escolha_ambiente = input("Escolha o ambiente (default: 1 - ORCA): ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("\n[CANCELADO] Seleção cancelada pelo usuário.")
                    return 1
                if escolha_ambiente in ("2", "subagent", "subagentes"):
                    ambiente = "subagent"
                elif escolha_ambiente in ("3", "gitworktree", "git-worktree"):
                    ambiente = "gitworktree"
                else:
                    ambiente = "orca"
            else:
                ambiente = "gitworktree"

        if ambiente == "orca":
            if profiles is None:
                profiles = os.path.join(
                    ROOT_DIR, "componentes", "compartilhado", "skills",
                    "orca-plan-orchestrator", ".orca", "harness_profiles.json.example",
                )
            harness_map_pars = {}
            if harness_map:
                import json
                try:
                    harness_map_pars = json.loads(harness_map)
                except Exception:
                    for par in harness_map.split(","):
                        if "=" in par:
                            k, v = par.split("=", 1)
                            harness_map_pars[k.strip()] = v.strip()

            if from_flight_plan:
                data = carregar_plano_de_voo(from_flight_plan)
            else:
                try:
                    data = compilar_plano_orca(
                        plano, profiles, repo_path or ROOT_DIR,
                        harness=harness or "claude",
                        harness_map=harness_map_pars or None,
                        parent_worktree=parent_worktree or PARENT_WORKTREE_PADRAO,
                    )
                except (FileNotFoundError, ValueError, KeyError) as exc:
                    print(f"Erro ao gerar Flight Plan para o ORCA real: {exc}")
                    return 1
                salvar_plano_de_voo(data, flight_plan_path)

            print(renderizar_plano_orca(data))
            print(f"[FLIGHT PLAN] Salvo em: {flight_plan_path}")
            print(
                "[ORCA ADE] Ambiente 'orca' nunca e executado por este CLI — ecossistema.py e um "
                "compilador mecanico, sem acesso ao orca-cli. Revise/edite o JSON acima e peca ao "
                "assistente da sessao pra executar cada frente via orca-cli (worktree create "
                f"--parent-worktree {data['parent_worktree']} -> terminal create -> terminal send), "
                "seguindo o protocolo completo em componentes/compartilhado/skills/orchestrate/SKILL.md."
            )
            return 0

        if ambiente == "subagent":
            subagent_map = {}
            model_map = {}

            if from_flight_plan:
                data = carregar_plano_de_voo(from_flight_plan)
            else:
                try:
                    data = compilar_plano_subagentes(
                        plano,
                        subagent_type=subagent_type,
                        model=model,
                        subagent_map=subagent_map or None,
                        model_map=model_map or None,
                    )
                except (FileNotFoundError, ValueError, KeyError) as exc:
                    print(f"Erro ao gerar Flight Plan de subagentes: {exc}")
                    return 1
                salvar_plano_de_voo(data, flight_plan_path)

            print(renderizar_plano_subagentes(data))
            print(f"[FLIGHT PLAN] Salvo em: {flight_plan_path}")
            print(
                "[ORCA ADE] Ambiente 'subagent' nunca é executado por este CLI — "
                "ecossistema.py é um compilador mecânico, sem acesso a modelo/Agent tool. "
                "Revise/edite o JSON acima e peça ao assistente da sessão pra executar "
                "cada frente via Agent tool seguindo o Plano de Voo confirmado "
                "(protocolo completo em componentes/compartilhado/skills/orchestrate/SKILL.md)."
            )
            return 0

        if profiles is None:
            profiles = os.path.join(
                ROOT_DIR, "componentes", "compartilhado", "skills",
                "orca-plan-orchestrator", ".orca", "harness_profiles.json.example",
            )

        candidatos = ["claude", "agy", "mimo", "opencode"]

        harness_map_pars = {}
        if harness_map:
            try:
                import json
                harness_map_pars = json.loads(harness_map)
            except Exception:
                for par in harness_map.split(","):
                    if "=" in par:
                        k, v = par.split("=", 1)
                        harness_map_pars[k.strip()] = v.strip()

        is_interactive = not dangerously_force_headless
        harness_escolhido = harness

        if harness_escolhido is None and not harness_map_pars:
            if sys.stdin.isatty() and not yes and not dry_run:
                print("\n" + "=" * 65)
                print("  ORCA ADE — CONFIGURAÇÃO DO PLANO DE VOO & HARNESSES")
                print("=" * 65)

                if dangerously_force_headless:
                    print("\n[AVISO CRITICO] Modo headless forcado via flag --dangerously-force-headless!")
                else:
                    print("\n[MODO OPERACAO] Sessao INTERATIVA ativada (Desenvolvedor no controle absoluto).")

                try:
                    plan_obj = parse_plan(plano)
                    state_file = Path(ROOT_DIR) / ".orca" / ".orca_state.json"
                    st = load_state(state_file) if state_file.exists() else {"fronts": {}}

                    concluidas = [f.name for f in plan_obj.fronts if st.get("fronts", {}).get(f.name, {}).get("state") == "MERGED"]
                    pendentes = [f.name for f in plan_obj.fronts if f.name not in concluidas]

                    if concluidas:
                        print(f"\n[ORCA ADE] Frentes já concluídas ({len(concluidas)}): {', '.join(concluidas)} (serão puladas)")
                    print(f"[ORCA ADE] Frentes pendentes ({len(pendentes)}): {', '.join(pendentes)}")

                    modo_sel = input("\nModo de Atribuição:\n  1) Multi-Harness por Frente (Recomendado - escolher para cada fase)\n  2) Global único para todas\nEscolha (default: 1): ").strip()

                    if modo_sel in ("2", "global"):
                        print("\nEscolha o Harness Global:")
                        for idx, h in enumerate(candidatos, 1):
                            caminho = shutil.which(h)
                            tag = f"[INSTALADO: {caminho}]" if caminho else "[NÃO DETECTADO NO PATH]"
                            print(f"  {idx}) {h:<10} {tag}")
                        escolha = input("\nEscolha o número do harness (default: 1 - claude): ").strip()
                        map_num = {"1": "claude", "2": "agy", "3": "mimo", "4": "opencode", "": "claude"}
                        harness_escolhido = map_num.get(escolha, "claude")
                    else:
                        print("\n[ORCA ADE] Atribuição Individual por Frente (1: claude | 2: agy | 3: mimo | 4: opencode):")
                        map_num = {"1": "claude", "2": "agy", "3": "mimo", "4": "opencode"}
                        for f_name in pendentes:
                            resp = input(f"  -> Frente '{f_name}' (default: 1 - claude): ").strip()
                            harness_map_pars[f_name] = map_num.get(resp, resp if resp in candidatos else "claude")
                        harness_escolhido = "claude"
                except (EOFError, KeyboardInterrupt):
                    print("\n[CANCELADO] Seleção cancelada pelo usuário.")
                    return 1
            else:
                harness_escolhido = "claude" if shutil.which("claude") else "mimo"

        if harness_escolhido is None:
            harness_escolhido = "claude" if shutil.which("claude") else "mimo"

        if harness_map_pars:
            print(f"[ORCA ADE] Multi-Harness mapeado para {len(harness_map_pars)} frente(s): {harness_map_pars}")
        else:
            print(f"[ORCA ADE] Harness Executor global: {harness_escolhido}")

        if dry_run:
            try:
                data = gerar_plano_de_voo(
                    plano, profiles, harness=harness_escolhido, harness_map=harness_map_pars or None, interactive=is_interactive
                )
            except (FileNotFoundError, ValueError, KeyError) as exc:
                print(f"Erro ao gerar Flight Plan: {exc}")
                return 1
            salvar_plano_de_voo(data, flight_plan_path)
            print(renderizar_plano_de_voo(data))
            print(f"[FLIGHT PLAN] Salvo em: {flight_plan_path}")
            print(
                "[DRY-RUN] Flight Plan gerado com sucesso. Nenhuma acao executada. "
                "Para ajustar harness/modelo por frente, edite --harness-map ou --profiles "
                "e rode o dry-run de novo — o motor de worktree recompila deterministicamente "
                "a partir desses parametros, nao le o JSON salvo acima."
            )
            return 0

        # Marca o plano como EM EXECUCAO de verdade e move para docs/planos/fazendo/
        # AQUI - exatamente no instante em que a orquestracao real comeca, nunca
        # antes (dry-run/compilacao nao chega a este ponto do codigo).
        gerenciador_planos = os.path.join(ROOT_DIR, "scripts", "gerenciador_planos.py")
        run_command([sys.executable, gerenciador_planos, "iniciar-execucao", plano], cwd=ROOT_DIR)

        try:
            return executar_orquestracao(
                plano,
                profiles,
                harness=harness_escolhido,
                harness_map=harness_map_pars or None,
                resume=resume,
                yes=yes,
                stream=stream or is_interactive,
                interactive=is_interactive,
            )
        except (FileNotFoundError, ValueError, KeyError, RuntimeError) as exc:
            print(f"Erro na orquestracao: {exc}")
            return 1

    try:
        rv = orchestrate_cli.main(args=args, prog_name="ecossistema.py orchestrate", standalone_mode=False)
        return rv or 0
    except click.exceptions.Exit as exc:
        return exc.exit_code or 0
    except click.ClickException as exc:
        exc.show()
        return 1
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 0


def cmd_plan(args):
    script = os.path.join(ROOT_DIR, "scripts", "gerenciador_planos.py")
    return run_command([sys.executable, script] + args, cwd=ROOT_DIR)

def cmd_melhoria(args):
    script = os.path.join(ROOT_DIR, "scripts", "gerenciador_melhorias.py")
    return run_command([sys.executable, script] + args, cwd=ROOT_DIR)

# Gates realmente materializados em gates/ e executados pelo 'audit'.
# Ordem identica a AGENTS.md §4 (inclui G_HADOLINT, que jah existe em gates/).
_GATES_AUDIT = [
    "G_ECOSSISTEMA_INTEGRIDADE.py",
    "G_DRIFT_NUCLEO_COMPARTILHADO.py",
    "G_HARNESS_COMPAT.py",
    "G_SEGREDOS.py",
    "G_CLI_HELP_CONSISTENCIA.py",
    "G_COMPONENTE_AGNOSTICO.py",
    "G_ZERO_HEADLESS.py",
    "G_INFRA_COMPOSE.py",
    "G_HADOLINT.py",
    "G_TESTES_REAIS.py",
]

def _audit_gates_legado(args):
    for gate in _GATES_AUDIT:
        gate_script = os.path.join(ROOT_DIR, "gates", gate)
        codigo = run_command([sys.executable, gate_script] + args, cwd=ROOT_DIR)
        if codigo != 0:
            return codigo
    return 0

def cmd_audit(args):
    # NIH #4 (Fase 2-Gates3): o runner proprio dos quality gates foi
    # substituido pelo framework pre-commit. 'audit' DELEGA para
    # 'pre-commit run --all-files', que roda os mesmos gates do _GATES_AUDIT
    # acima agora como hooks locais em .pre-commit-config.yaml.
    # G_HONESTIDADE_ROTULO segue fora do audit agregado (stages manual,
    # conforme AGENTS.md §4 — decisao humana pendente).
    import importlib.util
    if importlib.util.find_spec("pre_commit") is None:
        print("[audit] AVISO: pre-commit nao instalado — usando runner legado "
              "(gates direto). Instale com: pip install pre-commit")
        return _audit_gates_legado(args)
    print("[audit] Delegando para o framework pre-commit "
          "('pre-commit run --all-files')...")
    return run_command(
        [sys.executable, "-m", "pre_commit", "run", "--all-files"], cwd=ROOT_DIR
    )

def cmd_status(args):
    if "--testes" in args:
        sys.path.insert(0, os.path.join(ROOT_DIR, "scripts", "manutencao"))
        from gerar_status_testes import gerar
        escrever = "--write" in args
        gerar(escrever=escrever)
        return 0

    print_banner()
    print("\nFerramentas Integradas em tools/:")
    tools = [
        ("aidd-forge", "Bootstrap, governança, fatiamento e context-purge"),
        ("aidd-generator", "Fábrica autônoma de software (Pipeline 8 fases)"),
        ("aidd-master", "Suíte Modular com Fatias Verticais e SQLite WAL"),
        ("aidd-enterprise", "Missão crítica, conformidade SHA-256 e Zero-Trust"),
        ("aidd-ops", "Meta-Orquestrador Agêntico de Infraestrutura (Pacote 3)"),
        ("aidd-bridge", "Extrator, unificador e empacotador Lovable/VPS")
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
        "aidd-ops-runner",
        "aidd-bridge-runner",
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
    print("  /ops [requisito]        -> Dispara aidd-ops (infraestrutura)")
    print("  /orchestrate [plano]    -> Dispara orca-plan-orchestrator (ORCA ADE)")
    print("  /melhoria <pedido>      -> Dispara analise profunda pre-planejamento (docs/melhorias/)")
    print("  /plan <nome>            -> Dispara planos-auditoria-runner")
    print("  /bridge [comando]       -> Dispara aidd-bridge-runner")
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
  ops <args>          Executa o pipeline do aidd-ops (ex: ops "<texto>" --pasta <dest>)
  bridge <args>       Executa comandos do aidd-bridge (scan, convert-db, merge, pack)
  components sync|verify --tipo <tipo|todos> [--ferramenta <nome>] [--dry-run]
                      Sincroniza/verifica distribuicao fisica multi-harness de
                      componentes (gates/manifesto_harnesses.json)
  dependencia bootstrap [--tipo skills|mcps|todos] [--dry-run]
  dependencia add-skill --nome <n> --pacote <p> --instalar "<cmd>" --verificar <caminho> [--gitignore "a,b"]
  dependencia add-mcp --nome <n> --pacote <p> --comando <cmd> [--args "a,b"] [--env V1,V2] [--harnesses claude-code,opencode]
  dependencia add-mcp --nome <n> --pacote <p> --tipo remote --url <url> [--harnesses claude-code,opencode]
  dependencia list|verify
                      Instala/registra skills e MCPs de terceiros usados pelo
                      agente (gates/dependencias_externas.json)
  orchestrate <plano> [--dry-run] [--resume] [--yes]
                      [--ambiente {orca,subagent,gitworktree}]
                      [--harness {mimo,opencode,claude,agy}] [--harness-map ...]
                      [--subagent-type <tipo>] [--model <modelo>]
                      [--repo-path <path>] [--parent-worktree <selector>]
                      [--profiles <path>] [--from-flight-plan <path>]
                      Gera Flight Plan a partir de um plano ORCA. Cada ambiente
                      compila um JSON no formato certo pra ele, nenhum e
                      executado por este CLI (sempre revisado e disparado pelo
                      assistente da sessao): 'orca' monta o plano pro app ORCA
                      real via orca-cli (worktree create --parent-worktree
                      ativo -> terminal create -> terminal send); 'subagent'
                      compila pra execucao via Agent tool da sessao; 'gitworktree'
                      executa de verdade a orquestracao multi-agente nativa
                      deste projeto (git worktrees + harness spawnado direto,
                      sem precisar do app ORCA).
  melhoria init --pedido "<texto>" [--nome ...] [--nota-atual ...] [--evidencia ...]
                      [--plano-existente <caminho> [--item <NN>]]
                      [--itens-avaliados "<item>::<feito|parcial|nao-feito>::<justificativa>" ...]
                      Gerenciador determinístico de relatórios de análise profunda
                      em docs/melhorias/ (etapa anterior ao 'plan'). Com
                      --plano-existente, reanalisa o código real e compara com a
                      Nota Atual já registrada naquele plano/item (Nota Anterior ->
                      Nota Nova, e tabela previsto-vs-implementado por item).
  plan init|check-fences|ler-nota|atualizar-nota|aprovar|iniciar-execucao <args>
                      Gerenciador determinístico de iniciativas de planos em docs/planos/
                      (--notas-atuais/--notas-alvo/--evidencias por item e
                      --nota-atual-geral/--nota-alvo-geral/--evidencia-geral no init).
                      'ler-nota <caminho> [--item <NN>]' le a Nota Atual/evidencia
                      registrada (JSON; NAO AUDITADO se o plano for anterior a esta
                      métrica). 'atualizar-nota <caminho> [--item <NN>] --nota-atual
                      <n> --evidencia <texto>' grava uma nota nova por cima da
                      existente (nunca mexe em Nota Alvo/Real; evidência obrigatória).
                      'aprovar <caminho>' aprova TODOS os itens de uma vez e move
                      docs/planos/<nome>/ -> docs/planos/a-fazer/<nome>/. 'iniciar-execucao
                      <caminho>' marca EM EXECUCAO de verdade e move -> docs/planos/fazendo/
                      (chamado automaticamente pelo 'orchestrate' no instante real do início).
  audit               Executa o Meta-Quality Gate de Integridade
  status              Exibe o status do ecossistema e ferramentas integradas
  status --testes     Roda pytest real em cada ferramenta e atualiza
                      PLANO-EXECUCAO-ESTRUTURADO.json com a contagem medida
  help                Exibe esta ajuda
""")

def main():
    # Windows abre stdout/stderr no codepage local (cp1252), que não
    # representa emojis/travessões usados nas mensagens do CLI — força UTF-8
    # (mesmo padrao de scripts/atualizar_index_planos.py).
    for fluxo in (sys.stdout, sys.stderr):
        if hasattr(fluxo, "reconfigure"):
            fluxo.reconfigure(encoding="utf-8")

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
        "ops": cmd_ops,
        "bridge": cmd_bridge,
        "components": cmd_components,
        "dependencia": cmd_dependencia,
        "orchestrate": cmd_orchestrate,
        "plan": cmd_plan,
        "melhoria": cmd_melhoria,
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
