---
name: aidd-pipeline
description: Runs the deterministic Triad pipeline in ephemeral git worktrees with a join barrier, from a Markdown plan (run-plan) or a JSON handoff manifest (pipeline). Use when the user wants to execute plan tickets in parallel worktrees, or types "/run-plan", "/pipeline", "run-plan", "pipeline", "rodar plano em worktrees".
---

# aidd-pipeline

## Invariants

1. **Determinism first (Law #1):** dispatch driven by the formal JSON Schema (`handoff-execucao.schema.json`) and native git operations.
2. **Binary exit (Law #2):** `exit 0` = every validation passed; `exit 1` = immediate block and merge abort.
3. **Zero stubs (Law #5):** TODO, FIXME, PLACEHOLDER and trivial validation commands (`exit 0`, `true`, `echo ok`) are rejected.
4. **Agnostic (Law #6):** works on Windows PowerShell and Linux Bash, in every harness.
5. **Developer in control (Law #7):** synchronous and inspectable, no invisible subagents; worktrees cleaned deterministically at the end.

## Architecture

```text
Markdown plan (docs/planos/) OR JSON handoff manifest
                     |
                     v
Parallel phase (ephemeral worktrees)
  - Task A (.worktrees/TASK-A on branch task/TASK-A)
  - Task B (.worktrees/TASK-B on branch task/TASK-B)
                     |
                     v
Join barrier
  - any task fails: full abort and cleanup
  - all pass: sequential merge into the base branch
                     |
                     v
Sequential phase (main tree)
  - migrations, global gates, final validation
```

## Run

```bash
# from a Markdown plan: compile tickets to JSON and run
python ecossistema.py run-plan docs/planos/a-fazer/PLAN-0029-teste-e2e-ferramentas
python ecossistema.py run-plan PLAN-0029-teste-e2e-ferramentas --dry-run
python ecossistema.py run-plan PLAN-0029-teste-e2e-ferramentas --no-exec   # compile only

# from a JSON handoff manifest
python ecossistema.py pipeline --handoff docs/planos/a-fazer/PLAN-0029-teste-e2e-ferramentas/handoff_evolution.json
python ecossistema.py pipeline --handoff <handoff.json> --dry-run -q
```

Done when the command exits 0 after the sequential phase.

Slash commands in any harness: `/run-plan <plan>` runs `python ecossistema.py run-plan <plan>`; `/pipeline <handoff>` runs `python ecossistema.py pipeline --handoff <handoff>`.
