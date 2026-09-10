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
"""

import os
import sys
import types

# Adiciona a raiz do tool ao sys.path para que `application` (pacote de Use Cases) seja importável.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import click  # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from application.commands.setup import ensure_environment, cmd_setup  # noqa: E402
from application.commands.init import cmd_init  # noqa: E402
from application.commands.compose import cmd_compose, cmd_compose_orca  # noqa: E402
from application.commands.add_module import cmd_add_module, cmd_refine_module  # noqa: E402
from application.commands.test_cmd import cmd_test  # noqa: E402
from application.commands.audit import cmd_audit  # noqa: E402
from application.commands.bench import cmd_bench  # noqa: E402
from application.commands.heal import cmd_heal  # noqa: E402
from application.commands.deploy import cmd_deploy  # noqa: E402
from application.commands.export_frontend import cmd_export_frontend  # noqa: E402
from application.commands.scaffold_infra import cmd_scaffold_infra  # noqa: E402
from application.commands.inject import (  # noqa: E402
    _tentar_injecao_por_linguagem_natural,
    cmd_inject as _cmd_inject_impl,
)
from application.commands.plan import (  # noqa: E402
    cmd_plan,
    cmd_apply,
    parse_natural_language_intent,
)
from application.commands.status import cmd_status  # noqa: E402


def cmd_inject(args):
    """Wrapper casca-fina — delega ao Use Case da camada de aplicação.

    Preservado como def (não re-export puro) para manter compatibilidade
    com G_INJECT._verificar_integracao_cli, que faz substring match em
    ``def cmd_inject(`` no conteúdo deste arquivo.
    """
    return _cmd_inject_impl(args)


_DEFAULT_MODULOS = ["crm", "erp", "helpdesk", "logistica"]


@click.group(
    name="aidd",
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
    help="AIDD Framework CLI — Dividir para Conquistar (v5.1 Enterprise)",
)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        sys.exit(1)


@cli.command(
    "plan",
    help="Gera especificação arquitetural e plano antes de compor. "
         "PROMPT: instrução em linguagem natural (ex: 'Crie um CRM e ERP de faturamento') "
         "— processada por casamento de palavras-chave contra lista fixa de domínios, "
         "SEM uso de LLM/IA generativa",
)
@click.argument("prompt")
@click.option("--dir", default=".", help="Diretório base de destino")
@click.option("--apply", "apply_", is_flag=True, default=False, help="Executa a composição imediatamente após planejar")
def _plan_cmd(prompt, dir, apply_):
    cmd_plan(prompt, dir, apply_)


@cli.command("apply", help="Executa o plano estruturado aprovado e roda os gates")
@click.option("--dir", default=".", help="Diretório do projeto contendo PLANO-EXECUCAO-ESTRUTURADO.json")
def _apply_cmd(dir):
    cmd_apply(types.SimpleNamespace(dir=dir))


@cli.command("bench", help="Executa benchmark local de concorrência no SQLite WAL e EventBus")
@click.option("-n", "n", type=int, default=100, help="Número de operações concorrentes")
@click.option("--dir", default=".", help="Diretório do projeto")
def _bench_cmd(n, dir):
    cmd_bench(types.SimpleNamespace(n=n, dir=dir))


@cli.command("heal", help="Executa auto-remediação determinística de módulos")
@click.option("--dir", default=".", help="Diretório do projeto")
def _heal_cmd(dir):
    cmd_heal(types.SimpleNamespace(dir=dir))


@cli.command(
    "prompt",
    help="Gera aplicação a partir de prompt em linguagem natural. "
         "TEXTO: instrução em linguagem natural (ex: 'Crie um CRM e ERP de faturamento') "
         "— processada por casamento de palavras-chave contra lista fixa de domínios, "
         "SEM uso de LLM/IA generativa",
)
@click.argument("texto")
@click.option("--dir", default=".", help="Diretório base de destino")
def _prompt_cmd(texto, dir):
    parse_natural_language_intent(texto, dir)


@cli.command("setup", help="Executa diagnóstico completo e instalação automática de dependências")
def _setup_cmd():
    cmd_setup(None)


@cli.command("init", help="Provisiona novo projeto modular")
@click.argument("nome")
@click.option("--dir", "--pasta", "dir", default=".", help="Diretório base de destino (--pasta é alias de --dir)")
def _init_cmd(nome, dir):
    cmd_init(types.SimpleNamespace(nome=nome, dir=dir))


@cli.command("compose", help="Compõe suíte empresarial completa")
@click.argument("target_dir")
@click.argument("suite_name")
@click.argument("modulos", nargs=-1)
@click.option("--db", type=click.Choice(["sqlite", "postgres"]), default="sqlite", help="Motor de persistência (default: sqlite)")
def _compose_cmd(target_dir, suite_name, modulos, db):
    cmd_compose(types.SimpleNamespace(
        target_dir=target_dir, suite_name=suite_name,
        modulos=list(modulos) if modulos else list(_DEFAULT_MODULOS), db=db,
    ))


@cli.command("compose-orca", help="Compõe módulos via subagentes efêmeros com context-purge")
@click.option("--dir", default=".", help="Diretório de destino")
@click.option("--suite-name", "suite_name", default="AIDD Suite", help="Nome da suíte empresarial")
@click.argument("modulos", nargs=-1)
def _compose_orca_cmd(dir, suite_name, modulos):
    cmd_compose_orca(types.SimpleNamespace(
        dir=dir, suite_name=suite_name,
        modulos=list(modulos) if modulos else list(_DEFAULT_MODULOS),
    ))


@cli.command("add-module", help="Gera nova fatia vertical desacoplada")
@click.argument("nome")
@click.option("--descricao", "-d", default="", help="Descrição do módulo")
@click.option("--dir", "--pasta", "dir", default=".", help="Diretório do projeto (--pasta é alias de --dir)")
def _add_module_cmd(nome, descricao, dir):
    cmd_add_module(types.SimpleNamespace(nome=nome, descricao=descricao, dir=dir))


@cli.command("test", help="Executa suítes de testes unitários ou de carga")
@click.argument("tipo", required=False, default="unit", type=click.Choice(["unit", "load", "contracts", "all"]))
@click.option("--dir", default=".", help="Diretório do projeto")
def _test_cmd(tipo, dir):
    cmd_test(types.SimpleNamespace(tipo=tipo, dir=dir))


@cli.command("audit", help="Executa a bateria completa de gates determinísticos")
@click.option("--report", is_flag=True, default=False, help="Gera relatório factual RELATORIO-AUDITORIA.json")
@click.option("--json", "json_", is_flag=True, default=False, help="Exporta saída em JSON")
@click.option("--dir", default=".", help="Diretório do projeto")
def _audit_cmd(report, json_, dir):
    cmd_audit(types.SimpleNamespace(report=report, json=json_, dir=dir))


@cli.command("deploy", help="Executa deploy da aplicação")
@click.argument("alvo", required=False, default="docker", type=click.Choice(["docker", "vps", "vercel"]))
def _deploy_cmd(alvo):
    cmd_deploy(types.SimpleNamespace(alvo=alvo))


@cli.command("status", help="Exibe integridade dos módulos e manifesto do projeto")
@click.option("--dir", default=".", help="Diretório do projeto")
def _status_cmd(dir):
    cmd_status(types.SimpleNamespace(dir=dir))


@cli.command("export-frontend", help="Exporta front-end Next.js/TypeScript tipado a partir do OpenAPI")
@click.option("--stack", type=click.Choice(["nextjs"]), default="nextjs", help="Stack de frontend alvo")
@click.option("--dir", default=".", help="Diretório do projeto")
def _export_frontend_cmd(stack, dir):
    cmd_export_frontend(types.SimpleNamespace(dir=dir, stack=stack))


@cli.command("refine-module", help="Executa a suíte BDD (behave) de um módulo até 100% dos cenários passarem")
@click.argument("modulo")
@click.option("--spec", default=None, help="Caminho do arquivo .feature (default: features/<modulo>.feature)")
@click.option("--dir", default=".", help="Diretório do projeto")
def _refine_module_cmd(modulo, spec, dir):
    cmd_refine_module(types.SimpleNamespace(modulo=modulo, spec=spec, dir=dir))


@cli.command("scaffold-infra", help="Gera infraestrutura declarativa Terraform + Helm em infra/")
@click.option("--dir", default=".", help="Diretório do projeto")
def _scaffold_infra_cmd(dir):
    cmd_scaffold_infra(types.SimpleNamespace(dir=dir))


@cli.command(
    "inject",
    help="Injeta e sincroniza um componente (skill, mcp, rule, spec, config, hook, agent) em todos os harnesses",
)
@click.argument("tipo", type=click.Choice(["skill", "mcp", "rule", "spec", "config", "hook", "agent"]))
@click.argument("nome")
@click.option("--descricao", "-d", default="", help="Descrição do componente")
@click.option("--content-file", "content_file", default=None, help="Arquivo com o conteúdo completo do componente")
@click.option("--mcp-command", "mcp_command", default=None, help="[mcp] Comando executável do servidor MCP")
@click.option("--mcp-args", "mcp_args", default=None, help="[mcp] Argumentos separados por vírgula")
@click.option("--mcp-env", "mcp_env", default=None, help="[mcp] Variáveis de ambiente no formato CHAVE=valor,CHAVE2=valor2")
@click.option("--files-json", "files_json", default=None, help="[config] Caminho de um JSON {caminho: conteudo}")
@click.option("--dry-run", "dry_run", is_flag=True, default=False, help="Simula a injeção sem escrever no filesystem")
@click.option("--remover", is_flag=True, default=False, help="Remove um componente previamente injetado")
@click.option("--dir", default=".", help="Diretório do projeto")
def _inject_cmd(tipo, nome, descricao, content_file, mcp_command, mcp_args, mcp_env, files_json, dry_run, remover, dir):
    cmd_inject(types.SimpleNamespace(
        tipo=tipo, nome=nome, descricao=descricao, content_file=content_file,
        mcp_command=mcp_command, mcp_args=mcp_args, mcp_env=mcp_env, files_json=files_json,
        dry_run=dry_run, remover=remover, dir=dir,
    ))


def main():
    known_cmds = {"setup", "init", "plan", "apply", "prompt", "compose", "compose-orca", "add-module", "test", "audit", "bench", "heal", "deploy", "status", "export-frontend", "refine-module", "scaffold-infra", "inject", "-h", "--help"}
    if len(sys.argv) > 1 and sys.argv[1] not in known_cmds:
        raw_prompt = " ".join(sys.argv[1:])
        if _tentar_injecao_por_linguagem_natural(raw_prompt):
            return
        parse_natural_language_intent(raw_prompt)
        return

    cli()


if __name__ == '__main__':
    main()