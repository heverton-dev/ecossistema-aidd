#!/usr/bin/env python3
"""Quality Gate: checa latencia de execucao dos endpoints/comandos do projeto.

Le um orcamento de performance opcional em `.aidd/gates/performance_budget.json`
(formato abaixo), executa cada comando declarado e compara o tempo de
parede medido contra o limite `max_ms`. Se o arquivo de orcamento nao
existir, o gate passa silenciosamente (nao ha o que medir ainda — nao
bloqueia projetos recem-inicializados). Script autonomo (apenas stdlib)
para poder ser copiado para qualquer projeto alvo.

Formato de `.aidd/gates/performance_budget.json`:
    {
      "budgets": [
        {"name": "healthcheck", "command": ["python", "scripts/healthcheck.py"], "max_ms": 500}
      ]
    }

Uso: `python gates/G_PERFORMANCE.py [repo_root]`
Saida: exit 0 (sem orcamento, ou todos dentro do limite) ou exit 1 (estouro/erro).
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

BUDGET_RELATIVE_PATH = Path(".aidd") / "gates" / "performance_budget.json"


@dataclass
class GateResult:
    passed: bool
    messages: list[str] = field(default_factory=list)


def _load_budgets(budget_path: Path) -> list[dict]:
    payload = json.loads(budget_path.read_text(encoding="utf-8"))
    return payload.get("budgets", [])


def _measure_ms(command: list[str], repo_root: Path) -> tuple[int, float]:
    start = time.perf_counter()
    proc = subprocess.run(
        command, cwd=repo_root, capture_output=True, text=True, timeout=60, check=False,
    )
    elapsed_ms = (time.perf_counter() - start) * 1000
    return proc.returncode, elapsed_ms


def scan(repo_root: Path) -> GateResult:
    repo_root = Path(repo_root)
    budget_path = repo_root / BUDGET_RELATIVE_PATH

    if not budget_path.exists():
        return GateResult(
            passed=True,
            messages=[f"nenhum orcamento em {BUDGET_RELATIVE_PATH} — gate passa (nada a medir)"],
        )

    try:
        budgets = _load_budgets(budget_path)
    except (OSError, json.JSONDecodeError) as exc:
        return GateResult(passed=False, messages=[f"orcamento invalido em {budget_path}: {exc}"])

    failures: list[str] = []
    messages: list[str] = []

    for budget in budgets:
        name = budget.get("name", "?")
        command = budget.get("command")
        max_ms = budget.get("max_ms")

        if not command or max_ms is None:
            failures.append(f"{name}: orcamento incompleto (precisa de 'command' e 'max_ms')")
            continue

        try:
            returncode, elapsed_ms = _measure_ms(command, repo_root)
        except (OSError, subprocess.TimeoutExpired) as exc:
            failures.append(f"{name}: falha ao executar comando ({exc})")
            continue

        if returncode != 0:
            failures.append(f"{name}: comando retornou codigo de erro {returncode}")
            continue

        if elapsed_ms > max_ms:
            failures.append(f"{name}: {elapsed_ms:.1f}ms excedeu o orcamento de {max_ms}ms")
        else:
            messages.append(f"{name}: {elapsed_ms:.1f}ms dentro do orcamento de {max_ms}ms")

    if failures:
        return GateResult(passed=False, messages=[*messages, *failures])
    return GateResult(passed=True, messages=messages or ["nenhum orcamento configurado"])


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    repo_root = Path(argv[0]) if argv else Path.cwd()

    result = scan(repo_root)
    for message in result.messages:
        print(f"[G_PERFORMANCE] {message}")

    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
