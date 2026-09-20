---
id: ISSUE-0016
title: Portão de Skill Rot (skills apontando para o que não existe mais)
status: ready-for-agent
blocked_by: []
created: 2026-09-19
source: docs/melhorias/19-09-2026_melhoria-taxonomia-prevencao-rot-ecossistema.md — category 8
---

# ISSUE-0016 — Portão de Skill Rot

**Deliver:** a skill whose instructions point at a renamed script, a moved path or a
changed flag is caught at commit instead of failing mid-flow.

**Blocked by:** nothing. Start now.

## Why this one is genuinely new — and would have caught a real case

Checked against all 27 existing gates: none validates the paths and commands written
inside `SKILL.md` bodies.

**Proven case it would have caught:** the `sandeco-token-reduce` skill (ISSUE-0008).
Its middleware checks for `llmlingua` in the main Python interpreter while the library
lives in the skill's own isolated environment. The check always fails, the flow always
falls back to truncation, and nothing reported it. A gate validating that a skill's
declared entry point is actually reachable would have flagged it.

## Scope

Static validation of every relative and absolute path, script reference and CLI
command appearing in `SKILL.md` files across all harness copies. Exit 1 on any
reference that does not resolve.

**Scope caution:** skills are replicated across `.claude/`, `.cursor/`, `.gemini/`,
`.opencode/`, `.mimocode/`, `.agents/` and `componentes/compartilhado/skills/`. Decide
whether the gate treats the shared copy as source of truth and the rest as mirrors, or
validates each independently. Getting this wrong produces six duplicate failures per
real defect.

## Acceptance criteria

- [ ] Every path, script and command referenced in `SKILL.md` bodies is resolved; exit 1 on any that does not.
- [ ] Mirror strategy decided and documented; one real defect produces one reported failure, not six.
- [ ] Run against the current repo; the resulting list is triaged individually, not bulk-suppressed.
- [ ] The `sandeco-token-reduce` case is used as the regression fixture — if the gate does not flag it, the gate is insufficient.
- [ ] Failing-path test, strict Law #13: rename a referenced script, execute the gate, assert exit 1.
- [ ] Declared against its law in `AGENTS.md`, per ISSUE-0010 convention.
