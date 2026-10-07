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

## Negative Guardrails

- NEVER trust invariant 4 alone: no code in `modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/scripts/dispatch_pipeline.py` or `gates/G_DISPATCH_PIPELINE_VSA.py` reads `arquivos_permitidos` (the manifest field is `arquivos_esperados`); check each `slice/<slice_id>` with `git diff --name-only <base>...slice/<slice_id>` yourself.
- NEVER keep manual edits in `.worktrees/<slice_id>`: `_run_slice_validation` runs `git add -A` and auto-commits everything there as `feat(<slice_id>): auto-commit vertical slice`, and even `--dry-run` cleanup `shutil.rmtree`s that folder.
- NEVER break a cycle by deleting edges from `vsa_dispatch.json`: fix dependencies in `PLANNER.json` (`aidd-planner`) and recompile.
- NEVER read a `--dry-run` exit 0 as converged: slices, `despachar_fatia` and `post_merge_suite` are simulated.
- NEVER write a slice that imports another slice's internals or skips the Quarteto routes: master convergence and `aidd-enterprise` depend on that contract.

## Failure Modes & Fallback

- **`ERRO: Rejeitado por G_DISPATCH_PIPELINE_VSA`:** run `python gates/G_DISPATCH_PIPELINE_VSA.py --manifesto <vsa_dispatch.json>`; fix stubs, missing `isolamento: git-worktree` or cycles at the source.
- **`Falha na compilação do PLANNER.json para VSA`:** `compilar_grafo_topologico_vsa` failed; run `python ecossistema.py planner validate` on that planner before dispatching.
- **`ERRO FATAL na fatia '<id>'`:** the batch stops before merge; fix the slice's `comandos_teste` failure and rerun the whole dispatch.
- **`Falha na suíte pós-merge`:** slices are already merged; show the user the failing command and `git log --oneline -<n>` instead of resetting.

## Stopping Checklist

Prove each item with the exit code read from a file (`> x.log 2>&1; echo $? > x.rc`, read `x.rc`), never through a pipe.

- [ ] `python gates/G_DISPATCH_PIPELINE_VSA.py --manifesto <vsa_dispatch.json>` exit 0 (or the `--planner` dry-run exit 0).
- [ ] `python ecossistema.py dispatch --planner <PLANNER.json>` exit 0 without `--dry-run`.
- [ ] Each slice's `git diff --name-only` stays inside its `arquivos_esperados`.
- [ ] `git worktree list` has no `.worktrees/<slice_id>` and `git branch --list "slice/*"` is empty.
