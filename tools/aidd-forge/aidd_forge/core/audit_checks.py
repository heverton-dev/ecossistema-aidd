"""Conjunto de verificadores deterministas de conformidade de governanca.

Cada funcao recebe um `project_path` e retorna um `AuditItem` descrevendo
o resultado da verificacao. Zero LLM, zero chamadas de rede — apenas leitura
de arquivos, regex e heuristica de contagem de tokens.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from aidd_forge.core.context_linter import CHARS_PER_TOKEN, estimate_tokens
from aidd_forge.core.harness_manifest import carregar_todos_prefixos_harness

# Heuristica de deteccao de PT-BR: padroes comuns que indicam texto em portugues.
PT_BR_PATTERNS = re.compile(
    r"\b(?:ção|ções|não|são|está|estão|pode|podem|deve|devem|fazer|feito|"
    r"através|utilizando|utilizar|configuração|implementação|necessário|"
    r"obrigatório|resultado|componente|diretório|arquivo|conteúdo|"
    r"descrição|informações|instruções|funcionalidade|estrutura|"
    r"sobre|entre|quando|cada|para|como|mais|também|apenas|"
    r"deve|ser|ter|está|foram|será|podem|esta|esse|essa|este|esta)\b",
    re.IGNORECASE,
)

# Padroes de diretrizes de execucao que o audit procura no AGENTS.md.
DIRECTIVE_PATTERNS: dict[str, list[str]] = {
    "G05_THINKING_CONSTRAINT": [
        r"(?i)thinking\s+constraint",
        r"(?i)compact\s+english",
        r"(?i)under\s+\d+\s+words?\s+of\s+reasoning",
    ],
    "G06_EXECUTION_LIMIT": [
        r"(?i)\b3\s+to\s+5\b",
        r"(?i)\b3\s*-\s*5\s+(?:discrete\s+)?steps?",
        r"(?i)stop\s+and\s+request\s+(?:confirmation|user)",
    ],
    "G07_OUTPUT_FORMAT": [
        r"(?i)silent\s+executor",
        r"(?i)return\s+code\s+edits",
        r"(?i)1-line\s+execution\s+status",
    ],
    "G08_BASH_RULE": [
        r"(?i)pipe\s+verbose\s+commands",
        r"(?i)tail/grep",
        r"(?i)never\s+dump\s+raw\s+(?:bundle|output)",
    ],
    "G09_GRAPH_FIRST": [
        r"(?i)graph-first",
        r"(?i)query\s+(?:knowledge\s+)?graph\s+before",
        r"(?i)code-review-graph",
    ],
}

# Dimensoes de impacto.
IMPACT_MAP: dict[str, str] = {
    "G01": "CRITICAL",
    "G02": "HIGH",
    "G03": "HIGH",
    "G04": "MEDIUM",
    "G05": "HIGH",
    "G06": "MEDIUM",
    "G07": "HIGH",
    "G08": "MEDIUM",
    "G09": "MEDIUM",
    "G10": "CRITICAL",
    "G11": "HIGH",
    "G12": "CRITICAL",
    "G13": "MEDIUM",
    "G14": "MEDIUM",
    "G15": "CRITICAL",
}

MAX_CONTEXT_TOKENS = 1500
MAX_SKILL_DESC_WORDS = 20
GITIGNORE_REQUIRED_PATTERNS = ("node_modules/", "node_modules/**")

EXCLUDED_DIRS = frozenset({
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    "dist", "build", ".mypy_cache", ".pytest_cache", ".aidd",
})


@dataclass(frozen=True)
class AuditItem:
    """Resultado de uma verificacao de conformidade."""

    id: str
    category: str
    requirement: str
    status: str  # "PASS" | "FAIL" | "WARN" | "SKIP"
    details: str
    impact: str
    fixable: bool


def _find_agents_md(root: Path) -> Path | None:
    """Localiza o AGENTS.md principal (raiz ou governance/)."""
    for candidate in (root / "AGENTS.md", root / "governance" / "AGENTS.md"):
        if candidate.exists():
            return candidate
    return None


def _is_english_dominant(text: str) -> bool:
    """Heuristica: se <20% das palavras casam com padroes PT-BR, considera EN."""
    pt_matches = PT_BR_PATTERNS.findall(text)
    words = text.split()
    if not words:
        return True
    ratio = len(pt_matches) / len(words)
    return ratio < 0.20


def _has_pattern(content: str, patterns: list[str]) -> bool:
    """Verifica se algum padrao regex casa no conteudo."""
    return any(re.search(p, content) for p in patterns)


def _collect_agents_md_files(root: Path) -> list[Path]:
    """Coleta todos os AGENTS.md do projeto (excluindo dirs de build/venv)."""
    results: list[Path] = []
    for path in sorted(root.rglob("AGENTS.md")):
        parts = path.relative_to(root).parts
        if any(part in EXCLUDED_DIRS for part in parts):
            continue
        results.append(path)
    return results


def _collect_skill_files(root: Path) -> list[Path]:
    """Coleta todos os SKILL.md do projeto."""
    results: list[Path] = []
    for path in sorted(root.rglob("SKILL.md")):
        parts = path.relative_to(root).parts
        if any(part in EXCLUDED_DIRS for part in parts):
            continue
        results.append(path)
    return results


def _parse_frontmatter_description(content: str) -> str | None:
    """Extrai o campo 'description:' do frontmatter YAML de um SKILL.md."""
    lines = content.split("\n")
    in_frontmatter = False
    for line in lines:
        stripped = line.strip()
        if stripped == "---":
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter and stripped.lower().startswith("description:"):
            return stripped.split(":", 1)[1].strip().strip('"').strip("'")
    return None


def _content_has_timestamps_or_abs_paths(content: str) -> bool:
    """Detecta timestamps ou caminhos absolutos de SO no conteudo."""
    # Timestamps ISO-ish: 2024-01-15, 2024/01/15, etc.
    if re.search(r"\b20\d{2}[-/]\d{2}[-/]\d{2}", content):
        return True
    # Caminhos absolutos Windows: C:\... ou C:/...
    if re.search(r"[A-Z]:[/\\]", content):
        return True
    # Caminhos absolutos Unix: /home/..., /Users/..., /tmp/...
    if re.search(r"(?:^|\s)/(?:home|Users|tmp|var|opt|etc)/", content):
        return True
    return False


# ---------------------------------------------------------------------------
# Verificadores individuais (15 checks)
# ---------------------------------------------------------------------------


def check_g01_agents_md_exists(project_path: Path) -> AuditItem:
    """G01: Verifica se AGENTS.md existe na raiz ou em governance/."""
    found = _find_agents_md(project_path)
    return AuditItem(
        id="G01",
        category="Governance Core",
        requirement="AGENTS.md exists in project root or governance/",
        status="PASS" if found else "FAIL",
        details=f"found at {found.relative_to(project_path)}" if found else "AGENTS.md not found",
        impact=IMPACT_MAP["G01"],
        fixable=True,
    )


def check_g02_agents_md_language(project_path: Path) -> AuditItem:
    """G02: Verifica se o AGENTS.md esta primariamente em Ingles."""
    found = _find_agents_md(project_path)
    if not found:
        return AuditItem(
            id="G02", category="Governance Core",
            requirement="AGENTS.md content is primarily in English",
            status="SKIP", details="AGENTS.md not found, skipping language check",
            impact=IMPACT_MAP["G02"], fixable=False,
        )
    content = found.read_text(encoding="utf-8")
    is_english = _is_english_dominant(content)
    return AuditItem(
        id="G02", category="Governance Core",
        requirement="AGENTS.md content is primarily in English",
        status="PASS" if is_english else "FAIL",
        details="content is primarily in English" if is_english else "content has significant PT-BR content",
        impact=IMPACT_MAP["G02"], fixable=False,
    )


def check_g03_ide_pointers(project_path: Path) -> AuditItem:
    """G03: Verifica se CLAUDE.md/GEMINI.md existem com ponteiro para AGENTS.md."""
    pointer_files = ["CLAUDE.md", "GEMINI.md"]
    found_files = []
    missing_files = []
    no_pointer = []

    for name in pointer_files:
        path = project_path / name
        if not path.exists():
            missing_files.append(name)
            continue
        content = path.read_text(encoding="utf-8")
        if "AGENTS.md" in content or "@AGENTS.md" in content:
            found_files.append(name)
        else:
            no_pointer.append(name)

    if no_pointer:
        details = f"files missing pointer: {', '.join(no_pointer)}"
        status = "FAIL"
    elif missing_files and not found_files:
        details = f"pointer files missing: {', '.join(missing_files)}"
        status = "FAIL"
    else:
        details = f"pointers active: {', '.join(found_files)}"
        status = "PASS"

    return AuditItem(
        id="G03", category="Governance Core",
        requirement="CLAUDE.md/GEMINI.md exist with @AGENTS.md pointer",
        status=status, details=details,
        impact=IMPACT_MAP["G03"], fixable=True,
    )


def check_g04_agents_md_generic(project_path: Path) -> AuditItem:
    """G04: Verifica se o AGENTS.md da raiz nao contem specs operacionais de ferramentas."""
    found = _find_agents_md(project_path)
    if not found:
        return AuditItem(
            id="G04", category="Governance Core",
            requirement="Root AGENTS.md is generic (no tool-specific operational specs)",
            status="SKIP", details="AGENTS.md not found",
            impact=IMPACT_MAP["G04"], fixable=False,
        )
    content = found.read_text(encoding="utf-8")
    tool_operational_patterns = [
        r"(?i)(?:forge|generator|master|enterprise|ops|bridge)\s+(?:init|inject|run|build|deploy)",
        r"(?i)python\s+(?:-m\s+aidd_|ecossistema\.py)",
        r"(?i)(?:comando|slash\s+command).*?:",
    ]
    has_tool_specs = any(re.search(p, content) for p in tool_operational_patterns)
    return AuditItem(
        id="G04", category="Governance Core",
        requirement="Root AGENTS.md is generic (no tool-specific operational specs)",
        status="FAIL" if has_tool_specs else "PASS",
        details="contains tool-specific operational specs" if has_tool_specs else "generic as required",
        impact=IMPACT_MAP["G04"], fixable=False,
    )


def _check_directive(directive_id: str, directive_key: str, requirement: str) -> callable:
    """Fabrica uma funcao de verificacao para uma diretriz especifica."""
    patterns = DIRECTIVE_PATTERNS[directive_key]
    prefix = directive_id.split("_")[0]

    def checker(project_path: Path) -> AuditItem:
        found = _find_agents_md(project_path)
        if not found:
            return AuditItem(
                id=prefix, category="Execution Directives",
                requirement=requirement,
                status="SKIP", details="AGENTS.md not found",
                impact=IMPACT_MAP[prefix], fixable=True,
            )
        content = found.read_text(encoding="utf-8")
        has_it = _has_pattern(content, patterns)
        return AuditItem(
            id=prefix, category="Execution Directives",
            requirement=requirement,
            status="PASS" if has_it else "FAIL",
            details="directive present" if has_it else "directive missing",
            impact=IMPACT_MAP[prefix], fixable=True,
        )

    checker.__name__ = f"check_{directive_id.lower()}"
    return checker


check_g05_thinking_constraint = _check_directive(
    "G05", "G05_THINKING_CONSTRAINT",
    "AGENTS.md contains Thinking constraint directive",
)
check_g06_execution_limit = _check_directive(
    "G06", "G06_EXECUTION_LIMIT",
    "AGENTS.md contains execution limit (3-5 steps)",
)
check_g07_output_format = _check_directive(
    "G07", "G07_OUTPUT_FORMAT",
    "AGENTS.md contains Silent executor output format",
)
check_g08_bash_rule = _check_directive(
    "G08", "G08_BASH_RULE",
    "AGENTS.md contains Bash rule (tail/grep pipe)",
)
check_g09_graph_first = _check_directive(
    "G09", "G09_GRAPH_FIRST",
    "AGENTS.md contains Graph-first priority rule",
)


def check_g10_context_budget(project_path: Path) -> AuditItem:
    """G10: Verifica se todos os AGENTS.md estao abaixo do orcamento de tokens."""
    agents_files = _collect_agents_md_files(project_path)
    if not agents_files:
        return AuditItem(
            id="G10", category="Token Economy",
            requirement="All AGENTS.md files under token budget (<1500 tokens)",
            status="SKIP", details="no AGENTS.md files found",
            impact=IMPACT_MAP["G10"], fixable=False,
        )

    over_budget: list[tuple[Path, int]] = []
    for path in agents_files:
        content = path.read_text(encoding="utf-8")
        tokens = estimate_tokens(content)
        if tokens > MAX_CONTEXT_TOKENS:
            over_budget.append((path, tokens))

    if over_budget:
        details = "; ".join(
            f"{p.relative_to(project_path)}={t} tokens" for p, t in over_budget
        )
        return AuditItem(
            id="G10", category="Token Economy",
            requirement="All AGENTS.md files under token budget (<1500 tokens)",
            status="FAIL", details=f"over budget: {details}",
            impact=IMPACT_MAP["G10"], fixable=False,
        )

    return AuditItem(
        id="G10", category="Token Economy",
        requirement="All AGENTS.md files under token budget (<1500 tokens)",
        status="PASS",
        details=f"all {len(agents_files)} file(s) within budget",
        impact=IMPACT_MAP["G10"], fixable=False,
    )


def check_g11_skills_frontmatter(project_path: Path) -> AuditItem:
    """G11: Verifica se descriptions de skills sao 1 linha e <=20 palavras."""
    skill_files = _collect_skill_files(project_path)
    if not skill_files:
        return AuditItem(
            id="G11", category="Token Economy",
            requirement="SKILL.md descriptions are single-line and <=20 words",
            status="SKIP", details="no SKILL.md files found",
            impact=IMPACT_MAP["G11"], fixable=False,
        )

    violations: list[str] = []
    for path in skill_files:
        content = path.read_text(encoding="utf-8")
        desc = _parse_frontmatter_description(content)
        if desc is None:
            violations.append(f"{path.relative_to(project_path)}: no description field")
            continue
        if "\n" in desc:
            violations.append(f"{path.relative_to(project_path)}: multi-line description")
            continue
        word_count = len(desc.split())
        if word_count > MAX_SKILL_DESC_WORDS:
            violations.append(f"{path.relative_to(project_path)}: {word_count} words (max {MAX_SKILL_DESC_WORDS})")

    if violations:
        return AuditItem(
            id="G11", category="Token Economy",
            requirement="SKILL.md descriptions are single-line and <=20 words",
            status="FAIL", details=f"{len(violations)} violation(s): {'; '.join(violations[:3])}",
            impact=IMPACT_MAP["G11"], fixable=False,
        )

    return AuditItem(
        id="G11", category="Token Economy",
        requirement="SKILL.md descriptions are single-line and <=20 words",
        status="PASS", details=f"all {len(skill_files)} skill(s) compliant",
        impact=IMPACT_MAP["G11"], fixable=False,
    )


def check_g12_gitignore(project_path: Path) -> AuditItem:
    """G12: Verifica se .gitignore ignora node_modules/.

    Lockfiles NAO entram: ignora-los quebra `npm ci`/instalacao reproduzivel no CI.
    """
    gitignore_path = project_path / ".gitignore"
    if not gitignore_path.exists():
        return AuditItem(
            id="G12", category="Repository Hygiene",
            requirement=".gitignore contains node_modules/ (lockfiles stay versioned)",
            status="FAIL", details=".gitignore not found",
            impact=IMPACT_MAP["G12"], fixable=True,
        )

    content = gitignore_path.read_text(encoding="utf-8")
    missing: list[str] = []

    if "node_modules" not in content:
        missing.append("node_modules/")

    if missing:
        return AuditItem(
            id="G12", category="Repository Hygiene",
            requirement=".gitignore contains node_modules/ (lockfiles stay versioned)",
            status="FAIL", details=f"missing: {', '.join(missing)}",
            impact=IMPACT_MAP["G12"], fixable=True,
        )

    return AuditItem(
        id="G12", category="Repository Hygiene",
        requirement=".gitignore contains node_modules/ (lockfiles stay versioned)",
        status="PASS", details="all required patterns present",
        impact=IMPACT_MAP["G12"], fixable=True,
    )


def check_g13_gitattributes(project_path: Path) -> AuditItem:
    """G13: Verifica se .gitattributes existe com forca LF."""
    gitattributes_path = project_path / ".gitattributes"
    if not gitattributes_path.exists():
        return AuditItem(
            id="G13", category="Repository Hygiene",
            requirement=".gitattributes exists with '* text=auto eol=lf'",
            status="FAIL", details=".gitattributes not found",
            impact=IMPACT_MAP["G13"], fixable=True,
        )

    content = gitattributes_path.read_text(encoding="utf-8")
    has_lf = "text=auto" in content and "eol=lf" in content

    return AuditItem(
        id="G13", category="Repository Hygiene",
        requirement=".gitattributes exists with '* text=auto eol=lf'",
        status="PASS" if has_lf else "FAIL",
        details="LF enforcement active" if has_lf else "missing LF enforcement rule",
        impact=IMPACT_MAP["G13"], fixable=True,
    )


def check_g14_no_duplicates(project_path: Path) -> AuditItem:
    """G14: Verifica duplicatas entre componentes/ e QUALQUER pasta de harness
    confirmada em `gates/manifesto_harnesses.json` (via `harness_manifest`)."""
    comp_dir = project_path / "componentes"
    if not comp_dir.exists():
        return AuditItem(
            id="G14", category="Repository Hygiene",
            requirement="No file-level duplicates between componentes/ and harness dirs",
            status="PASS", details="no componentes/ directory (skip)",
            impact=IMPACT_MAP["G14"], fixable=False,
        )

    # ".agent" e a pasta canonica-fonte (nao um harness em si); os demais vem do
    # manifesto (achado real 2026-09-15: a lista fixa antiga faltava Antigravity,
    # OpenCode e CodeBuddy — duplicatas nessas pastas passavam batido).
    harness_dirs = [".agent", *carregar_todos_prefixos_harness()]
    duplicates: list[str] = []

    for harness_name in harness_dirs:
        harness_dir = project_path / harness_name
        if not harness_dir.exists():
            continue
        for comp_file in sorted(comp_dir.rglob("*")):
            if comp_file.is_dir():
                continue
            relative = comp_file.relative_to(comp_dir)
            harness_file = harness_dir / relative
            if harness_file.exists():
                duplicates.append(
                    f"{comp_file.relative_to(project_path)} <-> {harness_file.relative_to(project_path)}"
                )

    if duplicates:
        return AuditItem(
            id="G14", category="Repository Hygiene",
            requirement="No file-level duplicates between componentes/ and harness dirs",
            status="WARN", details=f"{len(duplicates)} duplicate(s): {duplicates[0]}",
            impact=IMPACT_MAP["G14"], fixable=False,
        )

    return AuditItem(
        id="G14", category="Repository Hygiene",
        requirement="No file-level duplicates between componentes/ and harness dirs",
        status="PASS", details="no duplicates detected",
        impact=IMPACT_MAP["G14"], fixable=False,
    )


def check_g15_cache_prefix(project_path: Path) -> AuditItem:
    """G15: Verifica se AGENTS.md nao contem timestamps ou caminhos absolutos."""
    agents_files = _collect_agents_md_files(project_path)
    if not agents_files:
        return AuditItem(
            id="G15", category="Cache Invariance",
            requirement="No timestamps or absolute OS paths in AGENTS.md files",
            status="SKIP", details="no AGENTS.md files found",
            impact=IMPACT_MAP["G15"], fixable=False,
        )

    violations: list[str] = []
    for path in agents_files:
        content = path.read_text(encoding="utf-8")
        if _content_has_timestamps_or_abs_paths(content):
            violations.append(str(path.relative_to(project_path)))

    if violations:
        return AuditItem(
            id="G15", category="Cache Invariance",
            requirement="No timestamps or absolute OS paths in AGENTS.md files",
            status="FAIL", details=f"volatile content in: {', '.join(violations)}",
            impact=IMPACT_MAP["G15"], fixable=False,
        )

    return AuditItem(
        id="G15", category="Cache Invariance",
        requirement="No timestamps or absolute OS paths in AGENTS.md files",
        status="PASS", details="all files free of volatile content",
        impact=IMPACT_MAP["G15"], fixable=False,
    )


# Lista ordenada de todos os checks para uso pelo AuditEngine.
ALL_CHECKS: list[callable] = [
    check_g01_agents_md_exists,
    check_g02_agents_md_language,
    check_g03_ide_pointers,
    check_g04_agents_md_generic,
    check_g05_thinking_constraint,
    check_g06_execution_limit,
    check_g07_output_format,
    check_g08_bash_rule,
    check_g09_graph_first,
    check_g10_context_budget,
    check_g11_skills_frontmatter,
    check_g12_gitignore,
    check_g13_gitattributes,
    check_g14_no_duplicates,
    check_g15_cache_prefix,
]
