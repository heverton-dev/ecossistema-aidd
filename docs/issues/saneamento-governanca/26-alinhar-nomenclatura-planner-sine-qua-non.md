---
id: ISSUE-0026
title: Nomenclatura de pilares desatualizada no portão local do planner (Lei #10)
status: ready-for-agent
blocked_by: []
created: 2026-09-20
source: docs-audit 2026-09-20 — book/reference update pass, cross-check with ISSUE-0024
---

# ISSUE-0026 — Nomenclatura de pilares desatualizada no portão local do planner

**Deliver:** the planner's own Quarteto Sine Qua Non gate stops naming its first
and fourth pillar after a route scheme Law #10 replaced two sessions ago.

**Blocked by:** nothing. Start now.

## Verified this session

`tools/aidd-planner/gates/G_PLANNER_SINE_QUA_NON.py` still uses the pre-ISSUE-0001
pillar naming:

- Docstring lines 7-10 list the four pillars literally as `/swagger`, `/webhooks`,
  `/mcp`.
- `pilares = ["swagger", "webhooks", "mcp", "docs"]` (line ~56) names pillar 1
  `"swagger"` and pillar 4 `"docs"`.

Two problems, not one:

1. `AGENTS.md` Law #10 was corrected in Session 7 (ISSUE-0001) to name the four
   pillars `/docs`, `/webhooks`, `/mcp`, `/docs/guia` — every generated server
   serves `/docs`, none serve `/swagger` as primary. This gate's docstring still
   teaches the old names.
2. The internal key `"docs"` for pillar 4 collides in meaning with the real
   `/docs` route of pillar 1. A plan reader or a future maintainer skimming the
   dict sees `"docs"` and reasonably assumes it means the Swagger Studio pillar,
   not the User Guide pillar.

Contrast: the root gate built in Session 23 (`gates/G_QUARTETO_SINE_QUA_NON.py`,
ISSUE-0024) already treats `/docs` as canonical and accepts `/swagger` only as a
legacy-compatible route alias, with an unambiguous fourth-pillar key. This
planner-local gate was not reconciled against that convention when ISSUE-0024
was executed, even though that ticket's Definition of Done said "read
`tools/aidd-planner/scripts/gates/G_PLANNER_SINE_QUA_NON.py` in full first" — the
path named there was itself slightly off (the real file has no `scripts/`
segment: `tools/aidd-planner/gates/G_PLANNER_SINE_QUA_NON.py`).

## Two routes

- **Route A — rename.** Rename the internal pillar key `"docs"` (4th pillar) to
  something unambiguous (e.g. `"guia"`), update the docstring to name `/docs` as
  the canonical first-pillar route (keep `/swagger` only as a documented legacy
  alias, matching `gates/G_QUARTETO_SINE_QUA_NON.py`), and update every
  `PLANNER.json` fixture/schema that references the old key.
- **Route B — document as intentional.** If `"swagger"`/`"docs"` are internal
  JSON schema keys never meant to equal the literal route path, keep the keys and
  fix only the docstring/comments so they stop implying a literal route — record
  that decision here so it does not resurface as a false positive in a future
  audit.

## Acceptance criteria

- [x] Route chosen and justified (Rota A escolhida pelo usuário: renomeação da chave para 'guia' com rota '/docs' canônica e retrocompatibilidade para 'docs').
- [x] Route A: key renamed consistently across the gate, its test suite, and any
      `PLANNER.json` schema/fixture that names the 4th pillar `"docs"`; docstring
      corrected; full `aidd-planner` test suite still passes (13 passed).
- [ ] Route B: docstring/comments corrected only; this ticket records why the key
      names stay as-is.
- [x] Either route: `gates/G_QUARTETO_SINE_QUA_NON.py` and
      `tools/aidd-planner/gates/G_PLANNER_SINE_QUA_NON.py` describe the same 4
      pillars the same way, so a reader does not have to reconcile two
      vocabularies for one law.
- [x] Stop and ask before any commit.
