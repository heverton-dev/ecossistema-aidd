---
id: ISSUE-0007
title: SagaOrchestrator — ligar ou remover
status: closed
blocked_by: []
created: 2026-09-19
resolved: 2026-09-20
source: open-decision sweep 2026-09-19 / PLAN-0025 item 10
---

# ISSUE-0007 — SagaOrchestrator: ligar ou remover

**Deliver:** a recorded decision on a class that exists, is tested, and is never
used — so it stops surfacing in every dead-code audit.

**Resolution:** Route A executed. `SagaOrchestrator` e `SagaStep` removidos de todas as ferramentas, templates, manifestos e testes unitários. Suítes passam e `G_DRIFT_NUCLEO_COMPARTILHADO` aprovado.

## Verified this session

`SagaOrchestrator` solves a real problem: undo a multi-step operation when a late
step fails. Travel-booking pattern — flight fails, so cancel hotel and car in reverse.

Measured:

- Only instantiation: its own test (`tests/unit/test_cqrs_local_first.py`, both tools).
- **Absent** from the server-generating template — unlike `CircuitBreaker`, which is there.
- Byte-identical copy across `src/core/` and `templates/core/`.

Utility today: **zero**. Utility if wired: real, but only once a cross-slice
operation needing rollback exists. None does.

## Two routes

- **Route A — remove.** No multi-step operation in sight, so this is scaffolding
  left standing after the build. Drop from both tools, from template mirrors, and its test.
- **Route B — keep as library.** Concrete intent to use it exists, so keep it, but
  record where and when it gets wired — otherwise it returns in the next audit.

Unlike ISSUE-0006, **no broken documentation promise here** — the architecture doc
never sells distributed transaction management. Far less urgent.

## Acceptance criteria

- [x] Route chosen and justified in PLAN-0025 item 10 (Rota A escolhida pelo comitê).
- [x] Route A: class, mirrors and test removed; full suite still passes; master/enterprise drift gate still approves.
- [x] Route B: N/A (Rota A executada).
- [x] Dead-code inventory updated so this stops resurfacing.
