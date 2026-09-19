---
id: ISSUE-0012
title: Gate de idioma para a Lei #4 (inglês compacto no núcleo)
status: ready-for-agent
blocked_by: []
created: 2026-09-19
source: open-decision sweep 2026-09-19 — enforcement gap analysis
---

# ISSUE-0012 — Gate de idioma para a Lei #4

**Deliver:** Law #4 stops being unenforced. Agent-facing text written in PT-BR gets
blocked at commit, instead of depending on whoever writes it remembering the law.

**Blocked by:** nothing. Start now. Conceptually downstream of ISSUE-0010, which
reveals such gaps — but this gap is already confirmed, so no wait.

## Verified this session

Law #4 reads: *"Extreme Token Economy: Minimalist prompts, compact English core
rules, dense PT-BR user responses only when requested."*

No gate checks it. Grepped all 26 gates for any language check: zero hits.

Measured cost on this very ticket set: the 9 tickets first written in PT-BR prose
cost **6,730 tokens**; rewritten in telegraphic English, **4,826** — 28.3% cheaper.
Per ticket: 748 down to 536. Within a 100k budget that is 133 tickets versus 186 —
**40% more work fits one session window**.

## Scope

Deterministic detection, zero LLM — same shape as `G_HONESTIDADE_ROTULO`, which
already scans files for banned strings and serves as a working template.

Detection: PT-BR marker density above a threshold — accented-character ratio plus a
small closed list of structural words (`ção`, `não`, `que`, `para`, `são`, `está`).

**Define the scope list first; that is the hard part, not the detector.**
Agent-facing text must be English: ticket bodies, `SKILL.md` files, prompt
templates, gate output strings, `AGENTS.md` core. User-facing text stays PT-BR:
`title:` fields, `INDEX.md`, explanatory material under `docs/`, book, reports. Get
this list wrong and the gate is either useless or unbearable.

## Acceptance criteria

- [ ] Scope list written and agreed: which paths must be English, which stay PT-BR.
- [ ] Gate detects PT-BR prose in must-be-English paths, deterministically, no LLM call.
- [ ] Gate carries a failing-path test per ISSUE-0011: feed PT-BR prose into a must-be-English path, assert exit 1.
- [ ] Run against the current repo; resulting violations triaged individually, not bulk-suppressed.
- [ ] Law #4 in `AGENTS.md` names this gate, per ISSUE-0010.
- [ ] False-positive check against a PT-BR path that must NOT trigger (e.g. `INDEX.md`).
