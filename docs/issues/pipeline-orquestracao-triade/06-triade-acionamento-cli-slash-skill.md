---
id: ISSUE-PIPE-0006
title: Acionamento Tríade Universal: CLI, Slash Command e Skill Runner
status: ready-for-agent
blocked_by: [ISSUE-PIPE-0003, ISSUE-PIPE-0004, ISSUE-PIPE-0005]
created: 2026-09-21
source: Relatório de Melhoria 21-09-2026 — Pipeline Unificado de Orquestração
---

# ISSUE-PIPE-0006 — Acionamento Tríade Universal: CLI, Slash Command e Skill Runner

**Deliver:** Complete universal triad dispatch integration for the execution pipeline across all harnesses, enforcing Law #6 (Agnostic Supremacy) and Law #7 (Developer in Control).

**Blocked by:** `ISSUE-PIPE-0003`, `ISSUE-PIPE-0004`, `ISSUE-PIPE-0005`.

## Scope

1. **CLI Central (`ecossistema.py`):**
   - Add `cmd_run_plan`: `python ecossistema.py run-plan <plano-path-or-slug>`.
   - Add `cmd_pipeline`: `python ecossistema.py pipeline --handoff <json-path>`.
2. **Skill Runner (`componentes/compartilhado/skills/aidd-pipeline-runner/`):**
   - Implement `SKILL.md` with deterministic dispatch script.
   - Sync skill to all 7 harnesses via `python scripts/gestor_componentes.py sync --tipo skill`.
3. **Slash Commands:**
   - Document and intercept `/run-plan <plano>` and `/pipeline <handoff>` across `AGENTS.md`, `GEMINI.md`, and harness pointer files.
   - Prohibit "unsupported command" errors across all environments.

## Acceptance criteria

- [ ] `python ecossistema.py run-plan --help` and `python ecossistema.py pipeline --help` work with exit 0.
- [ ] Skill `aidd-pipeline-runner` synchronized and present in `.agents/`, `.claude/`, `.gemini/`.
- [ ] Quality gate `gates/G_UNIVERSAL_HARNESS.py` passes with exit 0.
- [ ] Quality gate `gates/G_CLI_HELP_CONSISTENCIA.py` passes with exit 0.
