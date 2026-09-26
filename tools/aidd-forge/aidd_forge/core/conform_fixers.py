"""Fixers de conformidade: correcoes cirurgicas e idempotentes para gaps detectados.

Cada funcao recebe `project_path` e retorna um `ConformFix` descrevendo
o que foi feito. Todas sao idempotentes: reexecutar produce o mesmo resultado.
Padrao de backup: le conteudo original antes de escrever, restaura em falha.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Diretrizes padrao que serao injetadas no AGENTS.md (em Ingles conciso)
# ---------------------------------------------------------------------------

DIRECTIVES: dict[str, str] = {
    "G05": (
        "- **Thinking constraint:** Think strictly in compact English. "
        "No meta-deliberation. Focus only on architectural invariants and edge cases. "
        "Under 150 words of reasoning."
    ),
    "G06": (
        "- **Execution limit:** Resolve tasks in 3 to 5 discrete steps. "
        "Stop and request confirmation if more steps are required."
    ),
    "G07": (
        "- **Output format:** Silent executor. Return code edits and 1-line "
        "execution status only. Do not explain what was changed unless explicitly "
        "asked. Do not repeat code in conversational reply."
    ),
    "G08": (
        "- **Bash rule:** Always pipe verbose commands to tail/grep. "
        "E.g., `pytest 2>&1 | tail -n 25`. Never dump raw bundle outputs, "
        "logs, or lockfiles into context."
    ),
    "G09": (
        "- **Graph-first:** Always query knowledge graph (code-review-graph MCP) "
        "before Grep, Glob, or full file reads."
    ),
}

DIRECTIVE_MARKER = "<!-- AIDD-FORGE:EXEC-DIRECTIVES:BEGIN -->"
DIRECTIVE_MARKER_END = "<!-- AIDD-FORGE:EXEC-DIRECTIVES:END -->"

AGENTS_MD_TEMPLATE = (
    "# AGENTS.md — Source of Truth\n\n"
    "This file governs how AI agents operate in this repository.\n\n"
    "{directives}\n"
)

GITIGNORE_ADDITIONS = (
    "\n# AIDD Forge: dependencies (lockfiles stay versioned for reproducible installs)\n"
    "node_modules/\n"
)

GITATTRIBUTES_CONTENT = "* text=auto eol=lf\n"

IDE_POINTER_CONTENT = (
    "# CLAUDE.md — IDE Rule Pointer\n\n"
    "This file points to the canonical governance source.\n"
    "All rules and directives are defined in `AGENTS.md`.\n\n"
    "@AGENTS.md\n"
)


@dataclass(frozen=True)
class ConformFix:
    """Resultado de uma correcao de conformidade."""

    audit_item_id: str
    description: str
    files_touched: list[str]
    success: bool
    error: str | None = None


@dataclass
class _Backup:
    path: Path
    original_content: bytes | None


# ---------------------------------------------------------------------------
# Fixers individuais
# ---------------------------------------------------------------------------


def fix_g01_agents_md_missing(project_path: Path) -> ConformFix:
    """G01: Cria AGENTS.md minimo se ausente."""
    candidates = [project_path / "AGENTS.md", project_path / "governance" / "AGENTS.md"]
    for path in candidates:
        if path.exists():
            return ConformFix(
                audit_item_id="G01",
                description="AGENTS.md already exists",
                files_touched=[],
                success=True,
            )

    target = project_path / "AGENTS.md"
    directives_block = _build_directives_block()
    content = AGENTS_MD_TEMPLATE.format(directives=directives_block)

    try:
        _safe_write(target, content)
        return ConformFix(
            audit_item_id="G01",
            description="Created minimal AGENTS.md with execution directives",
            files_touched=[str(target.relative_to(project_path))],
            success=True,
        )
    except OSError as exc:
        return ConformFix(
            audit_item_id="G01",
            description="Failed to create AGENTS.md",
            files_touched=[],
            success=False,
            error=str(exc),
        )


def fix_g03_ide_pointers(project_path: Path) -> ConformFix:
    """G03: Cria CLAUDE.md com ponteiro se ausente."""
    claude_path = project_path / "CLAUDE.md"
    touched: list[str] = []

    if not claude_path.exists():
        try:
            _safe_write(claude_path, IDE_POINTER_CONTENT)
            touched.append("CLAUDE.md")
        except OSError as exc:
            return ConformFix(
                audit_item_id="G03",
                description="Failed to create CLAUDE.md",
                files_touched=[], success=False, error=str(exc),
            )

    # Remove CLAUDE.md do .gitignore se la estiver ignorado.
    gitignore = project_path / ".gitignore"
    if gitignore.exists():
        content = gitignore.read_text(encoding="utf-8")
        new_lines = [
            line for line in content.splitlines()
            if line.strip() not in ("CLAUDE.md", "GEMINI.md")
        ]
        if len(new_lines) != len(content.splitlines()):
            _safe_write(gitignore, "\n".join(new_lines) + "\n")
            touched.append(".gitignore (removed CLAUDE.md/GEMINI.md from ignore)")

    return ConformFix(
        audit_item_id="G03",
        description="Created CLAUDE.md pointer and cleaned .gitignore" if touched else "IDE pointers already present",
        files_touched=touched,
        success=True,
    )


def fix_directive(project_path: Path, directive_id: str) -> ConformFix:
    """Injeta uma diretriz de execucao no AGENTS.md (padrao marcador idempotente)."""
    if directive_id not in DIRECTIVES:
        return ConformFix(
            audit_item_id=directive_id,
            description=f"Unknown directive: {directive_id}",
            files_touched=[], success=False,
            error=f"directive_id '{directive_id}' not in DIRECTIVES map",
        )

    from aidd_forge.core.audit_checks import _find_agents_md

    agents_md = _find_agents_md(project_path)
    if agents_md is None:
        return ConformFix(
            audit_item_id=directive_id,
            description="AGENTS.md not found, cannot inject directive",
            files_touched=[], success=False,
            error="AGENTS.md not found",
        )

    content = agents_md.read_text(encoding="utf-8")

    # Ja injetado? (checa se o bloco de diretrizes ja existe e contem esta diretriz)
    if DIRECTIVE_MARKER in content:
        block_start = content.index(DIRECTIVE_MARKER)
        block_end = content.index(DIRECTIVE_MARKER_END) if DIRECTIVE_MARKER_END in content else len(content)
        block_content = content[block_start:block_end]
        directive_key = DIRECTIVES[directive_id].split(":")[0].strip("- *")
        if directive_key in block_content:
            return ConformFix(
                audit_item_id=directive_id,
                description=f"Directive {directive_id} already present",
                files_touched=[], success=True,
            )
    elif directive_marker_open(directive_id) in content:
        return ConformFix(
            audit_item_id=directive_id,
            description=f"Directive {directive_id} already present",
            files_touched=[], success=True,
        )

    # Injeta via marcador.
    directive_line = DIRECTIVES[directive_id]
    block = f"{directive_marker_open(directive_id)}\n{directive_line}\n{directive_marker_close(directive_id)}"

    if DIRECTIVE_MARKER in content:
        # Ja existe um bloco de diretrizes — injeta dentro dele.
        content = content.replace(
            DIRECTIVE_MARKER_END,
            f"{directive_line}\n{DIRECTIVE_MARKER_END}",
        )
    else:
        # Cria novo bloco de diretrizes.
        separator = "\n" if content.endswith("\n") else "\n\n"
        content = (
            f"{content}{separator}\n"
            f"{DIRECTIVE_MARKER}\n"
            f"{directive_line}\n"
            f"{DIRECTIVE_MARKER_END}\n"
        )

    try:
        _safe_write(agents_md, content)
        return ConformFix(
            audit_item_id=directive_id,
            description=f"Injected {directive_id} directive into AGENTS.md",
            files_touched=[str(agents_md.relative_to(project_path))],
            success=True,
        )
    except OSError as exc:
        return ConformFix(
            audit_item_id=directive_id,
            description=f"Failed to inject {directive_id}",
            files_touched=[], success=False, error=str(exc),
        )


def fix_g12_gitignore(project_path: Path) -> ConformFix:
    """G12: Adiciona padroes faltantes ao .gitignore."""
    gitignore_path = project_path / ".gitignore"

    if not gitignore_path.exists():
        try:
            _safe_write(gitignore_path, GITIGNORE_ADDITIONS.strip() + "\n")
            return ConformFix(
                audit_item_id="G12",
                description="Created .gitignore with required patterns",
                files_touched=[".gitignore"],
                success=True,
            )
        except OSError as exc:
            return ConformFix(
                audit_item_id="G12",
                description="Failed to create .gitignore",
                files_touched=[], success=False, error=str(exc),
            )

    backup = _backup_file(gitignore_path)
    content = gitignore_path.read_text(encoding="utf-8")
    missing = [] if "node_modules" in content else ["node_modules/"]

    if not missing:
        return ConformFix(
            audit_item_id="G12",
            description="All required patterns already in .gitignore",
            files_touched=[], success=True,
        )

    append = "\n# AIDD Forge: dependencies (lockfiles stay versioned for reproducible installs)\n" + "\n".join(missing) + "\n"
    try:
        _safe_write(gitignore_path, content + append)
        return ConformFix(
            audit_item_id="G12",
            description=f"Added {len(missing)} missing pattern(s) to .gitignore",
            files_touched=[".gitignore"],
            success=True,
        )
    except OSError as exc:
        _restore_backup(backup)
        return ConformFix(
            audit_item_id="G12",
            description="Failed to update .gitignore (restored backup)",
            files_touched=[], success=False, error=str(exc),
        )


def fix_g13_gitattributes(project_path: Path) -> ConformFix:
    """G13: Cria .gitattributes com forca LF."""
    path = project_path / ".gitattributes"
    if path.exists():
        content = path.read_text(encoding="utf-8")
        if "text=auto" in content and "eol=lf" in content:
            return ConformFix(
                audit_item_id="G13",
                description=".gitattributes already has LF enforcement",
                files_touched=[], success=True,
            )
        # Adiciona a regra se ausente.
        backup = _backup_file(path)
        new_content = content.rstrip("\n") + "\n" + GITATTRIBUTES_CONTENT
        try:
            _safe_write(path, new_content)
            return ConformFix(
                audit_item_id="G13",
                description="Added LF enforcement to existing .gitattributes",
                files_touched=[".gitattributes"],
                success=True,
            )
        except OSError as exc:
            _restore_backup(backup)
            return ConformFix(
                audit_item_id="G13",
                description="Failed to update .gitattributes (restored backup)",
                files_touched=[], success=False, error=str(exc),
            )

    try:
        _safe_write(path, GITATTRIBUTES_CONTENT)
        return ConformFix(
            audit_item_id="G13",
            description="Created .gitattributes with LF enforcement",
            files_touched=[".gitattributes"],
            success=True,
        )
    except OSError as exc:
        return ConformFix(
            audit_item_id="G13",
            description="Failed to create .gitattributes",
            files_touched=[], success=False, error=str(exc),
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_write(path: Path, content: str) -> None:
    """Escreve arquivo com criacao de diretorio pai, sempre em LF (no Windows write_text gravaria CRLF)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def _backup_file(path: Path) -> _Backup:
    """Cria backup byte a byte do arquivo original (preserva o fim de linha)."""
    if path.exists():
        return _Backup(path=path, original_content=path.read_bytes())
    return _Backup(path=path, original_content=None)


def _restore_backup(backup: _Backup) -> None:
    """Restaura um arquivo a partir do backup."""
    if backup.original_content is not None:
        backup.path.write_bytes(backup.original_content)
    elif backup.path.exists():
        backup.path.unlink()


def _build_directives_block() -> str:
    """Constroi o bloco de diretrizes para injecao no AGENTS.md."""
    lines = [
        "## Core Execution Constraints\n",
        DIRECTIVE_MARKER,
    ]
    for key in ("G05", "G06", "G07", "G08", "G09"):
        lines.append(DIRECTIVES[key])
    lines.append(DIRECTIVE_MARKER_END)
    return "\n".join(lines)


def directive_marker_open(directive_id: str) -> str:
    return f"<!-- AIDD-FORGE:DIRECTIVE-{directive_id}:BEGIN -->"


def directive_marker_close(directive_id: str) -> str:
    return f"<!-- AIDD-FORGE:DIRECTIVE-{directive_id}:END -->"


# Mapa de audit_item_id -> funcao fixer (para uso pelo ConformEngine).
FIXER_MAP: dict[str, callable] = {
    "G01": lambda p: fix_g01_agents_md_missing(p),
    "G03": lambda p: fix_g03_ide_pointers(p),
    "G05": lambda p: fix_directive(p, "G05"),
    "G06": lambda p: fix_directive(p, "G06"),
    "G07": lambda p: fix_directive(p, "G07"),
    "G08": lambda p: fix_directive(p, "G08"),
    "G09": lambda p: fix_directive(p, "G09"),
    "G12": lambda p: fix_g12_gitignore(p),
    "G13": lambda p: fix_g13_gitattributes(p),
}
