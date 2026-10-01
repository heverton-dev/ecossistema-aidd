#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Caveman Ultra Linter — validates LLM prompt constants follow the triad:
  ENTRADA (EN)  → system prompt / operational instructions in English
  COT           → telegraphic chain-of-thought in English Caveman (3-5 lines, no articles)
  SAIDA (PT-BR) → output, artifacts, code, logs in Brazilian Portuguese

Static analysis only — no LLM calls, zero tokens.

Usage:
  python -m scripts.core.caveman_linter scripts/phases/02_analisador.py
  python -m scripts.core.caveman_linter scripts/phases/  # lint all .py in dir
"""

import ast
import re
import sys
import unicodedata
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

# =============================================================================
# CONSTANTS
# =============================================================================

# Marker patterns that signal each layer in a prompt string
MARKER_ENTRADA = re.compile(
    r'#\s*ENTRADA\b|'
    r'#\s*INPUT\b|'
    r'#\s*SYSTEM\s+PROMPT\b|'
    r'You\s+are\s+a\b|'
    r'You\s+are\s+an\b|'
    r'Analyze\b|'
    r'Implement\b|'
    r'Generate\b|'
    r'Define\b|'
    r'Create\b',
    re.IGNORECASE
)

MARKER_COT = re.compile(
    r'#\s*COT\b|'
    r'#\s*CAVEMAN\b|'
    r'#\s*THINK\b|'
    r'think\s+step\s+by\s+step|'
    r'chain.of.thought|'
    r'internal\s+reasoning',
    re.IGNORECASE
)

MARKER_SAIDA = re.compile(
    r'#\s*SA[IÍ]DA\b|'
    r'#\s*OUTPUT\b|'
    r'RETORNE\s+UM\s+JSON|'
    r'SA[IÍ]DA\s*\(|'
    r'RESPONDA\s+EM\s+PORTUGU[EÊ]S|'
    r'em\s+portugu[eê]s\s+do\s+brasil|'
    r'PT-BR',
    re.IGNORECASE
)

# PT-BR output instruction patterns
PTBR_OUTPUT_PATTERN = re.compile(
    r'portugu[eê]s|PT-BR|pt-BR|pt_BR|'
    r'RESPONDA EM|RETORNE|responda em portugu[eê]s|'
    r'Saída.*portugu[eê]s|Output.*Portugu[eê]s',
    re.IGNORECASE
)

# English word ratio heuristic: common English function words
ENGLISH_INDICATORS = {
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'shall', 'can', 'must', 'need',
    'this', 'that', 'these', 'those', 'it', 'its',
    'you', 'your', 'yours', 'we', 'our', 'ours', 'they', 'their',
    'for', 'from', 'with', 'without', 'into', 'onto', 'upon',
    'each', 'every', 'all', 'any', 'few', 'more', 'most', 'other',
    'if', 'then', 'else', 'when', 'where', 'how', 'what', 'which',
    'who', 'whom', 'whose', 'why',
    'not', 'no', 'nor', 'but', 'or', 'and', 'so',
    'only', 'just', 'also', 'very', 'too', 'quite', 'rather',
    'define', 'create', 'generate', 'implement', 'analyze', 'return',
    'output', 'input', 'must', 'should', 'never', 'always',
    'json', 'valid', 'error', 'test', 'script', 'function', 'code',
    'project', 'phase', 'layer', 'schema', 'gate', 'stack',
}

# Portuguese word indicators (high-confidence)
PORTUGUESE_INDICATORS = {
    'você', 'voce', 'é', 'são', 'está', 'estão', 'esta', 'estao',
    'não', 'nao', 'sim', 'também', 'tambem', 'mas', 'porém', 'porem',
    'então', 'entao', 'quando', 'onde', 'como', 'porque', 'porquê',
    'qual', 'quais', 'quem', 'cujo', 'cuja',
    'um', 'uma', 'uns', 'umas', 'do', 'da', 'dos', 'das', 'no', 'na',
    'nos', 'nas', 'ao', 'à', 'aos', 'às', 'pelo', 'pela', 'pelos',
    'pelas', 'dele', 'dela', 'deles', 'delas',
    'meu', 'minha', 'meus', 'minhas', 'seu', 'sua', 'seus', 'suas',
    'nosso', 'nossa', 'nossos', 'nossas',
    'ser', 'estar', 'ter', 'fazer', 'poder', 'querer', 'saber',
    'deve', 'deveria', 'pode', 'precisa', 'obrigatório', 'obrigatorio',
    'específico', 'especifico', 'análise', 'analise', 'projeto',
    'camada', 'validação', 'validacao', 'resultado', 'estrutura',
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class LintResult:
    """Result of linting a single prompt constant."""
    name: str
    file_path: str
    line_number: int
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, any] = field(default_factory=dict)


@dataclass
class LintReport:
    """Aggregated lint report for one or more files."""
    file_path: str
    results: List[LintResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)

    @property
    def total_prompts(self) -> int:
        return len(self.results)

    @property
    def total_passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def total_failed(self) -> int:
        return self.total_prompts - self.total_passed

    def to_dict(self) -> Dict:
        return {
            'file': self.file_path,
            'total_prompts': self.total_prompts,
            'passed': self.total_passed,
            'failed': self.total_failed,
            'all_passed': self.passed,
            'details': [
                {
                    'name': r.name,
                    'line': r.line_number,
                    'passed': r.passed,
                    'errors': r.errors,
                    'warnings': r.warnings,
                    'metrics': r.metrics,
                }
                for r in self.results
            ]
        }


# =============================================================================
# LANGUAGE DETECTION
# =============================================================================

def _tokenize(text: str) -> List[str]:
    """Split text into lowercase word tokens."""
    return re.findall(r'[a-záàâãéèêíïóôõúüç]+', text.lower())


def _compute_english_ratio(text: str) -> float:
    """Ratio of tokens that match English indicator words (0.0-1.0)."""
    tokens = _tokenize(text)
    if not tokens:
        return 0.0
    en_count = sum(1 for t in tokens if t in ENGLISH_INDICATORS)
    return en_count / len(tokens)


def _compute_portuguese_ratio(text: str) -> float:
    """Ratio of tokens that match Portuguese indicator words (0.0-1.0)."""
    tokens = _tokenize(text)
    if not tokens:
        return 0.0
    pt_count = sum(1 for t in tokens if t in PORTUGUESE_INDICATORS)
    return pt_count / len(tokens)


def _has_portuguese_diacritics(text: str) -> bool:
    """Check if text contains Portuguese-specific diacritics."""
    pt_chars = set('áàâãéèêíïóôõúüçñ')
    # Check NFC-normalized text (precomposed) so 'á' matches as a single char
    normalized = unicodedata.normalize('NFC', text.lower())
    return any(c in pt_chars for c in normalized)


# =============================================================================
# PROMPT EXTRACTION
# =============================================================================

def _extract_prompt_constants(filepath: Path) -> List[Tuple[str, str, int]]:
    """Extract module-level string constants that look like LLM prompts.

    Returns list of (name, value, line_number).
    Only considers UPPER_CASE string assignments at module level.
    """
    try:
        source = filepath.read_text(encoding='utf-8')
    except (UnicodeDecodeError, FileNotFoundError):
        return []

    tree = ast.parse(source, filename=str(filepath))
    prompts = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        value = node.value.value
                        # Heuristic: prompts are typically > 100 chars
                        if len(value) > 100:
                            prompts.append((target.id, value, node.value.lineno))
                    elif isinstance(node.value, ast.Dict):
                        # Handle dict of prompts (like PROMPTS_SUBAGENTES)
                        for key, val in zip(node.value.keys, node.value.values):
                            if isinstance(key, ast.Constant) and isinstance(val, ast.Constant):
                                if isinstance(val.value, str) and len(val.value) > 100:
                                    name = f"{target.id}[{key.value!r}]"
                                    prompts.append((name, val.value, val.lineno))

    return prompts


# =============================================================================
# LINT RULES
# =============================================================================

def lint_single_prompt(name: str, value: str, line_number: int, filepath: str) -> LintResult:
    """Apply Caveman Ultra triad rules to a single prompt constant."""
    result = LintResult(
        name=name,
        file_path=filepath,
        line_number=line_number,
        passed=True,
    )

    en_ratio = _compute_english_ratio(value)
    pt_ratio = _compute_portuguese_ratio(value)
    has_diacritics = _has_portuguese_diacritics(value)

    result.metrics = {
        'length_chars': len(value),
        'english_word_ratio': round(en_ratio, 3),
        'portuguese_word_ratio': round(pt_ratio, 3),
        'has_portuguese_diacritics': has_diacritics,
    }

    # --- RULE 1: ENTRADA — operational instructions must be primarily English ---
    # The prompt body (instructions to the LLM) should be in English for BPE economy.
    # We allow PT-BR in output-directed sections and examples.
    if en_ratio < 0.08 and len(value) > 200:
        result.errors.append(
            f"ENTRADA: English word ratio too low ({en_ratio:.1%}). "
            f"System prompts must be primarily in English for BPE economy (30-50% savings)."
        )
        result.passed = False

    # --- RULE 2: COT — must include caveman/telegraphic thinking instruction ---
    has_cot_marker = bool(MARKER_COT.search(value))
    # Also check for the explicit instruction pattern
    has_cot_instruction = bool(re.search(
        r'think.*caveman|caveman.*think|chain.of.thought|step.by.step|'
        r'think\s+before\s+answer|reasoning\s+step|internal\s+thinking|'
        r'Before\s+responding.*think|think\s+telegraphic',
        value, re.IGNORECASE
    ))

    if not has_cot_marker and not has_cot_instruction:
        # Soft check: warn but don't fail if the prompt is short (< 500 chars)
        if len(value) > 500:
            result.warnings.append(
                "COT: No caveman/telegraphic thinking instruction found. "
                "Consider adding '# COT: think in English Caveman (3-5 dense lines, no articles)' "
                "or equivalent instruction for internal reasoning."
            )

    # --- RULE 3: SAIDA — must direct output to PT-BR ---
    has_ptbr = bool(PTBR_OUTPUT_PATTERN.search(value))

    # For prompts that produce structured output (JSON), check for PT-BR instruction
    produces_output = bool(re.search(
        r'RETURN|RETORNE|OUTPUT|SAÍDA|SAIDA|JSON|response|answer|result',
        value, re.IGNORECASE
    ))

    if produces_output and not has_ptbr and len(value) > 200:
        result.warnings.append(
            "SAIDA: Prompt produces output but does not explicitly direct PT-BR response. "
            "Consider adding 'Respond in Brazilian Portuguese (PT-BR)' instruction."
        )

    # --- RULE 4: No mixed-language operational instructions ---
    # Detect if the prompt mixes PT and EN in the same instruction block
    # (not in examples/JSON, which are fine)
    lines = value.split('\n')
    instruction_lines = [
        l.strip() for l in lines
        if l.strip() and not l.strip().startswith('{') and not l.strip().startswith('#')
        and not l.strip().startswith('-') and len(l.strip()) > 20
    ]

    pt_instruction_lines = 0
    en_instruction_lines = 0
    for line in instruction_lines:
        line_en = _compute_english_ratio(line)
        line_pt = _compute_portuguese_ratio(line)
        if line_pt > 0.15 and _has_portuguese_diacritics(line):
            pt_instruction_lines += 1
        elif line_en > 0.1:
            en_instruction_lines += 1

    if pt_instruction_lines > 3 and en_instruction_lines > 3:
        result.warnings.append(
            f"MIX: Prompt has {pt_instruction_lines} PT-BR instruction lines mixed with "
            f"{en_instruction_lines} EN instruction lines. "
            f"Keep operational instructions in English; reserve PT-BR for output directives."
        )

    return result


# =============================================================================
# PUBLIC API
# =============================================================================

def lint_file(filepath: Path) -> LintReport:
    """Lint all prompt constants in a single Python file.

    Returns LintReport with per-prompt results.
    """
    report = LintReport(file_path=str(filepath))
    prompts = _extract_prompt_constants(filepath)

    for name, value, line_number in prompts:
        result = lint_single_prompt(name, value, line_number, str(filepath))
        report.results.append(result)

    return report


def lint_directory(dirpath: Path) -> List[LintReport]:
    """Lint all .py files in a directory (non-recursive)."""
    reports = []
    for py_file in sorted(dirpath.glob('*.py')):
        if py_file.name.startswith('_') and py_file.name != '__init__.py':
            continue
        report = lint_file(py_file)
        if report.results:  # only include files that have prompts
            reports.append(report)
    return reports


def format_report(reports: List[LintReport], verbose: bool = False) -> str:
    """Format lint reports as human-readable text."""
    lines = []
    total_prompts = sum(r.total_prompts for r in reports)
    total_passed = sum(r.total_passed for r in reports)
    total_failed = sum(r.total_failed for r in reports)

    lines.append("=" * 70)
    lines.append("CAVEMAN ULTRA LINTER — Report")
    lines.append("=" * 70)
    lines.append(f"Files scanned: {len(reports)}")
    lines.append(f"Prompts found: {total_prompts}")
    lines.append(f"Passed: {total_passed}  |  Failed: {total_failed}")
    lines.append("")

    for report in reports:
        status = "PASS" if report.passed else "FAIL"
        lines.append(f"[{status}] {report.file_path} ({report.total_passed}/{report.total_prompts})")

        for r in report.results:
            icon = "  OK" if r.passed else "FAIL"
            lines.append(f"  [{icon}] {r.name} (line {r.line_number})")

            if r.errors:
                for err in r.errors:
                    lines.append(f"       ERROR: {err}")
            if r.warnings and verbose:
                for warn in r.warnings:
                    lines.append(f"       WARN:  {warn}")
            if verbose and r.metrics:
                m = r.metrics
                lines.append(
                    f"       METRICS: len={m['length_chars']}, "
                    f"en_ratio={m['english_word_ratio']:.1%}, "
                    f"pt_ratio={m['portuguese_word_ratio']:.1%}"
                )

        lines.append("")

    lines.append("=" * 70)
    if total_failed == 0:
        lines.append("ALL PROMPTS PASS — Caveman Ultra triad validated.")
    else:
        lines.append(f"{total_failed} PROMPT(S) FAILED — fix errors above.")
    lines.append("=" * 70)

    return "\n".join(lines)


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def main():
    """CLI: lint file(s) and print report."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Caveman Ultra Linter — validate prompt triad (EN/CoT/PT-BR)'
    )
    parser.add_argument('paths', nargs='+', help='File(s) or directory(ies) to lint')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show warnings and metrics')

    args = parser.parse_args()

    all_reports = []
    for p in args.paths:
        path = Path(p)
        if path.is_dir():
            all_reports.extend(lint_directory(path))
        elif path.is_file():
            report = lint_file(path)
            if report.results:
                all_reports.append(report)
        else:
            print(f"WARNING: {p} not found, skipping", file=sys.stderr)

    if not all_reports:
        print("No prompt constants found in specified paths.")
        sys.exit(0)

    print(format_report(all_reports, verbose=args.verbose))

    if all(r.passed for r in all_reports):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
