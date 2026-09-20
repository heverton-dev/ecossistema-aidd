---
id: ISSUE-0024
title: Gate raiz do Quarteto Sine Qua Non para a Lei #10
status: closed
closed: 2026-09-20
blocked_by: []
created: 2026-09-20
source: BACKLOG-LEIS-SEM-GATE.md item 2.6 — enforcement gap analysis
---

# ISSUE-0024 — Gate raiz do Quarteto Sine Qua Non para a Lei #10

**Deliver:** Law #10 stops being convention-only at the root level. A root
gate audits any generated project deliverable for the four mandatory
pillars (Swagger Studio `/docs`, Webhook Studio `/webhooks`, MCP Studio
`/mcp`, Guia `/docs/guia`) instead of relying only on the planner-local
check.

**Blocked by:** nothing. Start now.

## Scope

1. Read `tools/aidd-planner/scripts/gates/G_PLANNER_SINE_QUA_NON.py` in
   full; decide promote-in-place vs. wrap from root — record the decision
   and why.
2. Build/promote `gates/G_QUARTETO_SINE_QUA_NON.py`: given a generated
   project path, assert all four route groups resolve (via OpenAPI spec or
   live route registry).
3. Run it against real fixture output from each of the 3 canonical flows
   (pure, open, factory-derived), not only the planner's own test fixture.

## Acceptance criteria

- [x] Gate audits a generated project's routes for all 4 pillars; exits 1
      if any is missing.
- [x] Own failing-path test: fixture project missing one pillar (e.g. no
      `/mcp`), assert exit 1.
- [x] False-positive check: a complete fixture project with all 4 pillars
      passes.
- [x] Runs against at least one real deliverable from each of the 3
      canonical flows.
- [x] Law #10 in `AGENTS.md` updated from `sem-gate` to name this gate.
- [x] `BACKLOG-LEIS-SEM-GATE.md` row for Lei #10 updated.
