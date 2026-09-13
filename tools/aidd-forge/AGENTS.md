# AIDD Forge — Canonical Agent Directives & Operational Rules

> **Tool:** `aidd-forge`  
> **Role:** Deterministic Environment Bootstrapping, Micro-Environment Isolation, Phase Slicing & Context Purging.  
> **Governance Standard:** Zero Stubs, Result Monad, Deterministic Injection, Cross-Harness Sync.

---

## 1. Core Execution Constraints

- **Thinking constraint:** Think strictly in compact English. Focus on injection invariants, schema consistency, and rollback transactions. Under 150 words.
- **Execution limit:** Resolve tasks in 3 to 5 discrete steps. Stop and request user confirmation if more steps are required.
- **Output format:** Silent executor. Return code edits and 1-line execution status only. Do not repeat generated files in chat.
- **Bash rule:** Always pipe verbose commands to tail/grep. E.g., `pytest tests/ 2>&1 | tail -n 25`. Never dump raw file trees or lockfiles.
- **Editing rule:** Use exact search/replace block edits (`replace_file_content`).

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
