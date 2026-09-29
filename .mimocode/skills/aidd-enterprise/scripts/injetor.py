# -*- coding: utf-8 -*-
"""
Injetor deterministico de componentes para aidd-enterprise (D8).

- Validacao estrita do payload contra
  tools/aidd-enterprise/scripts/injector/schema/component_manifest.schema.json.
- Calculo e verificacao de SHA-256 antes de copiar qualquer componente
  (zero-trust: hash divergente ou ausente bloqueia a copia).
- Copia confinada ao repo_root; exit 1 em qualquer violacao.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from jsonschema import Draft202012Validator
    from jsonschema.exceptions import SchemaError, ValidationError
except ImportError:  # pragma: no cover - dependencia declarada em requirements.txt
    Draft202012Validator = None  # type: ignore[assignment]

    class SchemaError(Exception):  # type: ignore[no-redef]
        pass

    class ValidationError(Exception):  # type: ignore[no-redef]
        pass


class ManifestValidationError(ValueError):
    """Payload fora do contrato do component_manifest.schema.json."""


class IntegrityError(ValueError):
    """SHA-256 ausente ou divergente: integridade do componente nao comprovada."""


def encontrar_raiz_repositorio() -> Optional[Path]:
    """Localiza a raiz do repositorio procurando por ecossistema.py."""
    atual = Path(__file__).resolve()
    for candidato in [atual, *atual.parents]:
        if (candidato / "ecossistema.py").is_file():
            return candidato
    return None


def caminho_schema() -> Path:
    raiz = encontrar_raiz_repositorio()
    if raiz is None:
        raise FileNotFoundError("raiz do repositorio nao encontrada (ecossistema.py ausente)")
    return raiz / "tools" / "aidd-enterprise" / "scripts" / "injector" / "schema" / "component_manifest.schema.json"


def carregar_schema() -> Dict[str, Any]:
    arquivo = caminho_schema()
    if not arquivo.is_file():
        raise FileNotFoundError(f"schema canonico ausente: {arquivo}")
    return json.loads(arquivo.read_text(encoding="utf-8"))


def validar_manifest(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Validacao estrita (JSON Schema 2020-12) contra component_manifest.schema.json."""
    if not isinstance(payload, dict):
        raise ManifestValidationError("manifest deve ser um objeto JSON")
    schema = carregar_schema()
    if Draft202012Validator is None:
        raise ManifestValidationError("biblioteca jsonschema indisponivel: validacao estrita impossivel")
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise ManifestValidationError(f"schema canonico invalido: {exc.message}") from exc
    erros = sorted(Draft202012Validator(schema).iter_errors(payload), key=lambda e: list(e.absolute_path))
    if erros:
        detalhes = "; ".join(
            f"{'/'.join(str(p) for p in e.absolute_path) or '<raiz>'}: {e.message}" for e in erros[:5]
        )
        raise ManifestValidationError(f"payload fora do schema: {detalhes}")
    return payload


def calcular_sha256(dados: Any) -> str:
    """SHA-256 deterministico de texto, bytes ou objeto JSON canonico."""
    if isinstance(dados, bytes):
        bruto = dados
    elif isinstance(dados, str):
        bruto = dados.encode("utf-8")
    else:
        bruto = json.dumps(dados, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(bruto).hexdigest()


def _carga_integridade(payload: Dict[str, Any]) -> Any:
    """Carga canonica coberta pelo hash: content, files (config) ou bloco mcp."""
    if isinstance(payload.get("content"), str):
        return payload["content"]
    if isinstance(payload.get("files"), dict):
        return payload["files"]
    if isinstance(payload.get("mcp"), dict):
        return payload["mcp"]
    raise IntegrityError("manifest sem carga util (content, files ou mcp) para verificacao de integridade")


def verificar_sha256(payload: Dict[str, Any]) -> str:
    """Confere o campo sha256 do manifest contra o hash calculado da carga util."""
    hash_declarado = payload.get("sha256")
    if not isinstance(hash_declarado, str) or not hash_declarado:
        raise IntegrityError("manifest sem campo 'sha256': integridade nao comprovada")
    calculado = calcular_sha256(_carga_integridade(payload))
    if calculado.lower() != hash_declarado.lower():
        raise IntegrityError(
            f"SHA-256 divergente: declarado {hash_declarado}, calculado {calculado}"
        )
    return calculado


def _destino_confinado(destino: Path, repo_root: Path) -> Path:
    destino_abs = destino.resolve()
    raiz_abs = repo_root.resolve()
    try:
        destino_abs.relative_to(raiz_abs)
    except ValueError:
        raise ManifestValidationError(
            f"destino '{destino_abs}' fora do repo_root '{raiz_abs}'"
        )
    if destino_abs == raiz_abs:
        raise ManifestValidationError("destino nao pode ser a propria raiz do repositorio")
    return destino_abs


def injetar_componente(
    payload: Dict[str, Any],
    destino: Path,
    repo_root: Optional[Path] = None,
) -> List[Path]:
    """
    Pipeline deterministico: valida schema -> confere SHA-256 -> copia componentes.
    Nenhum byte e copiado antes da integridade confirmada.
    """
    raiz = (repo_root or encontrar_raiz_repositorio() or Path.cwd()).resolve()
    validar_manifest(payload)
    verificar_sha256(payload)

    destino_abs = _destino_confinado(Path(destino), raiz)
    nome = payload["name"]
    raiz_componente = destino_abs / nome
    copiados: List[Path] = []

    if isinstance(payload.get("files"), dict):
        for relativo, conteudo in payload["files"].items():
            alvo = (raiz_componente / relativo).resolve()
            alvo.relative_to(raiz_componente.resolve())
            alvo.parent.mkdir(parents=True, exist_ok=True)
            alvo.write_text(conteudo, encoding="utf-8")
            copiados.append(alvo)
    elif isinstance(payload.get("mcp"), dict):
        raiz_componente.mkdir(parents=True, exist_ok=True)
        alvo = raiz_componente / "mcp.json"
        alvo.write_text(
            json.dumps(payload["mcp"], indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        copiados.append(alvo)
    else:
        raiz_componente.mkdir(parents=True, exist_ok=True)
        sufixo = "md" if payload["type"] in ("skill", "rule", "spec", "agent", "hook") else "txt"
        alvo = raiz_componente / f"{nome}.{sufixo}"
        alvo.write_text(payload["content"], encoding="utf-8")
        copiados.append(alvo)

    return copiados


def _montar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aidd-enterprise injetor",
        description="Injeta componentes com validacao estrita de schema e SHA-256",
    )
    parser.add_argument("--payload", required=True, help="Arquivo JSON do manifest do componente")
    parser.add_argument("--destino", required=True, help="Diretorio alvo da injecao")
    parser.add_argument("--repo-root", dest="repo_root", default=None, help="Raiz do repositorio (padrao: auto)")
    return parser


def main(args: Optional[List[str]] = None) -> int:
    """Entrypoint: exit 1 em payload corrompido, hash divergente ou falha de copia."""
    try:
        ns = _montar_parser().parse_args(args)
    except SystemExit as exc:
        return 0 if exc.code in (0, None) else 1

    try:
        payload = json.loads(Path(ns.payload).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"[aidd-enterprise][injetor] payload ilegivel: {exc}", file=sys.stderr)
        return 1

    raiz = Path(ns.repo_root).resolve() if ns.repo_root else None
    try:
        copiados = injetar_componente(payload, destino=Path(ns.destino), repo_root=raiz)
    except (ManifestValidationError, IntegrityError, ValidationError, OSError, ValueError) as exc:
        print(f"[aidd-enterprise][injetor] injecao bloqueada: {exc}", file=sys.stderr)
        return 1

    for caminho in copiados:
        print(f"[aidd-enterprise][injetor] copiado: {caminho}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
