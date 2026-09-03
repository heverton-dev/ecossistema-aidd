"""Entrypoint CLI do AIDD Forge.

Uso:
    forge init [path] [--force]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from aidd_forge.commands.slash_router import SlashRouter
from aidd_forge.core.git_hooks import GitHooksInstaller
from aidd_forge.core.injector import Injector
from aidd_forge.core.injector_profiles import TIPOS_SUPORTADOS
from aidd_forge.core.phase_fencer import PhaseFencer
from aidd_forge.core.universal_injector import UniversalInjector

TEMPLATES_ROOT = Path(__file__).parent / "templates"

IDE_RULE_ALIASES = {
    "CLAUDE.md": "governance/AGENTS.md",
}


def cmd_init(args: argparse.Namespace) -> int:
    target = Path(args.path).resolve()
    target.mkdir(parents=True, exist_ok=True)

    injector = Injector(TEMPLATES_ROOT, target, force=args.force)
    files_result = injector.run()
    links_result = injector.link_ide_rules(IDE_RULE_ALIASES)
    skills_result = injector.link_skills()

    fencer = PhaseFencer(TEMPLATES_ROOT, target, force=args.force)
    fence_result = fencer.run()

    router = SlashRouter(target, force=args.force)
    router_result = router.run()

    hooks = GitHooksInstaller(TEMPLATES_ROOT, target, force=args.force)
    hooks_result = hooks.run()

    print(f"[aidd-forge] projeto alvo: {target}")
    print(f"[aidd-forge] arquivos criados: {len(files_result.created)}")
    print(f"[aidd-forge] arquivos ignorados (ja existem): {len(files_result.skipped)}")
    if files_result.overwritten:
        print(f"[aidd-forge] arquivos sobrescritos: {len(files_result.overwritten)}")
    print(f"[aidd-forge] regras de IDE vinculadas: {len(links_result.created)}")
    print(f"[aidd-forge] skills vinculadas em .agent/skills/: {len(skills_result.created)}")
    print(f"[aidd-forge] fases provisionadas: {len(fence_result.phases)}")
    print(f"[aidd-forge] slash commands gravados: {len(router_result.created)}")
    if router_result.intent_router_injected:
        print("[aidd-forge] Intent Router injetado no AGENTS.md existente")
    print(f"[aidd-forge] quality gates instalados: {len(hooks_result.gate_scripts)}")
    if hooks_result.hook_installed:
        print(f"[aidd-forge] hook pre-commit instalado em: {hooks_result.hook_path}")
    elif hooks_result.skipped_reason:
        print(f"[aidd-forge] hook pre-commit nao instalado: {hooks_result.skipped_reason}")
    return 0


def cmd_inject(args: argparse.Namespace) -> int:
    target = Path(args.path).resolve()

    if args.conteudo_file:
        conteudo = Path(args.conteudo_file).read_text(encoding="utf-8")
    else:
        conteudo = args.conteudo or ""

    payload = {
        "tipo": args.tipo,
        "nome": args.nome,
        "descricao": args.descricao,
        "conteudo": conteudo,
    }

    resultado = UniversalInjector(target).injetar(payload, force=args.force)

    if not resultado.ok:
        print(f"[aidd-forge] injecao de '{args.nome}' ({args.tipo}) falhou:")
        for erro in resultado.errors:
            print(f"  - {erro}")
        return 1

    materializacao = resultado.materialization
    print(f"[aidd-forge] componente injetado: {args.tipo}/{args.nome} (camada {resultado.camada})")
    print(f"[aidd-forge] arquivo materializado: {materializacao.dest}")
    if materializacao.registry_updated:
        print(f"[aidd-forge] registry atualizado: {materializacao.registry_updated}")
    if materializacao.anchor_updated:
        print(f"[aidd-forge] AGENTS.md atualizado: {materializacao.anchor_updated}")
    if resultado.harness_sync and resultado.harness_sync.mirrored:
        print(f"[aidd-forge] espelhado em harnesses: {len(resultado.harness_sync.mirrored)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="forge",
        description="AIDD Forge - motor de governanca agentica e economia de tokens",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser(
        "init", help="Injeta a infraestrutura AIDD no projeto alvo"
    )
    init_parser.add_argument(
        "path", nargs="?", default=".", help="Caminho do projeto alvo (padrao: diretorio atual)"
    )
    init_parser.add_argument(
        "--force", action="store_true", help="Sobrescreve arquivos ja existentes no alvo"
    )
    init_parser.set_defaults(func=cmd_init)

    inject_parser = subparsers.add_parser(
        "inject", help="Injeta um novo componente (skill, mcp, rule, spec, roteiro) no projeto alvo"
    )
    inject_parser.add_argument("tipo", choices=TIPOS_SUPORTADOS, help="Tipo do componente")
    inject_parser.add_argument("nome", help="Nome do componente (kebab-case)")
    inject_parser.add_argument("--descricao", required=True, help="Descricao curta do componente")
    conteudo_group = inject_parser.add_mutually_exclusive_group(required=True)
    conteudo_group.add_argument("--conteudo", help="Conteudo do arquivo a materializar")
    conteudo_group.add_argument("--conteudo-file", help="Caminho de um arquivo com o conteudo")
    inject_parser.add_argument(
        "--path", default=".", help="Caminho do projeto alvo (padrao: diretorio atual)"
    )
    inject_parser.add_argument(
        "--force", action="store_true", help="Sobrescreve o destino caso ja exista"
    )
    inject_parser.set_defaults(func=cmd_inject)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
