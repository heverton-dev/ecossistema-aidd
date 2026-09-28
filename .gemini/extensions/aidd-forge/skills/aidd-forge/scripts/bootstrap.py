# -*- coding: utf-8 -*-
"""
Bootstrap deterministico de aidd-forge (D8 / DoD 3).

Valida o payload de bootstrap com schema estrito (sem inferencia de LLM),
renderiza templates de forma deterministica e confina a injecao do manifesto
ao diretorio alvo atraves do guard de isolamento (D3).
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Union

SCRIPTS_DIR = Path(__file__).resolve().parent

_RE_TOOL = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_RE_CICLO = re.compile(r"^ciclo-\d+$")
_RE_KIT = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
_RE_PLACEHOLDER = re.compile(r"\{\{\s*([a-z0-9_]+)\s*\}\}")

_CAMPOS_OBRIGATORIOS = ("tool", "ciclo", "alvo", "kits")
_CAMPOS_OPCIONAIS = ("force",)
_TODOS_CAMPOS = set(_CAMPOS_OBRIGATORIOS) | set(_CAMPOS_OPCIONAIS)


class PayloadValidationError(ValueError):
    """Payload de bootstrap invalido, nao estruturado ou fora do schema estrito."""


def _carregar_isolamento():
    """Carrega o modulo irmao isolamento.py (guard de escrita D3)."""
    nome = "aidd_forge_isolamento_bootstrap"
    if nome in sys.modules:
        return sys.modules[nome]
    spec = importlib.util.spec_from_file_location(nome, str(SCRIPTS_DIR / "isolamento.py"))
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nome] = modulo
    spec.loader.exec_module(modulo)
    return modulo


def validar_payload(dados: Any) -> Dict[str, Any]:
    """Valida o payload contra o schema estrito; normaliza e retorna o dicionario."""
    if not isinstance(dados, Mapping):
        raise PayloadValidationError("payload deve ser um objeto JSON (mapping)")

    chaves = set(dados.keys())
    desconhecidas = chaves - _TODOS_CAMPOS
    if desconhecidas:
        raise PayloadValidationError(f"chaves desconhecidas: {sorted(desconhecidas)}")

    ausentes = [campo for campo in _CAMPOS_OBRIGATORIOS if campo not in dados]
    if ausentes:
        raise PayloadValidationError(f"campos obrigatorios ausentes: {ausentes}")

    tool = dados["tool"]
    if not isinstance(tool, str) or not _RE_TOOL.match(tool):
        raise PayloadValidationError("campo 'tool' deve ser string [a-z0-9-] nao vazia")

    ciclo = dados["ciclo"]
    if not isinstance(ciclo, str) or not _RE_CICLO.match(ciclo):
        raise PayloadValidationError("campo 'ciclo' deve ter formato 'ciclo-<numero>'")

    alvo = dados["alvo"]
    if not isinstance(alvo, str) or not alvo.strip():
        raise PayloadValidationError("campo 'alvo' deve ser string nao vazia")
    if any(parte == ".." for parte in Path(alvo).parts):
        raise PayloadValidationError("campo 'alvo' nao pode conter traversal '..'")

    kits = dados["kits"]
    if not isinstance(kits, list) or not kits:
        raise PayloadValidationError("campo 'kits' deve ser lista nao vazia")
    for kit in kits:
        if not isinstance(kit, str) or not _RE_KIT.match(kit):
            raise PayloadValidationError(f"kit invalido: {kit!r}")

    force = dados.get("force", False)
    if not isinstance(force, bool):
        raise PayloadValidationError("campo 'force' deve ser booleano")

    return {
        "tool": tool,
        "ciclo": ciclo,
        "alvo": alvo,
        "kits": list(kits),
        "force": force,
    }


def carregar_payload(texto: Union[str, bytes]) -> Dict[str, Any]:
    """Interpreta JSON estrito; texto livre ou payload incompleto -> PayloadValidationError."""
    try:
        dados = json.loads(texto)
    except (ValueError, TypeError, UnicodeDecodeError) as exc:
        raise PayloadValidationError(f"input nao estruturado (JSON invalido): {exc}") from exc
    return validar_payload(dados)


def renderizar_template(template: str, contexto: Mapping[str, Any]) -> str:
    """
    Substituicao deterministica de placeholders {{chave}}.
    Placeholder sem chave correspondente ou trecho malformado residual -> erro.
    """
    if not isinstance(template, str):
        raise PayloadValidationError("template deve ser string")

    def _substituir(match: re.Match) -> str:
        chave = match.group(1)
        if chave not in contexto:
            raise PayloadValidationError(f"placeholder sem valor: {{{{{chave}}}}}")
        return str(contexto[chave])

    saida = _RE_PLACEHOLDER.sub(_substituir, template)
    if "{{" in saida or "}}" in saida:
        raise PayloadValidationError("renderizacao deixou placeholder malformado residual")
    return saida


def executar_bootstrap(payload: Dict[str, Any]) -> Path:
    """
    Renderiza o manifesto de bootstrap de forma deterministica e o injeta no
    diretorio alvo, confinado pelo guard de isolamento (D3).
    """
    isolamento = _carregar_isolamento()

    destino = Path(payload["alvo"]).resolve()
    destino.mkdir(parents=True, exist_ok=True)

    contexto = {
        "tool": payload["tool"],
        "ciclo": payload["ciclo"],
        "kits": ",".join(payload["kits"]),
        "force": str(payload["force"]).lower(),
    }
    assinatura = renderizar_template("forge/{{tool}}/{{ciclo}}", contexto)

    manifesto = {
        "tool": payload["tool"],
        "ciclo": payload["ciclo"],
        "alvo": payload["alvo"],
        "kits": payload["kits"],
        "force": payload["force"],
        "assinatura": assinatura,
    }
    conteudo = json.dumps(manifesto, indent=2, sort_keys=True, ensure_ascii=False) + "\n"

    return isolamento.escrever_com_isolamento(
        repo_root=destino,
        alvo_relativo="FORGE-BOOTSTRAP.json",
        conteudo=conteudo,
        worktree_dir=None,
    )


def main(args: Optional[List[str]] = None) -> int:
    """Entrypoint CLI: <arquivo_payload.json>. exit 1 em qualquer invalidade."""
    argv = list(sys.argv[1:] if args is None else args)
    if len(argv) != 1:
        print("Uso: bootstrap.py <arquivo_payload.json>", file=sys.stderr)
        return 1

    try:
        texto = Path(argv[0]).read_text(encoding="utf-8")
        payload = carregar_payload(texto)
        manifesto = executar_bootstrap(payload)
    except PayloadValidationError as exc:
        print(f"[aidd-forge] payload invalido: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"[aidd-forge] falha de E/S no bootstrap: {exc}", file=sys.stderr)
        return 1

    print(f"[aidd-forge] bootstrap gravado: {manifesto}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
