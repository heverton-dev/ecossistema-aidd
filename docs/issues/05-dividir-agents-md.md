---
id: ISSUE-0005
title: Dividir o AGENTS.md em nucleo obrigatorio e secoes sob demanda
status: ready-for-agent
blocked_by: [ISSUE-0001]
created: 2026-09-19
source: open-decision sweep 2026-09-19 / PLAN-0022 item 2
---

# ISSUE-0005 — Dividir o AGENTS.md em núcleo e seções sob demanda

**Deliver:** every session of every assistant loads only what is always needed,
fetching the rest on demand. Lower cost per session, no rule lost.

**Blocked by:** ISSUE-0001 — both touch the same file, and that one is small. Land
the small one first to avoid two efforts fighting over the same text (a failure
mode already recorded in this project when two sessions edit one folder).

## Verified this session

PLAN-0022 item 2 exists (created 2026-09-11) but its file is an unfilled template:
scope reads `[Descrever o que entra e o que nao entra]`, criteria read
`[Criterio 1 checavel]`. **The split is not designed yet** — this is a design task,
not an execution task.

Model it as an operations manual: the laminated sheet on the wall holds what is
consulted constantly; the binder in the drawer holds the rest. Today everything is
on the wall.

Design decision to make here: what is core (inviolable laws, canonical flow, commit
rules) versus what becomes on-demand (per-tool reference detail, decision history,
long tables).

## Acceptance criteria

- [ ] PLAN-0022 item 2 scope is genuinely filled in, with the proposed split and a reason per section leaving the core.
- [ ] Core still holds every inviolable law — no governance rule becomes on-demand.
- [ ] A real on-demand loading mechanism exists (not a file cut in half that nobody knows how to fetch).
- [ ] Core size reduction measured in numbers, before and after.
- [ ] Pointer files for the other assistants (CLAUDE.md, GEMINI.md, QODER.md, CODEBUDDY.md) still resolve correctly.
