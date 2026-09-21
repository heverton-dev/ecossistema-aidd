---
id: ISSUE-0025
title: Gate de stack padrão-ouro para a Lei #11
status: closed
closed: 2026-09-20
blocked_by: []
created: 2026-09-20
source: BACKLOG-LEIS-SEM-GATE.md item 2.7 — enforcement gap analysis
---

# ISSUE-0025 — Gate de stack padrão-ouro para a Lei #11

**Deliver:** Law #11 stops being convention-only. A gate rejects a generated
project whose frontend isn't Next.js + TypeScript + Tailwind, or whose
backend isn't Python + SQLite WAL + OpenAPI 3.1, unless the plan/prompt
explicitly authorized a different stack for that layer.

**Blocked by:** nothing. Start now.

## Scope

1. Build `gates/G_STACK_FRONTEND_PADRAO.py`: parse the generated
   `package.json` / `tsconfig.json` / `tailwind.config.*`; assert Next.js,
   React, TypeScript, and Tailwind CSS present as declared deps.
2. Pair it with a backend check: assert SQLite `journal_mode=WAL` in the
   generated DB init code, and the OpenAPI spec declares version `3.1.x`.
3. Honor the explicit-override clause in Law #11 (`AGENTS.md` §2.11): the
   gate must pass when the plan/prompt recorded an explicit different-stack
   decision for that layer, and fail only on silent drift.

## Acceptance criteria

- [x] Gate flags a generated frontend missing Next.js/TypeScript/Tailwind
      when no explicit override was recorded.
- [x] Gate flags a backend without SQLite WAL or without OpenAPI 3.1.
- [x] Own failing-path test: fixture `package.json` without Tailwind,
      assert exit 1.
- [x] False-positive check: fixture with an explicit recorded override for
      that layer passes.
- [x] Runs against `proj_ctt`'s real generated output (the reference case
      named in Law #11) and confirms it passes.
- [x] Law #11 in `AGENTS.md` updated from `sem-gate` to name this gate.
- [x] `BACKLOG-LEIS-SEM-GATE.md` row for Lei #11 updated.
