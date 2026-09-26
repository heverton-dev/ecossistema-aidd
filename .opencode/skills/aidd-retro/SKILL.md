---
name: aidd-retro
description: Retrospective on a coding session. Turns each agent mistake into a proposed gate (mechanical) or review rule (judgement). Use when the user asks for a retro or post-mortem of a session.
---

# AIDD-Retro — Session Retrospective

Suggest improvements to the agent's **environment** (checks, pointers, rules, tooling) so future runs go better. Propose only: this skill never edits files. Applying a proposal goes through `aidd-melhoria` with user approval.

Adapted from `retro` in mattpocock/skills (commit c55ee46), MIT license.

## Steps

1. **Style guide:** load the `aidd-escrita-agentes` skill before drafting any proposal. Done when it is in context.
2. **Read the session log:** default to the current session. If the user names another session, read its log by path (Claude Code keeps logs as JSONL under the user's projects folder; other harnesses keep their own). Read the primary source, not a summary. Done when every tool error, retry, user correction, and skipped gate in the log is listed.
3. **Find candidates** in the seven categories below. Done when every listed event is mapped to a category or marked "no environment fix".
4. **Classify each candidate:**
   - **Mechanical** (fixed pattern, banned API, import shape, file location, missing exit-code check) → propose a deterministic gate in `gates/` (new `G_*.py` + test that proves it fails with exit 1). Default to the gate over a written rule.
   - **Judgement** (cross-file consistency, "matches surrounding style") → propose a review rule for the review stage (`review-changes`), not an always-loaded instruction.
5. **Present** the list to the user in order of severity (worst first). Each item: evidence from the log (quote + position), category, mechanical/judgement, proposed change, target file.
6. **Hand off:** approved items go to `aidd-melhoria` as the change request. Done when the user has approved or rejected each item.

## Categories

- **Navigation:** how hard was finding the right files? Hidden dependencies between files? Would a navigation pointer help? _Use when_ finding information took long.
- **Automated checks:** could a check have caught the mistake? Read existing gates and `.pre-commit-config.yaml` first: a check that exists but is unwired or silently broken is the finding, not a reinvention. No guardrail at all is itself a finding. _Use when_ the agent made a mistake a check could catch.
- **Coding standards:** should the reviewer get a new rule, or an existing rule be removed or clarified? Classify mechanical vs judgement (step 4). _Use when_ review missed a mistake.
- **AGENTS.md / global instructions:** steering that belongs in a gate or a review rule instead? _Use when_ `AGENTS.md` (repo or global scope) is large.
- **Tool economy:** expensive tool calls that could be streamlined? Token-hungry CLI or MCP? _Use when_ a tool call was expensive.
- **No-ops:** steering lines that do not change behaviour versus the default. _Use when_ steering files are large.
- **Information access:** crucial information the agent could not reach (server logs, read-only third-party access). _Use when_ the agent lacked a key fact.

## Reference: Implementation vs Review
- Implementation agent carries the most context pressure (explore, write, debug).
- Review agent receives a diff; least pressure. Coding standards belong to review, not to always-loaded files.
- `AGENTS.md` / `CLAUDE.md` load every turn: keep them to navigation pointers.
