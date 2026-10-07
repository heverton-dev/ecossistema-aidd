# -*- coding: utf-8 -*-
"""
AIDD-Forge CLI: entrada deterministica da skill aidd-forge (D4 / DoD 1).

Ponto unico de entrada local de `python ecossistema.py forge <args>`:
- Subcomandos declarativos (init, inject, audit, conform) validados por argparse.
- exit 1 em parametros faltantes ou entrada nao tratada (nunca exit 2).
- Delegacao direta ao pacote local modulos/01-governanca-e-qualidade/core/aidd-forge (scripts do repositorio),
  sem nenhuma interpretacao por prompt de LLM.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


def encontrar_raiz_repositorio() -> Optional[Path]:
    """Localiza a raiz do repositorio procurando por ecossistema.py."""
    atual = Path(__file__).resolve()
    for candidato in [atual, *atual.parents]:
        if (candidato / "ecossistema.py").is_file():
            return candidato
    return None


def raiz_pacote_local() -> Optional[Path]:
    """Raiz do pacote local modulos/01-governanca-e-qualidade/core/aidd-forge quando presente neste repositorio."""
    raiz = encontrar_raiz_repositorio()
    if raiz is None:
        return None
    pacote = raiz / "modulos" / "01-governanca-e-qualidade" / "core" / "aidd-forge"
    if (pacote / "aidd_forge" / "cli.py").is_file():
        return pacote
    return None


def executar_script_local(argumentos: List[str]) -> int:
    """
    Delega os argumentos ja validados ao pacote local aidd_forge.
    Levanta RuntimeError quando o pacote local nao esta disponivel.
    """
    pacote = raiz_pacote_local()
    if pacote is None:
        raise RuntimeError("pacote local modulos/01-governanca-e-qualidade/core/aidd-forge nao encontrado")

    raiz_str = str(pacote)
    if raiz_str not in sys.path:
        sys.path.insert(0, raiz_str)

    from aidd_forge.cli import main as main_pacote  # type: ignore[import-not-found]

    return int(main_pacote(list(argumentos)))


HANDOFF_ARQUIVO = "handoff-forge.json"
COMPONENTES_PADRAO = [
    ".agents/skills/aidd-forge/scripts/isolamento.py",
    ".agents/skills/aidd-forge/scripts/cli.py",
    ".agents/skills/aidd-forge/scripts/bootstrap.py",
    ".agents/skills/aidd-forge/scripts/orquestracao.py",
    ".agents/skills/aidd-forge/scripts/resiliencia.py",
    ".agents/skills/aidd-forge/scripts/observabilidade.py",
    ".agents/skills/aidd-forge/scripts/rollback.py",
    "modulos/01-governanca-e-qualidade/gates/G_aidd_forge.py",
]


def montar_handoff(raiz: Path, componentes: List[str]) -> dict:
    """Monta o manifesto estruturado de handoff com SHA-256 de cada componente."""
    itens = []
    for relativo in componentes:
        caminho = raiz / relativo
        if not caminho.is_file():
            raise FileNotFoundError(f"componente inexistente para handoff: {relativo}")
        itens.append(
            {
                "caminho": relativo,
                "sha256": hashlib.sha256(caminho.read_bytes()).hexdigest(),
                "bytes": caminho.stat().st_size,
            }
        )
    return {
        "versao": "1.0",
        "ferramenta": "aidd-forge",
        "consumidor": "aidd-planner",
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "componentes": itens,
    }


def emitir_handoff(raiz: Path, componentes: List[str]) -> Path:
    dados = montar_handoff(raiz, componentes)
    destino = raiz / HANDOFF_ARQUIVO
    destino.write_text(json.dumps(dados, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return destino


def verificar_handoff(raiz: Path, componentes: List[str]) -> int:
    """exit 1 se o handoff estiver ausente, invalido ou com hash divergente."""
    arquivo = raiz / HANDOFF_ARQUIVO
    if not arquivo.is_file():
        print(f"[aidd-forge] handoff ausente: {arquivo}", file=sys.stderr)
        return 1
    try:
        dados = json.loads(arquivo.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"[aidd-forge] handoff invalido: {exc}", file=sys.stderr)
        return 1
    if not isinstance(dados, dict) or not isinstance(dados.get("componentes"), list):
        print("[aidd-forge] handoff sem campo 'componentes' valido.", file=sys.stderr)
        return 1
    registrados = {c.get("caminho"): c.get("sha256") for c in dados["componentes"] if isinstance(c, dict)}
    for relativo in componentes:
        caminho = raiz / relativo
        if not caminho.is_file():
            print(f"[aidd-forge] componente inexistente: {relativo}", file=sys.stderr)
            return 1
        atual = hashlib.sha256(caminho.read_bytes()).hexdigest()
        if registrados.get(relativo) != atual:
            print(f"[aidd-forge] hash divergente no handoff: {relativo}", file=sys.stderr)
            return 1
    return 0


def executar_handoff(argumentos: List[str]) -> int:
    parser = argparse.ArgumentParser(prog="forge handoff", description="Handoff estruturado ao aidd-planner")
    parser.add_argument("modo", choices=["emit", "verify"], help="emit gera o JSON; verify valida integridade")
    parser.add_argument("--path", default=".", help="Diretorio raiz do handoff (padrao: .)")
    parser.add_argument(
        "--componente",
        action="append",
        default=None,
        help="Componente relativo ao raiz (repetivel; padrao: componentes do forge)",
    )
    try:
        ns = parser.parse_args(argumentos)
    except SystemExit:
        return 1
    raiz = Path(ns.path).resolve()
    componentes = ns.componente if ns.componente else list(COMPONENTES_PADRAO)
    try:
        if ns.modo == "emit":
            destino = emitir_handoff(raiz, componentes)
            print(f"[aidd-forge] handoff emitido: {destino}")
            return 0
        return verificar_handoff(raiz, componentes)
    except Exception as exc:
        print(f"[aidd-forge] falha no handoff: {exc}", file=sys.stderr)
        return 1


def _montar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python ecossistema.py forge",
        description="CLI deterministica do aidd-forge (governanca agentica)",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    parser_init = subparsers.add_parser("init", help="Injeta a infraestrutura AIDD no projeto alvo")
    parser_init.add_argument("path", nargs="?", default=".", help="Diretorio alvo (padrao: .)")
    parser_init.add_argument("--force", action="store_true", help="Sobrescreve arquivos existentes")

    parser_inject = subparsers.add_parser("inject", help="Injeta um componente no projeto alvo")
    parser_inject.add_argument("tipo", help="Tipo do componente (skill, mcp, rule, spec, roteiro)")
    parser_inject.add_argument("nome", help="Nome do componente")
    parser_inject.add_argument("--descricao", required=True, help="Descricao curta do componente")
    parser_inject.add_argument("--conteudo", default=None, help="Conteudo do arquivo a materializar")
    parser_inject.add_argument("--conteudo-file", default=None, help="Arquivo com o conteudo")
    parser_inject.add_argument("--path", default=".", help="Caminho do projeto alvo")
    parser_inject.add_argument("--force", action="store_true", help="Sobrescreve o destino")

    parser_audit = subparsers.add_parser("audit", help="Audita a conformidade de governanca")
    parser_audit.add_argument("path", nargs="?", default=".", help="Diretorio alvo (padrao: .)")
    parser_audit.add_argument("--format", dest="fmt", default="md", choices=["json", "md", "html"],
                              help="Formato do relatorio")
    parser_audit.add_argument("--output", default=None, help="Arquivo de saida (padrao: stdout)")

    parser_conform = subparsers.add_parser("conform", help="Aplica correcoes de conformidade")
    parser_conform.add_argument("path", nargs="?", default=".", help="Diretorio alvo (padrao: .)")
    parser_conform.add_argument("--dry-run", action="store_true", help="Apenas mostra o que seria feito")
    parser_conform.add_argument("--item", action="append", default=[], type=int,
                                help="Corrige apenas o item especifico (repetivel)")

    parser_handoff = subparsers.add_parser("handoff", help="Handoff estruturado com SHA-256 ao aidd-planner")
    parser_handoff.add_argument("modo", choices=["emit", "verify"])
    parser_handoff.add_argument("--path", default=".")
    parser_handoff.add_argument("--componente", action="append", default=None)

    parser_fornecer = subparsers.add_parser("fornecer", help="Entrega uma peca do almoxarifado no projeto alvo")
    parser_fornecer.add_argument("piece", help="Nome da peca no almoxarifado")
    parser_fornecer.add_argument("--destino", required=True, help="Diretorio ou caminho de destino no projeto")

    parser_mobbin = subparsers.add_parser("mobbin", help="Consulta deterministica de telas e fluxos de UI do Mobbin")
    parser_mobbin.add_argument("query", help="Termo de busca em linguagem natural")
    parser_mobbin.add_argument("--plataforma", choices=["web", "ios"], default="web", help="Plataforma alvo")
    parser_mobbin.add_argument("--modo", choices=["fast", "standard", "deep"], default="standard", help="Modo de busca")
    parser_mobbin.add_argument("--limite", type=int, default=10, help="Quantidade maxima de telas")
    parser_mobbin.add_argument("--json", action="store_true", help="Saida em JSON puro")

    return parser


def main(args: Optional[List[str]] = None) -> int:
    """Entrypoint principal. exit 1 em parametros faltantes ou entrada tratada."""
    argv = list(sys.argv[1:] if args is None else args)
    if argv and argv[0] == "handoff":
        return executar_handoff(argv[1:])
    parser = _montar_parser()

    try:
        parser.parse_args(argv)
    except SystemExit as exc:  # --help -> 0; erro de validacao -> 1
        return 0 if exc.code in (0, None) else 1

    try:
        return executar_script_local(argv)
    except Exception as exc:
        print(f"[aidd-forge] falha na delegacao ao script local: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
