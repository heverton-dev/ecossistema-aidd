---
id: ISSUE-0017
title: Portão de Migration Rot (migrações que não voltam atrás)
status: completed
blocked_by: []
created: 2026-09-19
source: docs/melhorias/19-09-2026_melhoria-taxonomia-prevencao-rot-ecossistema.md — category 9
---

# ISSUE-0017 — Portão de Migration Rot

**Deliver:** a migration that is not idempotent, has no rollback, or leaves the
schema diverging from what the migrations declare, is blocked before it reaches a
real database.

**Blocked by:** nothing. Start now.

## Why this one is genuinely new

Checked against all 27 existing gates: `G_TRANSACTION_LOG_LRU` and
`G_ESCRITOR_ATOMICO` cover runtime write integrity. None exercises the migration
sequence.

Law at stake: #3, Structured Persistence.

## Scope

Apply every migration up, then down, against an ephemeral in-memory database on each
build. Assert convergence to the declared final schema. Exit 1 on divergence, missing
rollback, or non-idempotent re-application.

**Scope decision to make first:** the ecosystem generates projects targeting both
SQLite WAL and PostgreSQL. Decide whether the gate runs both engines or only the
default, and state the limit rather than implying both are covered.

## Acceptance criteria

- [x] Migrations applied up and down in an ephemeral database per run; no real database touched.
- [x] Final schema compared against the declared schema; exit 1 on divergence.
- [x] Re-applying a migration is proven idempotent, not assumed.
- [x] Missing rollback scripts cause exit 1.
- [x] Engine coverage stated explicitly. If only one engine is exercised, output says so (Law #8).
- [x] Failing-path test, strict Law #13: remove a rollback, execute the gate, assert exit 1.
- [x] Declared against Law #3 in `AGENTS.md`, per ISSUE-0010 convention.
