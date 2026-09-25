---
name: aidd-escrita-agentes
description: Writing documents agents consume. Use when creating or editing a skill, or modifying AGENTS.md or CLAUDE.md.
---

# AIDD-Escrita-Agentes — Writing for Agents

Reference for any document an agent reads: a skill, `AGENTS.md`, `CLAUDE.md`, a doc reached by a pointer. Goal: **predictability** — agent takes the same process every run.

Adapted from `writing-for-agents` in mattpocock/skills (commit c55ee46), MIT license.

## Context Pointers
- **Context pointer** = line in context naming out-of-context material + condition to reach it. Skill description is one; an `AGENTS.md` line naming a doc is one.
- Wording decides when material is reached. Must-have target behind weak pointer = variance bug. Sharpen wording first; inline only if sharpening fails.
- Pointer states what the material is + lists its **branches** (distinct cases that should trigger it).
- Front-load the leading word. One trigger per branch; collapse synonyms. Cut identity the body already carries.

## Two Loads
- **Context load:** always-loaded material (`AGENTS.md` line, skill description) costs tokens and attention every turn.
- **Cognitive load:** human must know which docs exist and when. Spend it where human judgement matters.
- Material behind a pointer costs only the pointer line.

## Information Hierarchy
1. **In-file step:** ordered actions. Primary tier.
2. **In-file reference:** rules/facts consulted on demand. Flat peer-set is fine.
3. **Disclosed reference:** separate file behind a pointer, loaded only when it fires.
- Inline what every branch needs; disclose what only some branches reach.
- **Co-location:** keep a concept's definition, rules, caveats under one heading.
- **Sprawl:** document too long even when every line is live. Cure: disclose, split by branch or sequence.

## Steps and Completion Criterion
- Every step ends on a **completion criterion**: condition telling the agent the step is done.
- **Clarity:** vague bound ("understanding reached") invites premature completion. Sharpen the bound first; hide later steps (split across a real context boundary: hand-off or subagent) only if rush is observed.
- **Demand:** "every modified model accounted for" forces legwork; "produce a change list" does not.
- Strongest criteria: checkable and exhaustive.

## When to Split
- **By sequence:** later steps tempt rushing the current one → split.
- Merging sequences exposes later steps → invites premature completion.
- Every split spends a load; split only when the cut earns it.

## Leading Words
- **Leading word:** compact pretrained concept the agent thinks with (_tight_ loop, loop goes _red_). Repeat the token, never the sentence.
- Prefer an existing word over a coined one (coined words recruit no priors).
- Hunt restatements: a triad spelled at three sites → one word.

## Negation
- Prohibition drags the forbidden behaviour into context (_don't think of an elephant_).
- Prompt the positive target ("write one-line comments").
- Prohibition only as hard guardrail that has no positive phrasing; pair it with the positive target.

## Pruning
- **Single source of truth:** each meaning in one place; behaviour change = one-place edit. Duplication inflates prominence and costs tokens.
- **Environment is a source too** (`requirements.txt`, configs, directory layout, `--help`). Restating it = cache that goes stale. Cache only what lookup cannot find: unwritten convention, reason behind a choice, gotcha.
- **Relevance:** every line must still bear on the task. Without pruning → **sediment**: stale layers kept because adding feels safe and removing feels risky.
- **No-op:** instruction the model already obeys by default. Test: does it change behaviour versus default? Settle by running the document, not debate. Delete the whole sentence. Weak leading word (_be thorough_) = no-op; use stronger word (_relentless_).

## AIDD Checklist (before saving)
- [ ] Every always-loaded line passes the no-op test.
- [ ] Each rule lives in one file; others point to it.
- [ ] Each step has a checkable completion criterion.
- [ ] Positive phrasing; negation only as guardrail.
- [ ] Skill body under 150 lines; extra reference disclosed behind a pointer.
