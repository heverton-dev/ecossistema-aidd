---
name: aidd-grill
description: Relentless Socratic interview protocol to resolve assumptions, trade-offs, and invariants before writing code.
---

# AIDD-Grill — Pre-Code Socratic Protocol

Execute this skill BEFORE modifying code, designing features, or starting major refactors. Eliminates implicit assumptions, vibe coding, and cascade rework.

## Execution Rules

1. **One Question at a Time:** Never overwhelm the user with question dumps. Target the highest-risk ambiguity or architectural branching point first.
2. **Exhaust Decision Branches:**
   - Critical edge cases and boundary conditions.
   - Failure behavior: null, invalid, or concurrent inputs.
   - Core data invariants that must never be violated.
   - Blast radius and unwanted coupling with other modules.
3. **Structured Options:** Provide concise, opinionated options (e.g., "Option A vs Option B; recommend A because of X").
4. **Headless / Autonomous Fallback:** When executed in non-interactive batch pipelines (e.g., `aidd-generator` phases), synthesize default architectural assumptions into a structured `### Consolidated Assumptions` block and proceed deterministically.
5. **Completion Gate:** Once critical decision branches are resolved, declare alignment and hand off execution to `/aidd-spec`.

## Encadeamento Canônico de Intake
Após concluir a entrevista socrática, avance deterministicamente para a próxima etapa:
- **Próxima Skill:** `/aidd-spec` (sintetiza decisões e invariantes em especificação técnica com critérios binários).
- **Fluxo Geral:** `/aidd-grill` ➔ `/aidd-spec` ➔ `/aidd-planner` ➔ `/aidd-dispatch-runner`.

