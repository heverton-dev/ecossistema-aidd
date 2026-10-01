#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Caveman Ultra Linter — validates that all LLM prompts in
scripts/phases/ follow the triad protocol:
  ENTRADA (EN)  → operational instructions in English
  COT           → telegraphic chain-of-thought in English Caveman
  SAIDA (PT-BR) → output directed to Brazilian Portuguese
"""

import sys
from pathlib import Path

import pytest

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.core.caveman_linter import (
    lint_file,
    lint_directory,
    lint_single_prompt,
    _compute_english_ratio,
    _compute_portuguese_ratio,
    _has_portuguese_diacritics,
    _extract_prompt_constants,
    LintResult,
    LintReport,
)


# =============================================================================
# FIXTURES
# =============================================================================

PHASES_DIR = PROJECT_ROOT / 'scripts' / 'phases'


@pytest.fixture
def sample_prompt_en_cot_ptbr():
    """A well-formed prompt following the Caveman Ultra triad."""
    return """# ENTRADA: Project Analyzer — analyze the project idea and references.

You are an AIDD Project Analyst specialized in structured analysis.

Analyze the PROVIDED project idea and SIMILAR REFERENCES.

PROJECT IDEA: test idea
REFERENCES: test references

For each field below, be specific:
1. **objetivo** (1-2 lines): What does the project do?
2. **publico_alvo** (1 line): Who will use it?
3. **constraints** (3-5 bullets): Technical limitations

# COT: think in English Caveman (3-5 dense lines, no articles):
# "check idea → extract domain → map to stack → validate refs → output JSON"

# SAIDA: Return VALID JSON only. RESPOND IN BRAZILIAN PORTUGUESE (PT-BR).

{
  "objetivo": "...",
  "publico_alvo": "...",
  "constraints": ["..."]
}

CRITICAL: Return ONLY valid JSON, nothing else."""


@pytest.fixture
def sample_prompt_pt_only():
    """A prompt entirely in Portuguese (should fail ENTRADA rule)."""
    return """Você é um Analista de Projetos AIDD especializado.

Analise a ideia do projeto FORNECIDA e as REFERÊNCIAS similares encontradas.

Para cada campo abaixo, seja específico e cite as referências quando aplicável.

1. **objetivo** (1-2 linhas): O que o projeto faz? Qual problema resolve?
2. **publico_alvo** (1 linha): Quem vai usar? Engenheiros? Empresas? Educadores?
3. **constraints** (3-5 bullets): Limitações técnicas/de negócio
   - Exemplo: "Zero download de binários"
   - Exemplo: "Máxima economia de tokens"
4. **stack_recomendado**: JSON com linguagem, framework, banco, libs_principais
5. **arquitetura** (1 parágrafo): Visão geral. Camadas? Fluxo?
6. **referencias_utilizadas**: Lista exata das referências que você citou

RETORNE UM JSON VÁLIDO (sem markdown, sem ```json, sem blabla):

{
  "objetivo": "...",
  "publico_alvo": "...",
  "constraints": ["...", "..."],
  "stack_recomendado": {
    "linguagem": "...",
    "framework": "...",
    "banco": "...",
    "libs_principais": ["..."]
  },
  "arquitetura": "...",
  "referencias_utilizadas": ["referência1", "referência2"]
}

CRÍTICO: Mantenha zero alucinação. Só cite referências que estão na lista acima.
CRÍTICO: Retorne APENAS JSON válido, nada mais."""


@pytest.fixture
def sample_prompt_no_cot():
    """A prompt missing the COT section."""
    return """# ENTRADA: Project Analyzer — analyze the project idea.

You are an AIDD Project Analyst. Analyze the project idea and references.
For each field below, be specific and cite references when applicable.

1. **objetivo** (1-2 lines): What does the project do?
2. **publico_alvo** (1 line): Who will use it?
3. **constraints** (3-5 bullets): Technical limitations
4. **stack_recomendado**: JSON with linguagem, framework, banco, libs_principais
5. **arquitetura** (1 paragraph): Overview. Layers? Flow?
6. **referencias_utilizadas**: Exact list of references you cited

# SAIDA: Return VALID JSON only. RESPOND IN BRAZILIAN PORTUGUESE (PT-BR).

{
  "objetivo": "...",
  "publico_alvo": "...",
  "constraints": ["..."]
}

CRITICAL: Return ONLY valid JSON, nothing else."""


# =============================================================================
# UNIT TESTS — Language Detection
# =============================================================================

class TestLanguageDetection:
    """Test English/Portuguese ratio computation."""

    def test_english_ratio_pure_english(self):
        text = "You are an analyst. Analyze the project idea and define the stack."
        ratio = _compute_english_ratio(text)
        assert ratio > 0.15, f"Expected >15% English ratio, got {ratio:.1%}"

    def test_english_ratio_pure_portuguese(self):
        # Note: shared words like "e", "de", "o" inflate English ratio slightly.
        # A pure PT text should stay well below an English-heavy prompt (>30%).
        text = "Você é um analista. Analise a ideia do projeto e defina o stack."
        ratio = _compute_english_ratio(text)
        assert ratio < 0.30, f"Expected <30% English ratio for PT text, got {ratio:.1%}"

    def test_portuguese_ratio_pure_portuguese(self):
        text = "Você é um analista especializado. Analise a ideia do projeto."
        ratio = _compute_portuguese_ratio(text)
        assert ratio > 0.10, f"Expected >10% Portuguese ratio, got {ratio:.1%}"

    def test_portuguese_diacritics_detected(self):
        text = "Análise específica com validação e determinação"
        assert _has_portuguese_diacritics(text) is True

    def test_no_diacritics_in_english(self):
        text = "Analyze the specific validation and determination"
        assert _has_portuguese_diacritics(text) is False

    def test_empty_text(self):
        assert _compute_english_ratio("") == 0.0
        assert _compute_portuguese_ratio("") == 0.0


# =============================================================================
# UNIT TESTS — Prompt Extraction
# =============================================================================

class TestPromptExtraction:
    """Test that prompt constants are correctly extracted from Python files."""

    def test_extracts_prompts_from_phase02(self):
        prompts = _extract_prompt_constants(PHASES_DIR / '02_analisador.py')
        names = [p[0] for p in prompts]
        assert 'PROMPT_ANALISADOR_IDEIA' in names

    def test_extracts_prompts_from_phase03(self):
        prompts = _extract_prompt_constants(PHASES_DIR / '03_designer.py')
        names = [p[0] for p in prompts]
        # Should extract dict entries
        assert any('PROMPTS_SUBAGENTES' in n for n in names)

    def test_extracts_prompts_from_phase08(self):
        prompts = _extract_prompt_constants(PHASES_DIR / '08_implementador.py')
        names = [p[0] for p in prompts]
        assert 'PROMPT_GERAR_SCHEMA_COMPARTILHADO' in names
        assert 'PROMPT_IMPLEMENTAR_SCRIPT' in names
        assert 'PROMPT_CORRIGIR_SCRIPT' in names
        assert 'PROMPT_GERAR_TESTE_INTEGRACAO' in names

    def test_no_prompts_in_deterministic_phases(self):
        """Phases 1, 4, 5, 6, 7 are 100% deterministic — no LLM prompts."""
        for phase_file in ['01_pesquisador.py', '04_decisor.py', '05_criador.py',
                           '06_documentador.py', '07_analisador.py']:
            prompts = _extract_prompt_constants(PHASES_DIR / phase_file)
            assert len(prompts) == 0, (
                f"{phase_file} should have no LLM prompt constants, "
                f"found: {[p[0] for p in prompts]}"
            )


# =============================================================================
# UNIT TESTS — Lint Rules
# =============================================================================

class TestLintRules:
    """Test individual lint rules on synthetic prompts."""

    def test_well_formed_prompt_passes(self, sample_prompt_en_cot_ptbr):
        result = lint_single_prompt('TEST_PROMPT', sample_prompt_en_cot_ptbr, 1, 'test.py')
        assert result.passed is True
        assert len(result.errors) == 0

    def test_portuguese_only_prompt_fails_entrada(self, sample_prompt_pt_only):
        result = lint_single_prompt('TEST_PROMPT', sample_prompt_pt_only, 1, 'test.py')
        assert result.passed is False
        assert any('ENTRADA' in e for e in result.errors)

    def test_no_cot_prompt_warns(self, sample_prompt_no_cot):
        result = lint_single_prompt('TEST_PROMPT', sample_prompt_no_cot, 1, 'test.py')
        # Should warn about missing COT (prompt is > 500 chars)
        assert any('COT' in w for w in result.warnings)

    def test_short_prompt_no_false_positive(self):
        """Short prompts (< 200 chars) should not trigger ENTRADA failure."""
        short_prompt = "Analyze this project idea and return JSON with objetivo and stack."
        result = lint_single_prompt('SHORT', short_prompt, 1, 'test.py')
        # Short prompts are exempt from strict EN ratio check
        assert result.passed is True

    def test_metrics_populated(self, sample_prompt_en_cot_ptbr):
        result = lint_single_prompt('TEST', sample_prompt_en_cot_ptbr, 1, 'test.py')
        assert 'length_chars' in result.metrics
        assert 'english_word_ratio' in result.metrics
        assert 'portuguese_word_ratio' in result.metrics
        assert result.metrics['length_chars'] > 100


# =============================================================================
# INTEGRATION TESTS — Real Phase Files
# =============================================================================

class TestRealPhaseFiles:
    """Integration tests: lint the actual phase script prompt constants."""

    def test_phase02_prompts_pass_linter(self):
        """Phase 02 (Analisador) prompts must follow Caveman Ultra triad."""
        report = lint_file(PHASES_DIR / '02_analisador.py')
        assert report.total_prompts > 0, "No prompts found in 02_analisador.py"
        failed = [r for r in report.results if not r.passed]
        assert len(failed) == 0, (
            f"Phase 02 prompts failed linter:\n"
            + "\n".join(f"  {r.name}: {r.errors}" for r in failed)
        )

    def test_phase03_prompts_pass_linter(self):
        """Phase 03 (Designer) prompts must follow Caveman Ultra triad."""
        report = lint_file(PHASES_DIR / '03_designer.py')
        assert report.total_prompts > 0, "No prompts found in 03_designer.py"
        failed = [r for r in report.results if not r.passed]
        assert len(failed) == 0, (
            f"Phase 03 prompts failed linter:\n"
            + "\n".join(f"  {r.name}: {r.errors}" for r in failed)
        )

    def test_phase08_prompts_pass_linter(self):
        """Phase 08 (Implementador) prompts must follow Caveman Ultra triad."""
        report = lint_file(PHASES_DIR / '08_implementador.py')
        assert report.total_prompts > 0, "No prompts found in 08_implementador.py"
        failed = [r for r in report.results if not r.passed]
        assert len(failed) == 0, (
            f"Phase 08 prompts failed linter:\n"
            + "\n".join(f"  {r.name}: {r.errors}" for r in failed)
        )

    def test_all_phase_files_lint_clean(self):
        """Full directory scan: every prompt in scripts/phases/ must pass."""
        reports = lint_directory(PHASES_DIR)
        all_failed = []
        for report in reports:
            for r in report.results:
                if not r.passed:
                    all_failed.append(f"{r.file_path}:{r.name} — {r.errors}")
        assert len(all_failed) == 0, (
            f"Caveman Ultra linter found {len(all_failed)} failing prompt(s):\n"
            + "\n".join(f"  {f}" for f in all_failed)
        )

    def test_all_prompts_have_cot_instruction(self):
        """Every prompt constant must include a COT instruction (warning-level)."""
        reports = lint_directory(PHASES_DIR)
        missing_cot = []
        for report in reports:
            for r in report.results:
                has_cot_warning = any('COT' in w for w in r.warnings)
                if has_cot_warning:
                    missing_cot.append(f"{r.file_path}:{r.name}")
        assert len(missing_cot) == 0, (
            f"Prompts missing COT instruction:\n"
            + "\n".join(f"  {m}" for m in missing_cot)
        )

    def test_prompt_count_per_file(self):
        """Verify expected prompt counts per phase file."""
        expected = {
            '02_analisador.py': 1,
            '03_designer.py': 5,  # 5 subagent prompts in dict
            '08_implementador.py': 4,
        }
        for filename, min_count in expected.items():
            report = lint_file(PHASES_DIR / filename)
            assert report.total_prompts >= min_count, (
                f"{filename}: expected >= {min_count} prompts, found {report.total_prompts}"
            )


# =============================================================================
# INTEGRATION TESTS — Lint Report Structure
# =============================================================================

class TestLintReport:
    """Test report data structures."""

    def test_report_to_dict(self):
        report = lint_file(PHASES_DIR / '02_analisador.py')
        d = report.to_dict()
        assert 'file' in d
        assert 'total_prompts' in d
        assert 'passed' in d
        assert 'failed' in d
        assert 'all_passed' in d
        assert 'details' in d
        assert isinstance(d['details'], list)

    def test_report_properties(self):
        report = lint_file(PHASES_DIR / '02_analisador.py')
        assert report.total_prompts == report.total_passed + report.total_failed
        assert report.passed == (report.total_failed == 0)


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Edge case tests for robustness."""

    def test_nonexistent_file(self):
        report = lint_file(Path('/nonexistent/file.py'))
        assert report.total_prompts == 0

    def test_empty_directory(self, tmp_path):
        reports = lint_directory(tmp_path)
        assert len(reports) == 0

    def test_file_with_no_prompts(self, tmp_path):
        """A .py file with no string constants should yield no results."""
        test_file = tmp_path / 'no_prompts.py'
        test_file.write_text('x = 42\ny = "short"\n', encoding='utf-8')
        report = lint_file(test_file)
        assert report.total_prompts == 0
