---
id: ISSUE-MESO-0008
title: Skill Canônica Multi-Harness aidd-dispatch-runner e Encadeamento de Intake
status: done
blocked_by: [ISSUE-MESO-0007]
created: 2026-09-21
source: Relatório de Melhoria 21-09-2026 — Meso-Camada da Tríade Canônica
---

# ISSUE-MESO-0008 — Skill Canônica Multi-Harness aidd-dispatch-runner e Encadeamento de Intake

**Deliver:** Multi-harness canonical skill `componentes/compartilhado/skills/aidd-dispatch-runner/` synchronized across all 7 harnesses, and updated intake skills documentation.

**Blocked by:** `ISSUE-MESO-0007`

## Scope

1. Create `componentes/compartilhado/skills/aidd-dispatch-runner/SKILL.md`:
   - YAML frontmatter with `name: aidd-dispatch-runner`, description and invocation triggers (`/dispatch`, `dispatch`, `/aidd-dispatch`).
   - Detailed instructions for taking a `PLANNER.json`, running the dispatch pipeline in Git Worktrees, checking Quality Gates, and reporting results.
2. Update intake skills documentation:
   - `componentes/compartilhado/skills/aidd-grill/SKILL.md`: explicit handoff section guiding developer from Socratic interview directly to `/aidd-spec`.
   - `componentes/compartilhado/skills/aidd-spec/SKILL.md`: explicit handoff to `/aidd-planner`.
   - `componentes/compartilhado/skills/aidd-planner-runner/SKILL.md`: explicit handoff to `/aidd-dispatch-runner`.
3. Synchronize skills across all 7 harnesses using:
   - `python ecossistema.py components sync --tipo skills`
4. Update `AGENTS.md` and `GEMINI.md` registering the new canonical Meso-Layer flow.

## Acceptance criteria

- [ ] Skill `aidd-dispatch-runner` exists in `componentes/compartilhado/skills/` and is synchronized to `.agents`, `.claude`, `.gemini`, `.cursor`, `.windsurf`, `.cline`, `.trae`.
- [ ] `python ecossistema.py components verify --tipo skills` passes with 0 errors.
- [ ] Documentation chain `grill` ➔ `spec` ➔ `planner` ➔ `dispatch` ➔ `master` is completely cross-linked.
