# AIDD Enterprise — Canonical Agent Directives & Mission-Critical Rules

> **Tool:** `aidd-enterprise`  
> **Role:** Regulated, Mission-Critical Platform with SHA-256 Validated Component Injection & Zero-Trust Architecture.  
> **Governance Standard:** Zero Stubs, Strict Isolation, Deterministic Multi-Harness Sync.

---

## 1. Core Execution Constraints

- **Thinking constraint:** Think strictly in compact English. Focus on SHA-256 integrity, zero-trust enforcement, and transaction boundaries. Under 150 words.
- **Execution limit:** Resolve tasks in 3 to 5 discrete steps. Stop and request confirmation if exceeding 5 steps.
- **Output format:** Silent executor. Return code edits and 1-line execution status only. Do not dump file contents in chat.
- **Bash rule:** Always pipe verbose commands to tail/grep. E.g., `pytest tests/ 2>&1 | tail -n 25`.
- **Editing rule:** Use exact search/replace block edits (`replace_file_content`).

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
