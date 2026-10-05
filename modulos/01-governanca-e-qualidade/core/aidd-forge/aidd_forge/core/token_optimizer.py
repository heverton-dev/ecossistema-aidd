"""Gerador da regra obrigatoria de economia extrema de tokens (Triade Caveman Ultra).

Injeta em templates de governanca (`AGENTS.md` e afins) um bloco Markdown
delimitado por marcadores, descrevendo o protocolo triplice mandatorio:

1. Entrada em ingles (economia de 30%-50% de tokens de BPE).
2. Processamento (chain-of-thought) em English Caveman telegrafico, 3-5 linhas.
3. Saida estritamente em Portugues do Brasil (PT-BR) de alta precisao.

A injecao e puramente textual (zero LLM) e idempotente: reexecutar sobre um
arquivo que ja contem o marcador nao duplica o bloco.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

MARKER_BEGIN = "<!-- AIDD-FORGE:TOKEN-TRIAD:BEGIN -->"
MARKER_END = "<!-- AIDD-FORGE:TOKEN-TRIAD:END -->"

TRIAD_RULE_BODY = """## Protocolo de Tokens (Triade Caveman Ultra)

Regra obrigatoria de economia severa de tokens para todo agente que opera
neste repositorio:

1. **ENTRADA (Ingles):** system prompts e regras de governanca escritos em
   ingles — economia de 30% a 50% de tokens de BPE frente ao portugues.
2. **PROCESSAMENTO (English Caveman):** raciocinio interno (chain-of-thought)
   telegrafico, sem artigos, em no maximo 3-5 linhas. Ex.: "inspect files,
   verify gate, impl clean slice, test exit 0".
3. **SAIDA (PT-BR):** toda resposta, comunicacao e codigo entregues em
   Portugues do Brasil de alta precisao — sem stubs, sem placeholders.
"""

DEFAULT_TARGET_FILENAMES: tuple[str, ...] = ("AGENTS.md", "AGENTS-WORKFLOW.md")


@dataclass
class TokenOptimizerResult:
    """Resumo de uma execucao de injecao da triade, usado para relatar ao usuario."""

    injected: list[Path] = field(default_factory=list)
    already_present: list[Path] = field(default_factory=list)


def render_triad_block() -> str:
    """Renderiza o bloco Markdown completo (marcadores + regra)."""
    return f"{MARKER_BEGIN}\n{TRIAD_RULE_BODY}{MARKER_END}\n"


def has_triad_rule(content: str) -> bool:
    """Verifica se o conteudo ja contem o bloco injetado."""
    return MARKER_BEGIN in content


def inject_into_content(content: str) -> str:
    """Anexa o bloco da triade ao final do conteudo, se ainda nao presente."""
    if has_triad_rule(content):
        return content

    if not content:
        return render_triad_block()

    separator = "\n" if content.endswith("\n") else "\n\n"
    return f"{content}{separator}{render_triad_block()}"


def inject_into_file(path: Path) -> bool:
    """Injeta a regra no arquivo; retorna True se injetou, False se ja tinha."""
    content = path.read_text(encoding="utf-8") if path.exists() else ""
    if has_triad_rule(content):
        return False

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(inject_into_content(content), encoding="utf-8")
    return True


def inject_into_tree(
    root: Path, filenames: tuple[str, ...] = DEFAULT_TARGET_FILENAMES
) -> TokenOptimizerResult:
    """Percorre `root` injetando a regra em todo arquivo cujo nome esteja em `filenames`."""
    root = Path(root)
    result = TokenOptimizerResult()

    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name in filenames:
            if inject_into_file(path):
                result.injected.append(path)
            else:
                result.already_present.append(path)

    return result
