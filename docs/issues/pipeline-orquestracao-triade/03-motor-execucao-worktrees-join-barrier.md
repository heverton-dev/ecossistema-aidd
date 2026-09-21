---
id: ISSUE-PIPE-0003
title: Motor de Execução de Fases em Git Worktrees e Join Barrier
status: ready-for-agent
blocked_by: [ISSUE-PIPE-0002]
created: 2026-09-21
source: Relatório de Melhoria 21-09-2026 — Pipeline Unificado de Orquestração
---

# ISSUE-PIPE-0003 — Motor de Execução de Fases em Git Worktrees e Join Barrier

**Deliver:** Deterministic execution engine at `tools/aidd-master/scripts/orchestrator_pipeline.py` that partitions tasks into ephemeral Git Worktrees, executes validation commands, and merges through a join barrier.

**Blocked by:** `ISSUE-PIPE-0002`.

## Scope

1. Read validated handoff manifest JSON.
2. For each task in `fase_paralela_assincrona`:
   - Create ephemeral worktree at `.worktrees/<task_id>` on fresh branch `task/<task_id>`.
   - Run task's `comando_validacao` inside worktree directory.
   - Record output, execution time, and exit code.
3. Join Barrier:
   - If any parallel task fails (exit != 0), immediately abort merge, log failing task, and clean up all worktrees (`git worktree remove --force`).
   - If all parallel tasks pass: sequentially rebase/merge branches into base branch.
4. For `fase_sequencial_sincrona`:
   - Execute each ordered step in the main working tree.
   - Stop immediately on first failure.
5. Exit 0 on complete end-to-end success, exit 1 on any failure.

## Acceptance criteria

- [ ] `orchestrator_pipeline.py` executes cleanly on Windows PowerShell and Linux bash.
- [ ] Ephemeral worktrees are 100% cleaned up even upon unhandled exceptions.
- [ ] Concurrency test: runs 3 mock parallel tasks in worktrees simultaneously without file collision.
- [ ] Join barrier blocks merge when one task fails validation.
