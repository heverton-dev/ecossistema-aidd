---
name: aidd-dispatch
description: Dispatches VSA vertical slices into ephemeral git worktrees in topological (DAG) batches, with strict file boundaries, quality gates per slice and safe convergence into the aidd-master modular monolith. Use when the user wants to execute a PLANNER.json or vsa_dispatch.json as slices, or types "/dispatch", "/aidd-dispatch", "dispatch", "despachar fatias".
---

# aidd-dispatch (VSA meso-layer dispatch)

## Invariants

1. **Topological determinism (Law #1):** the compiled plan (`vsa_dispatch.json`) orders slices with Kahn's algorithm. Independent slices share a batch; dependent ones wait for the previous convergence.
2. **Binary exit (Law #2):** each slice and the master convergence pass quality gates (`exit 0` approves, `exit 1` blocks).
3. **Worktree isolation (Law #7):** each slice runs in `.worktrees/<slice_id>` on branch `slice/<slice_id>`; cleanup is guaranteed.
4. **Strict file boundary (Law #5):** a slice may only change files under its `arquivos_permitidos`; a violation aborts the merge.
5. **Quarteto Sine Qua Non (Law #10):** every slice provides routes and contracts for the Quarteto defined in `AGENTS.md` section 3.

## Run

```bash
# from PLANNER.json (compiles the graph and dispatches)
python ecossistema.py dispatch --planner <path/to/PLANNER.json>

# from a precompiled vsa_dispatch.json (validated by G_DISPATCH_PIPELINE_VSA)
python ecossistema.py dispatch --dispatch <path/to/vsa_dispatch.json>

# simulation: graph, contracts and isolation without touching git or disk
python ecossistema.py dispatch --planner <path/to/PLANNER.json> --dry-run

# limit parallel worktrees
python ecossistema.py dispatch --planner <path/to/PLANNER.json> --workers 2
```

Done when the command exits 0 and every slice converged into master.

## Intake chain

`/aidd-grill` -> `/aidd-spec` -> `/aidd-planner` -> `/aidd-dispatch` -> `aidd-master` -> `aidd-enterprise`
