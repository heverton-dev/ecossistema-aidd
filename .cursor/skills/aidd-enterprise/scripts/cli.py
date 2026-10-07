# -*- coding: utf-8 -*-
"""
AIDD-Enterprise CLI: entrada deterministica da skill aidd-enterprise (D4).

Ponto unico de entrada local de `python ecossistema.py enterprise <args>`:
- Subcomandos declarativos (inject, audit) validados por argparse.
- Tipos de componente: skill, rule, mcp, spec, config, hook, agent.
- exit 1 em parametros faltantes, entrada nao tratada ou fallback sem
  implementacao local (nunca exit 2, nunca sucesso silencioso).
- Roteamento direto para os modulos Python de modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise,
  sem nenhuma interpretacao por prompt de LLM.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

TIPOS_COMPONENTES = ("skill", "rule", "mcp", "spec", "config", "hook", "agent")

HANDOFF_ARQUIVO = "handoff-enterprise.json"
COMPONENTES_PADRAO = [
    ".agents/skills/aidd-enterprise/scripts/isolamento.py",
    ".agents/skills/aidd-enterprise/scripts/cli.py",
    ".agents/skills/aidd-enterprise/scripts/injetor.py",
    ".agents/skills/aidd-enterprise/scripts/orquestrador.py",
    ".agents/skills/aidd-enterprise/scripts/fallback.py",
    ".agents/skills/aidd-enterprise/scripts/observabilidade.py",
    ".agents/skills/aidd-enterprise/scripts/rollback.py",
    "modulos/03-plataforma-e-entrega/gates/G_aidd_enterprise.py",
]


def encontrar_raiz_repositorio() -> Optional[Path]:
    """Localiza a raiz do repositorio procurando por ecossistema.py."""
    atual = Path(__file__).resolve()
    for candidato in [atual, *atual.parents]:
        if (candidato / "ecossistema.py").is_file():
            return candidato
    return None


def raiz_pacote_local() -> Optional[Path]:
    """Raiz do pacote local modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise quando presente neste repositorio."""
    raiz = encontrar_raiz_repositorio()
    if raiz is None:
        return None
    pacote = raiz / "modulos" / "03-plataforma-e-entrega" / "blindagem-enterprise" / "aidd-enterprise"
    if (pacote / "scripts" / "aidd.py").is_file():
        return pacote
    return None


def executar_script_local(argumentos: List[str]) -> int:
    """
    Delega os argumentos ja validados ao pacote local modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise.
    Levanta RuntimeError quando o pacote local nao esta disponivel (fallback
    sem implementacao -> exit 1 no chamador).
    """
    pacote = raiz_pacote_local()
    if pacote is None:
        raise RuntimeError("pacote local modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise nao encontrado")

    script = pacote / "scripts" / "aidd.py"
    env = dict(os.environ)
    env["PYTHONPATH"] = str(pacote) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    res = subprocess.run(
        [sys.executable, str(script), *argumentos],
        cwd=str(pacote),
        env=env,
        capture_output=False,
    )
    return int(res.returncode)


def _montar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python ecossistema.py enterprise",
        description="CLI deterministica do aidd-enterprise (governanca de componentes criticos)",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    parser_inject = subparsers.add_parser("inject", help="Injeta um componente em todos os harnesses")
    parser_inject.add_argument("tipo", choices=TIPOS_COMPONENTES, help="Tipo do componente")
    parser_inject.add_argument("nome", help="Nome do componente")
    parser_inject.add_argument("--descricao", "-d", default="", help="Descricao curta do componente")
    parser_inject.add_argument("--content-file", default=None, help="Arquivo com o conteudo completo")
    parser_inject.add_argument("--dir", default=".", help="Diretorio do projeto alvo")
    parser_inject.add_argument("--dry-run", action="store_true", help="Simula sem escrever no filesystem")
    parser_inject.add_argument("--remover", action="store_true", help="Remove componente injetado")

    parser_audit = subparsers.add_parser("audit", help="Executa a bateria de gates deterministicos")
    parser_audit.add_argument("path", nargs="?", default=".", help="Diretorio alvo (padrao: .)")
    parser_audit.add_argument("--report", action="store_true", help="Gera relatorio factual")
    parser_audit.add_argument("--json", dest="json_", action="store_true", help="Saida em JSON")

    return parser


def montar_argv_delegacao(ns: argparse.Namespace, argv: List[str]) -> List[str]:
    """Converte o namespace validado no argv esperado pelo pacote local."""
    if ns.subcommand == "audit":
        delegado = ["audit", "--dir", ns.path]
        if ns.report:
            delegado.append("--report")
        if ns.json_:
            delegado.append("--json")
        return delegado
    return list(argv)


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
        "ferramenta": "aidd-enterprise",
        "consumidor": "aidd-ops",
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
        print(f"[aidd-enterprise] handoff ausente: {arquivo}", file=sys.stderr)
        return 1
    try:
        dados = json.loads(arquivo.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"[aidd-enterprise] handoff invalido: {exc}", file=sys.stderr)
        return 1
    if not isinstance(dados, dict) or not isinstance(dados.get("componentes"), list):
        print("[aidd-enterprise] handoff sem campo 'componentes' valido.", file=sys.stderr)
        return 1
    registrados = {c.get("caminho"): c.get("sha256") for c in dados["componentes"] if isinstance(c, dict)}
    for relativo in componentes:
        caminho = raiz / relativo
        if not caminho.is_file():
            print(f"[aidd-enterprise] componente inexistente: {relativo}", file=sys.stderr)
            return 1
        atual = hashlib.sha256(caminho.read_bytes()).hexdigest()
        if registrados.get(relativo) != atual:
            print(f"[aidd-enterprise] hash divergente no handoff: {relativo}", file=sys.stderr)
            return 1
    return 0


def executar_handoff(argumentos: List[str]) -> int:
    parser = argparse.ArgumentParser(prog="enterprise handoff", description="Handoff estruturado ao aidd-ops")
    parser.add_argument("modo", choices=["emit", "verify"], help="emit gera o JSON; verify valida integridade")
    parser.add_argument("--path", default=".", help="Diretorio raiz do handoff (padrao: .)")
    parser.add_argument(
        "--componente",
        action="append",
        default=None,
        help="Componente relativo ao raiz (repetivel; padrao: componentes do aidd-enterprise)",
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
            print(f"[aidd-enterprise] handoff emitido: {destino}")
            return 0
        return verificar_handoff(raiz, componentes)
    except Exception as exc:
        print(f"[aidd-enterprise] falha no handoff: {exc}", file=sys.stderr)
        return 1


def main(args: Optional[List[str]] = None) -> int:
    """Entrypoint principal. exit 1 em parametros faltantes ou entrada nao tratada."""
    argv = list(sys.argv[1:] if args is None else args)
    if argv and argv[0] == "handoff":
        return executar_handoff(argv[1:])
    parser = _montar_parser()

    try:
        ns = parser.parse_args(argv)
    except SystemExit as exc:  # --help -> 0; erro de validacao -> 1
        return 0 if exc.code in (0, None) else 1

    try:
        return int(executar_script_local(montar_argv_delegacao(ns, argv)))
    except Exception as exc:
        print(f"[aidd-enterprise] falha na delegacao ao script local: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
