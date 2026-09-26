---
name: aidd-grill
description: Relentless Socratic interview protocol to resolve assumptions, trade-offs, and invariants before writing code.
---

# AIDD-Grill — Pre-Code Socratic Protocol

Execute this skill BEFORE modifying code, designing features, or starting major refactors. Eliminates implicit assumptions, vibe coding, and cascade rework.

## Execution Rules

1. **Rounds, Not Single Questions:** Each round asks the whole frontier: every open question whose prerequisites are already decided. Number the questions (1, 2, 3...) so the user can answer by number. Questions still blocked by an open decision wait for a later round.
2. **Recommended Answer per Question:** Every question carries a recommended answer and one-line reason (e.g., "Recommended: A, because X"). The user may just reply "ok" to accept.
3. **Facts vs Decisions:** Facts are the agent's job: read code, docs, configs, and git history before asking; never ask the user what the repository already answers. Decisions are the user's job: trade-offs, priorities, scope, naming.
4. **Exhaust Decision Branches:**
   - Critical edge cases and boundary conditions.
   - Failure behavior: null, invalid, or concurrent inputs.
   - Core data invariants that must never be violated.
   - Blast radius and unwanted coupling with other modules.
5. **Headless / Autonomous Fallback:** When executed in non-interactive batch pipelines (e.g., `aidd-generator` phases), synthesize default architectural assumptions into a structured `### Consolidated Assumptions` block, one numbered item per open question, each written as `Recommended: <answer>, because <reason>` (never a bare decision), and proceed deterministically.
6. **Completion Gate:** Done only when the frontier is empty and the user confirms alignment. Then hand off execution to `/aidd-spec`.

## Encadeamento Canônico de Intake
Após concluir a entrevista socrática, avance deterministicamente para a próxima etapa:
- **Próxima Skill:** `/aidd-spec` (sintetiza decisões e invariantes em especificação técnica com critérios binários).
- **Fluxo Geral:** `/aidd-grill` ➔ `/aidd-spec` ➔ `/aidd-planner` ➔ `/aidd-dispatch-runner`.

