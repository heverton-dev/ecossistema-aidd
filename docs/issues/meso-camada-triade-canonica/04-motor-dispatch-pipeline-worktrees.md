---
id: ISSUE-MESO-0004
title: Motor de Despacho de Fatias em Git Worktrees Efêmeros
status: ready-for-agent
blocked_by: [ISSUE-MESO-0003]
created: 2026-09-21
source: Relatório de Melhoria 21-09-2026 — Meso-Camada da Tríade Canônica
---

# ISSUE-MESO-0004 — Motor de Despacho de Fatias em Git Worktrees Efêmeros

**Deliver:** Core execution engine `tools/aidd-master/scripts/dispatch_pipeline.py` managing ephemeral Git Worktrees and slice generation dispatch.

**Blocked by:** `ISSUE-MESO-0003`

## Scope

1. Create `tools/aidd-master/scripts/dispatch_pipeline.py`:
   - Ingest `VSA_DISPATCH.json` (or `PLANNER.json` and invoke compiler automatically).
   - Validate input against `G_DISPATCH_PIPELINE_VSA`. Abort with exit 1 if invalid.
   - For each topological level in the DAG:
     - Group independent slices into concurrent execution batches.
     - For each slice in batch:
       - Spawn ephemeral Git Worktree: `git worktree add -b slice/<id> .worktrees/<id>`.
       - Isolate working directory so no cross-slice contamination occurs.
       - Route execution to the target engine router (Issue 05).
       - Run local validation barrier (Issue 06).
       - Fast-forward or rebase merge slice branch into target staging branch.
       - Clean up worktree: `git worktree remove --force .worktrees/<id>`.
   - Implement robust error handling: ensure cleanup of temporary worktrees on keyboard interrupt, test failure, or exit.
2. CLI ergonomics:
   - Support `python tools/aidd-master/scripts/dispatch_pipeline.py --dispatch <manifest> [--target-dir <dir>] [--dry-run]`.

## Acceptance criteria

- [ ] Motor runs multiple independent slices in isolated worktrees without file conflicts.
- [ ] Temporary worktree directories are completely cleaned up after execution.
- [ ] In case of execution failure in a slice, the pipeline safely unmounts worktrees and reports exact failure code without corrupting main git index.
