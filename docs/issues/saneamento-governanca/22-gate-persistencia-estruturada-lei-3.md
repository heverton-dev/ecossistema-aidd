---
id: ISSUE-0022
title: Gate de persistência estruturada para a Lei #3
status: closed
blocked_by: []
created: 2026-09-20
source: BACKLOG-LEIS-SEM-GATE.md item 2.3 — enforcement gap analysis
---

# ISSUE-0022 — Gate de persistência estruturada para a Lei #3

**Deliver:** Law #3 stops being convention-only for known state-holding
tools. A gate validates that the JSON/SQLite persistence schemas declared by
orchestration tools (`flight_plan.json`, `.jsonl` logs, …) actually exist and
match their expected shape after a real run, catching state silently kept
only in process memory.

**Blocked by:** nothing. Start now.

## Known limit (state it, do not hide it)

Cannot prove a negative — "no script anywhere keeps state only in a
variable" — in general. Scope narrows to tools that already claim structured
persistence: verify the claim, don't invent global coverage. Say so in the
gate's own output, per Law #8.

## Scope

1. Inventory tools that claim JSON/SQLite persistence, starting from the
   `flight_plan.json` schema and existing `.jsonl` log writers.
2. Build `gates/G_ESTRUTURA_ESTADO.py`: for each inventoried tool, assert its
   persistence artifact exists and validates against a JSON Schema (or the
   SQLite table exists with expected columns) after a real run.
3. Keep the inventory list explicit inside the gate so additions require a
   deliberate edit, never silent drift.

## Acceptance criteria

- [x] Gate validates each inventoried tool's persistence artifact against
      its schema.
- [x] Own failing-path test: run a tool with its persistence write
      disabled/corrupted, assert exit 1.
- [x] False-positive check: a tool with valid persisted state passes.
- [x] Gate's own output states the inventory is a named list, not exhaustive
      coverage.
- [x] Law #3 in `AGENTS.md` updated from `sem-gate` to name this gate.
- [x] `BACKLOG-LEIS-SEM-GATE.md` row for Lei #3 updated.
