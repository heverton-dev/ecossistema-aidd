#!/usr/bin/env python3
"""Quality Gate: valida integridade e compatibilidade de Schemas JSON Draft 2020-12.

Descobre todo `.json` do repositorio que se declara um schema (contem a
chave `$schema`), confirma que aponta para o dialeto Draft 2020-12, e
valida sua integridade estrutural. Se o pacote opcional `jsonschema`
estiver instalado no projeto alvo, usa `Draft202012Validator.check_schema`
para validacao profunda do meta-schema; caso contrario cai para uma
checagem estrutural leve (stdlib apenas), sem nunca falhar por causa de
uma dependencia ausente. Tambem detecta `$id` duplicado entre schemas
(conflito de compatibilidade dentro do repositorio).

Uso: `python gates/G_CONTRACTS.py [repo_root]`
Saida: exit 0 (todos os schemas validos e sem conflito) ou exit 1.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

EXCLUDED_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    "dist", "build", ".mypy_cache", ".pytest_cache",
}

DRAFT_2020_12_URI = "https://json-schema.org/draft/2020-12/schema"

VALID_JSON_TYPES = {"null", "boolean", "object", "array", "number", "string", "integer"}


@dataclass
class GateResult:
    passed: bool
    messages: list[str] = field(default_factory=list)


def _iter_json_files(repo_root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(repo_root.rglob("*.json")):
        if any(part in EXCLUDED_DIRS for part in path.relative_to(repo_root).parts):
            continue
        files.append(path)
    return files


def _is_schema(payload: object) -> bool:
    return isinstance(payload, dict) and "$schema" in payload


def _basic_structural_check(payload: dict, rel: Path) -> list[str]:
    """Checagem estrutural leve, usada quando `jsonschema` nao esta instalado."""
    errors: list[str] = []

    schema_type = payload.get("type")
    if schema_type is not None:
        types = schema_type if isinstance(schema_type, list) else [schema_type]
        for t in types:
            if t not in VALID_JSON_TYPES:
                errors.append(f"{rel}: 'type' invalido: {t!r}")

    required = payload.get("required")
    if required is not None and not (
        isinstance(required, list) and all(isinstance(r, str) for r in required)
    ):
        errors.append(f"{rel}: 'required' deve ser uma lista de strings")

    properties = payload.get("properties")
    if properties is not None and not isinstance(properties, dict):
        errors.append(f"{rel}: 'properties' deve ser um objeto")

    return errors


def _deep_validate(payload: dict, rel: Path) -> list[str]:
    """Validacao profunda via `jsonschema`, se disponivel no ambiente alvo."""
    try:
        from jsonschema import Draft202012Validator
        from jsonschema.exceptions import SchemaError
    except ImportError:
        return _basic_structural_check(payload, rel)

    try:
        Draft202012Validator.check_schema(payload)
    except SchemaError as exc:
        return [f"{rel}: meta-schema invalido: {exc.message}"]
    return []


def scan(repo_root: Path) -> GateResult:
    repo_root = Path(repo_root)
    errors: list[str] = []
    seen_ids: dict[str, Path] = {}
    schema_count = 0

    for path in _iter_json_files(repo_root):
        rel = path.relative_to(repo_root)
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"{rel}: nao foi possivel ler o arquivo ({exc})")
            continue

        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            errors.append(f"{rel}:{exc.lineno}: JSON invalido ({exc.msg})")
            continue

        if not _is_schema(payload):
            continue

        schema_count += 1
        schema_uri = payload.get("$schema", "")
        if not schema_uri.startswith(DRAFT_2020_12_URI.rsplit("/schema", 1)[0]):
            errors.append(
                f"{rel}: '$schema' nao aponta para Draft 2020-12 (encontrado: {schema_uri!r})"
            )

        errors.extend(_deep_validate(payload, rel))

        schema_id = payload.get("$id")
        if schema_id:
            if schema_id in seen_ids:
                errors.append(
                    f"{rel}: '$id' duplicado {schema_id!r} (ja usado em {seen_ids[schema_id]})"
                )
            else:
                seen_ids[schema_id] = rel

    if errors:
        return GateResult(passed=False, messages=errors)
    return GateResult(passed=True, messages=[f"{schema_count} schema(s) validado(s), sem conflitos"])


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    repo_root = Path(argv[0]) if argv else Path.cwd()

    result = scan(repo_root)
    for message in result.messages:
        print(f"[G_CONTRACTS] {message}")

    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
