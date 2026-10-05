---
name: aidd-tdd
description: Strict TDD with agreed seams, Red-Green loop, refactor at review, zero stubs. Use when implementing test first, or "tdd".
---

# AIDD-TDD — Polyglot Test-Driven Development

Strict Test-Driven Development protocol for building and evolving production features in the AIDD ecosystem.

## Core Invariant: Zero Stubs / Zero Empty Mocks
Empty stubs (`pass`, `throw NotImplementedError`, `// TODO`) and trivial assertions (`assert True`) are strictly prohibited. Tests must assert real runtime behavior against concrete, typed interfaces.

## 0. Agree Test Seams (before the first test)
- List the public seams to test: entry points, public functions, CLI commands, HTTP routes. Never private helpers.
- For each seam, state the observable behavior to assert.
- Show the list to the user and confirm it before writing any test. No agreed seam = stop and report it as a finding.

## Execution Loop: Red → Green
One test, then one implementation, at a time. Never write a batch of tests first and the code later.

### 1. Red (Failing Test)
- Write one test specifying one behavior on an agreed seam.
- Execute the stack test runner (e.g., `pytest`, `cargo test`, `go test`, `vitest`).
- **Verify Expected Failure:** The test MUST fail specifically due to missing functionality or an unsatisfied assertion, never due to syntax or environmental errors.

### 2. Green (Minimal Working Implementation)
- Write only the minimum amount of functional code required to make the test pass.
- Re-run the test suite.
- **Verify Success:** The test MUST pass with exit code 0.

Repeat Red → Green for the next behavior.

## Refactor at Review (outside the loop)
Refactor belongs to the review stage, after all behaviors are green: clean up duplication, enforce idiomatic patterns, verify complete type annotations, then re-run the entire suite to guarantee zero regression.

## Anti-Patterns (forbidden)
- **Tautological test:** asserts what the code computes by computing it the same way. The expected value comes from an independent source (spec, hand-computed example, known fixture), never from the code under test.
- **Implementation-coupled test:** asserts internal calls, private state, or call order instead of observable behavior; breaks on a harmless refactor.
- **Horizontal slicing:** all tests first, then all code (or one layer at a time). Each Red → Green pair covers one vertical behavior end to end.

## Negative Guardrails

- NEVER start without `python ecossistema.py tdd iniciar --alvo <file> --seam <seam>` on a seam the user confirmed in step 0.
- NEVER write production code before a Red run that exits non-zero on an unmet assertion; an ImportError, SyntaxError or collection error is not Red (rule of `scripts/motor_tdd.py` `analisar_resultado_red`).
- NEVER run `tdd red` or `tdd green` for a test you did not execute in this loop: those subcommands only write the step into `sessao.json`, they do not run the test, so the exit code you captured is the only proof.
- NEVER leave `pass`, `NotImplementedError`, `assert True`, a skip marker or a mock of the seam under test; a skipped test is not green.
- NEVER declare a behavior done without the red-then-green pair, and never commit with `git commit --no-verify` to get past a red suite.

## Failure Modes & Fallback

- **Red for the wrong reason** (import, fixture, syntax): fix the test harness and re-run; stay in RED, the attempt does not count.
- **Test passes on its first run:** the behavior already exists or the test is tautological. Rewrite the expected value from the spec or a hand-computed example before any code.
- **Runner unsupported** (`executar_runner` returns "não suportado"): run the stack runner below directly, capture its exit code to a file and record it with `tdd red` / `tdd green`.
- **No public seam to hook into:** stop and report "no test seam" to the user as a finding; do not test private helpers.

## Stopping Checklist

- [ ] Red captured before code: `pytest -v <test> > red.log 2>&1; echo $? > red.exit` gives non-zero for an assertion.
- [ ] Green captured after code: `pytest -v <test> > green.log 2>&1; echo $? > green.exit` gives 0.
- [ ] `python ecossistema.py tdd status --sessao <sessao.json> > status.txt` shows RED then GREEN for every test.
- [ ] Whole suite after refactor: `pytest > suite.log 2>&1; echo $? > suite.exit` gives 0.
- [ ] No stubs: `grep -rnE "assert True|NotImplementedError|^\s*pass$" <test-files> > stubs.txt; echo $? > stubs.exit` gives 1.

## Supported Test Runners
- **Python:** `pytest -v <test_path>`
- **Node / TypeScript:** `npx vitest run <test_path>` or `npm test`
- **Go:** `go test -v ./...`
- **Rust:** `cargo test`
