# AIDD Master — Canonical Agent Directives & Slicing Rules

> **Tool:** `aidd-master`  
> **Role:** Modular Clean Architecture & Vertical Slice Platform (SQLite WAL, EventBus, Result Monad).  
> **Governance Standard:** Zero Stubs, Bounded Context Isolation, Deterministic Quality Gates.

---

## 1. Core Execution Constraints

- **Thinking constraint:** Think strictly in compact English. Focus on bounded context boundaries, EventBus decoupling, and WAL pragmas. Under 150 words.
- **Execution limit:** Resolve tasks in 3 to 5 discrete steps. Stop and request confirmation if more steps are required.
- **Output format:** Silent executor. Return code edits and 1-line execution status only. Do not repeat code in conversational reply.
- **Bash rule:** Always pipe verbose commands to tail/grep. E.g., `pytest tests/ 2>&1 | tail -n 25`.
- **Editing rule:** Use exact search/replace block edits (`replace_file_content`).

---

## 2. Architectural Invariants & Quality Gates

1. **Bounded Context Isolation & Vertical Slices (G_ARQUITETURA):** Direct imports between business modules are strictly forbidden (e.g. `import modules.erp` within `modules.crm`). Every module must be an autonomous vertical slice containing `router.py`, `service.py`, `repository.py`, `dtos.py`, and `events.py`. Frontends mirror this structure (`hooks/`, `components/`, `types.ts`, `page.tsx`).
2. **Dedicated Repositories & Data Isolation:** Cross-module SQL JOINs or hard foreign keys between bounded contexts are prohibited. Data access is strictly encapsulated in the module's `repository.py`. Cross-slice communication occurs exclusively via `EventBus` or public service interfaces.
3. **Result Monad (G_QUALIDADE):** All service methods in `services.py` must return `Result[T, E]` (`Result.ok()` or `Result.fail()`). Never leak raw exceptions to presentation layers.
4. **Safe Persistence (G_SEGURANCA):** SQLite databases must always operate in WAL mode (`PRAGMA journal_mode=WAL;`). All SQL queries must use placeholders (`?`). Zero string concatenation. Soft-delete only (`deletado_em IS NULL`).
5. **Zero Stubs:** Forbidden empty functions (`pass`) or placeholder `TODO`s in production modules.
6. **Observability (G_PERFORMANCE):** Service routines must be decorated with `@trace_span(name)` and respect SLA ceilings (`p99 < 200ms`).
7. **Engineering Skills Alignment:** Slices must be decomposed via `/aidd-tickets` (tracer bullets) and implemented under strict `/aidd-tdd` (Red-Green-Refactor) before module graduation.

---

## 3. Command Dispatch

- `/master <module>`: Scaffolds a new vertical slice via `python scripts/aidd.py add-module <module>`.
- `python scripts/aidd.py compose-orca <modules>`: Composes selected modules into an isolated deployment.
- `python scripts/run_all.py`: Runs all 10 deterministic gates.
