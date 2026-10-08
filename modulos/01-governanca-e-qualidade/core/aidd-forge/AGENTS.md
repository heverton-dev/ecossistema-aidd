# AIDD Forge — Canonical Agent Directives & Operational Rules

> **Tool:** `aidd-forge`  
> **Role:** Deterministic Environment Bootstrapping, Micro-Environment Isolation, Phase Slicing & Context Purging.  
> **Governance Standard:** Zero Stubs, Result Monad, Deterministic Injection, Cross-Harness Sync.

---

## 1. Core Execution Constraints

- Root `AGENTS.md` §1 governs execution (compact thinking, 3-5 steps, silent executor, piped bash, exact edits).
- Tool focus: injection invariants, schema consistency, and rollback transactions.

---

## 2. Architectural Invariants & Laws

1. **Zero Stubs:** Forbidden to commit empty methods (`pass`), simulated returns, or mock facades in production code.
2. **Result Monad:** All operational routines and service boundaries must return `Result.ok(value)` or `Result.fail(error)`.
3. **Context-Purge Isolation:** Cognitive subagents receive only atomic task specs and terminate immediately after AST validation.
4. **Universal Injector:** `python -m aidd_forge.cli inject <type> <name>` materializes deterministic components (`skill`, `mcp`, `rule`, `spec`, `roteiro`) with atomic rollback via `materializador.py`.
5. **Deterministic Gates:** All code modifications must pass the 7 deterministic gates in `aidd_forge/templates/gates/`.

---

## 3. Command Dispatch

- `/forge [path]` or `/aidd-init`: Executes deterministic bootstrap via `python -m aidd_forge.cli init`.
- Natural Language: Intentions like *"prepare environment"*, *"harden rules"*, *"create skill X"* route directly to `forge inject` or `forge init`.
