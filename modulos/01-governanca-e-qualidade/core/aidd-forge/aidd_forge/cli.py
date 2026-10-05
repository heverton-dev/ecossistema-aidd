"""Entrypoint CLI do AIDD Forge.

Uso:
    forge init [path] [--force]
"""

from __future__ import annotations

import sys
from pathlib import Path

import click

from aidd_forge.commands.slash_router import SlashRouter
from aidd_forge.core.git_hooks import GitHooksInstaller
from aidd_forge.core.injector import Injector
from aidd_forge.core.injector_profiles import TIPOS_SUPORTADOS
from aidd_forge.core.phase_fencer import PhaseFencer
from aidd_forge.core.prontidao import HANDOFF_NOME, ProntidaoForge
from aidd_forge.core.universal_injector import UniversalInjector

TEMPLATES_ROOT = Path(__file__).parent / "templates"

# Raiz do toolbox ecossistema-aidd (4 niveis acima deste arquivo:
# aidd_forge/ -> tools/aidd-forge/ -> tools/ -> ecossistema-aidd/), quando
# o aidd-forge estiver rodando dentro do monorepo. Usado para gravar slash
# commands auto-contidos (sem depender de instalacao pip do aidd-forge, que
# pode ficar orfa se o clone do toolbox for movido ou apagado). Ausente
# (None) quando o aidd-forge roda standalone, fora do monorepo.
def _descobrir_ecossistema_script() -> Path | None:
    for parent in Path(__file__).resolve().parents:
        candidato = parent / "ecossistema.py"
        if candidato.is_file():
            return candidato
    candidato = Path(__file__).resolve().parents[3] / "ecossistema.py"
    return candidato if candidato.is_file() else None


_ECOSSISTEMA_SCRIPT = _descobrir_ecossistema_script()
ECOSSISTEMA_SCRIPT = _ECOSSISTEMA_SCRIPT if _ECOSSISTEMA_SCRIPT and _ECOSSISTEMA_SCRIPT.is_file() else None

IDE_RULE_ALIASES = {
    "AGENTS.md": "governance/AGENTS.md",
    "CLAUDE.md": "governance/AGENTS.md",
    "GEMINI.md": "governance/AGENTS.md",
}


def cmd_init(path: str, force: bool) -> int:
    target = Path(path).resolve()
    target.mkdir(parents=True, exist_ok=True)

    injector = Injector(TEMPLATES_ROOT, target, force=force)
    files_result = injector.run()
    links_result = injector.link_ide_rules(IDE_RULE_ALIASES)
    skills_result = injector.link_skills()
    mirror_skills_result = injector.mirror_skills_all_harnesses()

    fencer = PhaseFencer(TEMPLATES_ROOT, target, force=force)
    fence_result = fencer.run()

    router = SlashRouter(target, force=force, ecossistema_script=ECOSSISTEMA_SCRIPT)
    router_result = router.run()

    hooks = GitHooksInstaller(TEMPLATES_ROOT, target, force=force)
    hooks_result = hooks.run()

    print(f"[aidd-forge] projeto alvo: {target}")
    print(f"[aidd-forge] arquivos criados: {len(files_result.created)}")
    print(f"[aidd-forge] arquivos ignorados (ja existem): {len(files_result.skipped)}")
    if files_result.overwritten:
        print(f"[aidd-forge] arquivos sobrescritos: {len(files_result.overwritten)}")
    print(f"[aidd-forge] regras de IDE vinculadas: {len(links_result.created)}")
    print(f"[aidd-forge] skills vinculadas em .agents/skills/: {len(skills_result.created)}")
    print(f"[aidd-forge] fases provisionadas: {len(fence_result.phases)}")
    print(f"[aidd-forge] slash commands gravados: {len(router_result.created)}")
    if router_result.intent_router_injected:
        print("[aidd-forge] Intent Router injetado no AGENTS.md existente")
    print(f"[aidd-forge] quality gates instalados: {len(hooks_result.gate_scripts)}")
    if hooks_result.hook_installed:
        print(f"[aidd-forge] hook pre-commit instalado em: {hooks_result.hook_path}")
    elif hooks_result.skipped_reason:
        print(f"[aidd-forge] hook pre-commit nao instalado: {hooks_result.skipped_reason}")

    # Checklist de prontidao (C1): so passa o bastao com tudo provado.
    resultado = ProntidaoForge(target).executar()
    aprovados = sum(1 for item in resultado.itens if item.ok)
    situacao = "OK" if resultado.ok else "FALHOU"
    print(f"[aidd-forge] prontidao: {situacao} ({aprovados}/{len(resultado.itens)} itens)")
    for item in resultado.itens:
        marca = "OK" if item.ok else "FALHOU"
        print(f"[aidd-forge]   [{marca}] {item.nome}: {item.detalhe}")
        if not item.ok and item.dica:
            print(f"[aidd-forge]   dica: {item.dica}")
    if not resultado.ok:
        print(
            f"[aidd-forge] prontidao reprovada: {HANDOFF_NOME} nao gravado; "
            "corrija os itens acima e rode 'forge init' de novo"
        )
        return 1
    print(f"[aidd-forge] handoff gravado: {resultado.handoff_path}")
    return 0


def cmd_inject(
    tipo: str,
    nome: str,
    descricao: str,
    conteudo: str | None,
    conteudo_file: str | None,
    path: str,
    force: bool,
) -> int:
    target = Path(path).resolve()

    if conteudo_file:
        conteudo_final = Path(conteudo_file).read_text(encoding="utf-8")
    else:
        conteudo_final = conteudo or ""

    payload = {
        "tipo": tipo,
        "nome": nome,
        "descricao": descricao,
        "conteudo": conteudo_final,
    }

    resultado = UniversalInjector(target).injetar(payload, force=force)

    if not resultado.ok:
        print(f"[aidd-forge] injecao de '{nome}' ({tipo}) falhou:")
        for erro in resultado.errors:
            print(f"  - {erro}")
        return 1

    materializacao = resultado.materialization
    print(f"[aidd-forge] componente injetado: {tipo}/{nome} (camada {resultado.camada})")
    print(f"[aidd-forge] arquivo materializado: {materializacao.dest}")
    if materializacao.registry_updated:
        print(f"[aidd-forge] registry atualizado: {materializacao.registry_updated}")
    if materializacao.anchor_updated:
        print(f"[aidd-forge] AGENTS.md atualizado: {materializacao.anchor_updated}")
    if resultado.harness_sync and resultado.harness_sync.mirrored:
        print(f"[aidd-forge] espelhado em harnesses: {len(resultado.harness_sync.mirrored)}")
    return 0


@click.group(name="forge", help="AIDD Forge - motor de governanca agentica e economia de tokens")
def cli() -> None:
    """Grupo raiz do CLI. Garante saída UTF-8 antes de qualquer subcomando
    (os prints com acentos do forge quebram em console cp852/cp1252)."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


@cli.command("init", help="Injeta a infraestrutura AIDD no projeto alvo")
@click.argument("path", required=False, default=".")
@click.option("--force", is_flag=True, default=False, help="Sobrescreve arquivos ja existentes no alvo")
def init_command(path: str, force: bool) -> None:
    sys.exit(cmd_init(path, force))


@cli.command(
    "inject", help="Injeta um novo componente (skill, mcp, rule, spec, roteiro) no projeto alvo"
)
@click.argument("tipo", type=click.Choice(TIPOS_SUPORTADOS))
@click.argument("nome")
@click.option("--descricao", required=True, help="Descricao curta do componente")
@click.option("--conteudo", default=None, help="Conteudo do arquivo a materializar")
@click.option("--conteudo-file", default=None, help="Caminho de um arquivo com o conteudo")
@click.option("--path", default=".", help="Caminho do projeto alvo (padrao: diretorio atual)")
@click.option("--force", is_flag=True, default=False, help="Sobrescreve o destino caso ja exista")
def inject_command(
    tipo: str,
    nome: str,
    descricao: str,
    conteudo: str | None,
    conteudo_file: str | None,
    path: str,
    force: bool,
) -> None:
    if bool(conteudo) == bool(conteudo_file):
        raise click.UsageError(
            "informe exatamente um entre --conteudo e --conteudo-file (mutuamente exclusivos, um deles e obrigatorio)"
        )
    sys.exit(cmd_inject(tipo, nome, descricao, conteudo, conteudo_file, path, force))


@cli.command("audit", help="Audita a conformidade de governanca do projeto alvo")
@click.argument("path", required=False, default=".")
@click.option("--format", "fmt", type=click.Choice(["json", "md", "html"]), default="md", help="Formato do relatorio")
@click.option("--output", type=click.Path(), default=None, help="Arquivo de saida (padrao: stdout)")
def audit_command(path: str, fmt: str, output: str | None) -> None:
    sys.exit(cmd_audit(path, fmt, output))


@cli.command("conform", help="Aplica correcoes automaticas de conformidade")
@click.argument("path", required=False, default=".")
@click.option("--dry-run", is_flag=True, default=False, help="Apenas mostra o que seria feito")
@click.option("--item", "items", multiple=True, type=int, help="Corrige apenas o item especifico (repetivel)")
def conform_command(path: str, dry_run: bool, items: tuple[int, ...]) -> None:
    sys.exit(cmd_conform(path, dry_run, items))


@cli.command("fornecer", help="Entrega uma peca do almoxarifado no projeto alvo")
@click.argument("piece")
@click.option("--destino", required=True, help="Diretorio ou caminho de destino no projeto")
def fornecer_command(piece: str, destino: str) -> None:
    from aidd_forge.core.almoxarifado import obter_peca

    try:
        arquivo_entregue = obter_peca(piece, destino)
        print(f"[aidd-forge] peca fornecida: {piece} -> {arquivo_entregue}")
    except Exception as err:
        print(f"[aidd-forge] erro ao fornecer peca: {err}", file=sys.stderr)
        sys.exit(1)


def cmd_audit(path: str, fmt: str, output: str | None) -> int:
    from aidd_forge.core.audit_engine import AuditEngine
    from aidd_forge.core.audit_report import to_html, to_json, to_markdown

    target = Path(path).resolve()
    engine = AuditEngine(target)
    report = engine.run()

    formatters = {"json": to_json, "md": to_markdown, "html": to_html}
    formatted = formatters[fmt](report)

    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(formatted, encoding="utf-8")
        print(f"[forge audit] report written to: {out_path}")
    else:
        print(formatted)

    print(f"\n[forge audit] compliance: {report.compliance_rate:.1f}% ({report.passed}/{report.total} PASS)")
    return 0 if report.compliance_rate >= 80 else 1


def cmd_conform(path: str, dry_run: bool, items: tuple[int, ...]) -> int:
    from aidd_forge.core.conform_engine import ConformEngine

    target = Path(path).resolve()
    engine = ConformEngine(target)
    item_filter = list(items) if items else None
    report = engine.run(dry_run=dry_run, item_filter=item_filter)

    print(report.summary())
    return 0 if report.failed_fixes == 0 else 1


def main(argv: list[str] | None = None) -> int:
    try:
        cli.main(args=argv, prog_name="forge")
    except SystemExit as exc:
        code = exc.code
        if code is None:
            return 0
        return code if isinstance(code, int) else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
