---
id: ISSUE-0008
title: Compressor de prosa (skill sandeco) — ligar de verdade ou remover
status: closed
blocked_by: []
created: 2026-09-19
resolved: 2026-09-20
source: open-decision sweep 2026-09-19 / PLAN-0015 item 5, PLAN-0018
---

# ISSUE-0008 — Compressor de prosa (skill sandeco): ligar ou remover

**Deliver:** either the project really saves tokens by compressing prose, or it
stops carrying a heavy dependency that currently does nothing at all.

**Resolution:** Route B executed. Skill `sandeco-token-reduce`, `compressor_middleware.py`, seus testes e manifestos foram removidos. Alegação irreal em PLAN-0015 retificada e item de pinning em PLAN-0018 encerrado por remoção.

## Verified this session

Original intent: before sending long descriptive text to the model, shrink it
without losing meaning. Prose only — never code, schema or file paths.

**This never happens today.** Three independent checks:

1. **Nothing calls it.** The compression function appears in exactly two files in
   the whole repo: itself and its test. Zero pipeline usage.
2. **If called, it would switch itself off.** The code checks whether `llmlingua` is
   importable — but checks in the main Python, where it is not installed (confirmed:
   ModuleNotFoundError). The skill carries its own isolated environment holding
   `llmlingua 0.2.2` and `anthropic 1.5.0`, and the code never looks there. Right key,
   wrong pocket: the check always fails and the flow falls back to truncating with
   an ellipsis.
3. Therefore the token saving PLAN-0015 item 5 records as delivered **is not
   happening in production**.

## Knock-on effect

PLAN-0018 records as "next open item" pinning `llmlingua` and `anthropic` with
hashes, since they are installed unpinned. **That item depends entirely on this
one.** Pinning a library that may be deleted is painting a wall that may be
demolished. If the route is removal, that item dies with it.

## Two routes

- **Route A — wire it up.** Make the code use the skill's isolated environment (or
  install the library in the main one), call compression at the long-prose points of
  the pipeline, and prove it with real measurement: size before, size after, rate
  achieved. Then pin the versions with hashes.
- **Route B — remove.** Delete the compression code, its test, the skill, and its
  entries in the dependency manifest. Correct PLAN-0015 item 5, which currently
  claims a saving that does not exist. Close the PLAN-0018 pinning item as resolved
  by removal.

## Acceptance criteria

- [x] Route chosen and justified (Rota B escolhida pelo comitê).
- [ ] Route A: N/A (Rota B executada).
- [ ] Route A: N/A.
- [x] Route B: skill, code, test and manifest entries removed; full suite and `dependencia verify` still pass.
- [x] Either route: PLAN-0015 item 5 stops recording an unrealised saving.
- [x] PLAN-0018 pinning item closed with this decision's outcome.
