---
name: aidd-tdd
description: Strict Test-Driven Development protocol (Red-Green loop, refactor at review) with agreed test seams, zero stubs and polyglot runtime support.
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

## Supported Test Runners
- **Python:** `pytest -v <test_path>`
- **Node / TypeScript:** `npx vitest run <test_path>` or `npm test`
- **Go:** `go test -v ./...`
- **Rust:** `cargo test`
