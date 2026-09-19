---
id: ISSUE-0010
title: Cada lei declara seu portão verificador (inventário + meta-gate)
status: ready-for-agent
blocked_by: []
created: 2026-09-19
source: open-decision sweep 2026-09-19 — enforcement gap analysis
---

# ISSUE-0010 — Cada lei declara seu portão verificador

**Deliver:** every inviolable law names the gate that enforces it — or states
explicitly that none exists. A meta-gate fails when any law lacks that declaration.
Silent absence becomes loud absence.

**Blocked by:** nothing. Start now.

## Verified this session

- `AGENTS.md` holds **12 laws**. The architecture doc says "11 Leis Invioláveis". Drift.
- **Only Law #12 names its verifier inline** (`G_DOCS_ROT.py`). The other 11 leave the
  link implicit or absent.
- **Law #4 (compact English core rules) has no gate at all.** Grepped all 26 gates for
  any language check: zero hits. That absence is why it was violated with no friction
  when these very tickets were first written in PT-BR.

## Scope

For each of the 12 laws, append one declaration line: the enforcing gate, or the
explicit string `sem gate — cumprimento por convenção`. Then a meta-gate that parses
the law list and exits 1 on any law missing the declaration.

**Also record enforcement strength per law**, not just presence. Three states:

- `provado` — a gate exists AND a test proves it fails when the guarded thing breaks.
- `nao-provado` — a gate exists, but nothing proves it bites (see ISSUE-0011).
- `sem-gate` — no gate; honest gap.

Without that third column this ticket produces a false sense of coverage: a law can
point at a facade gate (see ISSUE-0009, where `G_ZERO_HEADLESS` greps for a string
and declares victory). The map must show which extinguishers were actually test-fired.

## Acceptance criteria

- [ ] All 12 laws carry a declaration line naming gate or explicit absence.
- [ ] Each declaration carries enforcement strength: `provado`, `nao-provado`, `sem-gate`.
- [ ] Meta-gate exists, parses the law list, exits 1 on any missing declaration.
- [ ] Meta-gate has its own failing-path test (ISSUE-0011 rule applies to it too).
- [ ] Law count corrected in the architecture doc and book: 12, not 11.
- [ ] The resulting `sem-gate` list is written down as a backlog, not silently accepted.
