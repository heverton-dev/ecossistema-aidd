---
name: aidd-tdd
description: Strict Test-Driven Development protocol (Red-Green-Refactor) with zero stubs and polyglot runtime support.
---

# AIDD-TDD — Polyglot Test-Driven Development

Strict Test-Driven Development protocol for building and evolving production features in the AIDD ecosystem.

## Core Invariant: Zero Stubs / Zero Empty Mocks
Empty stubs (`pass`, `throw NotImplementedError`, `// TODO`) and trivial assertions (`assert True`) are strictly prohibited. Tests must assert real runtime behavior against concrete, typed interfaces.

## 3-Step Execution Cycle

### 1. Red (Failing Test)
- Write the unit or integration test specifying desired behavior first.
- Execute the stack test runner (e.g., `pytest`, `cargo test`, `go test`, `vitest`).
- **Verify Expected Failure:** The test MUST fail specifically due to missing functionality or an unsatisfied assertion, never due to syntax or environmental errors.

### 2. Green (Minimal Working Implementation)
- Write only the minimum amount of functional code required to make the test pass.
- Re-run the test suite.
- **Verify Success:** The test MUST pass with exit code 0.

### 3. Refactor (Clean Code & Gate Compliance)
- Clean up duplication, enforce idiomatic patterns, and verify complete type annotations.
- Re-run the entire test suite to guarantee zero regression.

## Supported Test Runners
- **Python:** `pytest -v <test_path>`
- **Node / TypeScript:** `npx vitest run <test_path>` or `npm test`
- **Go:** `go test -v ./...`
- **Rust:** `cargo test`
