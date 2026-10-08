# AIDD Enterprise — Canonical Agent Directives & Mission-Critical Rules

> **Tool:** `aidd-enterprise`  
> **Role:** Regulated, Mission-Critical Platform with SHA-256 Validated Component Injection & Zero-Trust Architecture.  
> **Governance Standard:** Zero Stubs, Strict Isolation, Deterministic Multi-Harness Sync.

---

## 1. Core Execution Constraints

- Root `AGENTS.md` §1 governs execution (compact thinking, 3-5 steps, silent executor, piped bash, exact edits).
- Tool focus: SHA-256 integrity, zero-trust enforcement, and transaction boundaries.

---

## 2. Enterprise Invariants & Quality Gates

1. **Cryptographic Integrity:** Injected enterprise components are validated against SHA-256 signatures before being allowed into execution.
2. **Result Monad (G_QUALIDADE):** All business operations in `services.py` must return `Result[T, E]`. Raw exceptions are blocked at the perimeter.
3. **Strict Bounded Contexts (G_ARQUITETURA):** Zero cross-module direct imports. Decoupled integration exclusively via `EventBus` and `core.*`.
4. **Resilient Persistence (G_SEGURANCA):** SQLite WAL mode enforced (`PRAGMA journal_mode=WAL;`). Strict query parameterization. Zero raw SQL formatting. Soft-delete enforced.
5. **Zero Stubs:** All committed code must be 100% complete, strongly typed, and accompanied by automated tests.
6. **Engineering Skills Alignment:** Components must pass a strict `/aidd-tdd` cycle with 100% real assertion coverage before receiving SHA-256 cryptographic signatures.

---

## 3. Command Dispatch

- `/enterprise <type> <name>`: Injects regulated enterprise components via `python ecossistema.py enterprise inject <type> <name>`.
- `python scripts/run_all.py`: Validates all 10 local enterprise Quality Gates.
