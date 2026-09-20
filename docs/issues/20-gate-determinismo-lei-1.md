---
id: ISSUE-0020
title: Gate de determinismo para a Lei #1 (bloqueia LLM em pipeline mecânico)
status: closed
blocked_by: []
created: 2026-09-20
source: BACKLOG-LEIS-SEM-GATE.md item 2.1 — enforcement gap analysis
---

# ISSUE-0020 — Gate de determinismo para a Lei #1

**Deliver:** Law #1 stops being convention-only. A static check blocks LLM SDK
calls inside code paths declared mechanical (`gates/`, deterministic pipeline
scripts), instead of trusting whoever writes them to remember the law.

**Blocked by:** nothing. Start now.

## Known limit (state it, do not hide it)

No static analyzer can classify "mechanical" vs "cognitive" LLM usage in
general — that judgment is semantic. This gate covers a narrower, real subset:
known LLM SDK imports/calls (`anthropic`, `openai`, `google.generativeai`, …)
appearing inside `gates/*.py` or any file tagged deterministic-only in its own
manifest. Full coverage stays human-review territory; say so in the gate's
own output, per Law #8.

## Scope

1. Enumerate SDK import patterns that count as "LLM call" — reuse detection
   already built for `G_LLM_PROMPT_SHIELD.py` where possible.
2. Build `gates/G_DETERMINISMO_MECANICO.py`: AST scan of `gates/` (and any
   directory a manifest marks deterministic-only) for those imports/calls;
   exit 1 on any hit.
3. Exceptions only via a documented, version-controlled list — never a
   silent skip.

## Acceptance criteria

- [x] Gate scans `gates/` and any declared deterministic-only path; exits 1
      on LLM SDK usage found there.
- [x] Own failing-path test: inject a synthetic file importing an LLM SDK
      into `gates/`, assert exit 1.
- [x] False-positive check: a normal deterministic gate file passes (exit 0).
- [x] Gate's stated limit (semantic classification out of scope) is printed
      in its own output, not just in this ticket.
- [x] Law #1 in `AGENTS.md` updated from `sem-gate` to name this gate, per
      ISSUE-0010 convention.
- [x] `BACKLOG-LEIS-SEM-GATE.md` row for Lei #1 updated to reflect coverage
      and its stated limit.
