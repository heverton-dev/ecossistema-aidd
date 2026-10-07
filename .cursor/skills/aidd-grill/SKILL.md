---
name: aidd-grill
description: Socratic interview that resolves assumptions, trade-offs and invariants before code. Use when requirements are open, or "grill".
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
5. **Headless / Autonomous Fallback:** When executed in non-interactive batch pipelines (e.g., `aidd-pure` phases), synthesize default architectural assumptions into a structured `### Consolidated Assumptions` block, one numbered item per open question, each written as `Recommended: <answer>, because <reason>` (never a bare decision), and proceed deterministically.
6. **Completion Gate:** Done only when the frontier is empty and the user confirms alignment. Then hand off execution to `/aidd-spec`.

## Encadeamento Canônico de Intake
Após concluir a entrevista socrática, avance deterministicamente para a próxima etapa:
- **Próxima Skill:** `/aidd-spec` (sintetiza decisões e invariantes em especificação técnica com critérios binários).
- **Fluxo Geral:** `/aidd-grill` ➔ `/aidd-spec` ➔ `/aidd-planner` ➔ `/aidd-dispatch`.

## Negative Guardrails

- NEVER ask the user a fact the repo answers (code, `AGENTS.md`, git log); read first, ask only decisions.
- NEVER treat silence as approval in interactive mode, and never write "the user chose X" unless the user wrote it in this session (a fabricated decision is a known incident here).
- NEVER write a bare decision in `### Consolidated Assumptions`; each item is `Recommended: <answer>, because <reason>`, or `cli.py validar` and `modulos/01-governanca-e-qualidade/gates/G_PROVA_SKILLS_POCOCK.py` reprove it.
- NEVER start coding or jump to `/aidd-spec` while the frontier still has open questions.
- NEVER propose configuring an LLM API key to run the interview; the model is always the running harness.

## Failure Modes & Fallback

- **User silent, or headless run:** write the `### Consolidated Assumptions` block, then run `python componentes/compartilhado/skills/aidd-grill/scripts/cli.py consolidar --arquivo <round.md> --headless`.
- **`[FALHA] Validação estrutural rejeitou a rodada`:** renumber questions 1..N and give each one `Recommended:` line, rerun `validar`.
- **An answer contradicts an earlier decision:** stop the round, quote both answers by number, ask which one wins.

## Stopping Checklist

Exit codes go to a file, never through a pipe: `<cmd> > "$TEMP/grill.log" 2>&1; echo $? > "$TEMP/grill.rc"`.

- [ ] `python componentes/compartilhado/skills/aidd-grill/scripts/cli.py validar --arquivo <round.md>` wrote rc 0.
- [ ] Frontier empty: no numbered question left without an answer or a `Recommended:` default.
- [ ] User confirmed alignment (interactive), or the assumptions block exists (headless).
- [ ] `python modulos/01-governanca-e-qualidade/gates/G_PROVA_SKILLS_POCOCK.py --artefatos <dir> --skill aidd-grill` wrote rc 0 when this skill's text changed.
