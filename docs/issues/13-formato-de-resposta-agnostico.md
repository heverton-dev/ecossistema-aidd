---
id: ISSUE-0013
title: Formato de resposta obrigatório, cobrado em todo harness
status: ready-for-agent
blocked_by: []
created: 2026-09-19
source: user directive 2026-09-19 — chat output discipline
---

# ISSUE-0013 — Formato de resposta obrigatório em todo harness

**Deliver:** every harness answers in the same shape. The rule lives in `AGENTS.md`
and is enforced by a hook present in all of them — not only Claude.

**Blocked by:** nothing. Start now.

## Verified this session

- Rule 10 (plain language, no unexplained jargon) already lives in `AGENTS.md` and
  is enforced by `.claude/hooks/regra10_check.py`. Working template, reuse it.
- **That hook exists only for Claude.** Cursor, Gemini, opencode, mimocode, qoder
  carry no equivalent. The rule is written everywhere and enforced in one place.
- Same structural defect chased all week: rule without executable enforcement.

## The format to encode

1. **One top sentence** stating what to do or what happened. No preamble.
2. **Short body, bulleted.** Facts, numbers, findings. No narration of steps taken.
3. **One closing suggestion block.** What comes next, separated from the body.

Forbidden: introductions, restating the request, recapping what was just said,
listing options without a recommendation.

Shape is deterministically checkable — top sentence present, bullets present, closing
block present — so this needs no LLM, per Law #1.

## Acceptance criteria

- [ ] Format rule written into `AGENTS.md` alongside Rule 10, in compact English per Law #4.
- [ ] Hook extended to check shape, not only jargon. Deterministic, zero LLM.
- [ ] Hook replicated into every harness that supports hooks: Cursor, Gemini, opencode, mimocode, qoder, codebuddy. Harnesses without hook support get the rule in their pointer file plus an explicit note in the backlog that enforcement is unavailable there.
- [ ] Failing-path test per Law #13, strict reading: the test **executes** the hook against a prolix answer and asserts it blocks. Pattern presence does not count.
- [ ] Law #4 in `AGENTS.md` names this hook, per ISSUE-0010 convention.
- [ ] Harnesses that cannot enforce it are listed in `docs/protocolos/BACKLOG-LEIS-SEM-GATE.md`, never silently assumed covered.
