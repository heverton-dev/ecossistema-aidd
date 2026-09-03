"""Linter estatico de contexto: alerta quando arquivos de regras estouram o orcamento de tokens.

Reusa a mesma heuristica conservadora de ~4 chars por token (BPE) ja usada
pelo `subagent_purger` para o limite de prompt. E mecanica pura (zero LLM,
zero chamada de rede): apenas conta caracteres em arquivos de governanca e
reporta quais ultrapassam o limite de ~1500 tokens.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# ~4 chars por token (heuristica BPE conservadora), mesma usada em subagent_purger.
CHARS_PER_TOKEN = 4
MAX_CONTEXT_TOKENS = 1500

DEFAULT_TARGET_FILENAMES: tuple[str, ...] = ("AGENTS.md", "AGENTS-WORKFLOW.md")


@dataclass(frozen=True)
class ContextLintWarning:
    """Um arquivo de regras que ultrapassou o orcamento de tokens permitido."""

    path: Path
    estimated_tokens: int
    max_tokens: int


@dataclass
class ContextLintReport:
    """Resultado agregado de uma varredura de linting de contexto."""

    warnings: list[ContextLintWarning] = field(default_factory=list)

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


def estimate_tokens(text: str) -> int:
    """Estima tokens via heuristica conservadora de ~4 chars por token BPE."""
    return len(text) // CHARS_PER_TOKEN


def lint_file(path: Path, max_tokens: int = MAX_CONTEXT_TOKENS) -> ContextLintWarning | None:
    """Le `path` e retorna um warning se o arquivo ultrapassar `max_tokens`."""
    content = path.read_text(encoding="utf-8")
    tokens = estimate_tokens(content)
    if tokens > max_tokens:
        return ContextLintWarning(path=path, estimated_tokens=tokens, max_tokens=max_tokens)
    return None


def lint_tree(
    root: Path,
    filenames: tuple[str, ...] = DEFAULT_TARGET_FILENAMES,
    max_tokens: int = MAX_CONTEXT_TOKENS,
) -> ContextLintReport:
    """Percorre `root` e reporta todo arquivo de regras acima do orcamento de tokens."""
    root = Path(root)
    report = ContextLintReport()

    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name in filenames:
            warning = lint_file(path, max_tokens=max_tokens)
            if warning is not None:
                report.warnings.append(warning)

    return report
