---
id: ISSUE-MESO-0003
title: Quality Gate G_DISPATCH_PIPELINE_VSA com Prova que Morde
status: done
blocked_by: [ISSUE-MESO-0001, ISSUE-MESO-0002]
created: 2026-09-21
source: Relatório de Melhoria 21-09-2026 — Meso-Camada da Tríade Canônica
---

# ISSUE-MESO-0003 — Quality Gate G_DISPATCH_PIPELINE_VSA com Prova que Morde

**Deliver:** Quality Gate `gates/G_DISPATCH_PIPELINE_VSA.py` and proving test `tests/test_gate_dispatch_pipeline_vsa.py` strictly enforcing Law #1, #2, and #13.

**Blocked by:** `ISSUE-MESO-0001`, `ISSUE-MESO-0002`

## Scope

1. Create `gates/G_DISPATCH_PIPELINE_VSA.py`:
   - Inspect any generated application dispatch manifest or project directory.
   - Assert presence and validity of `VSA_DISPATCH.json` against `vsa-topological-dispatch.schema.json`.
   - Assert all slices define isolation `git-worktree` and real test commands (zero empty strings/stubs).
   - Assert topological graph has no cycles and resolves in a finite directed acyclic graph.
   - Return exit code `0` on compliant dispatch manifest.
   - Return exit code `1` on missing manifest, broken schema, cycle, or stubs.
2. Create automated test `tests/test_gate_dispatch_pipeline_vsa.py`:
   - Proves gate passes (exit 0) on valid VSA dispatch manifest.
   - Proves gate bites (exit 1) on: missing validation commands, invalid JSON, cyclic dependencies, missing schema.
3. Register gate in `ecossistema.py` audit runner.

## Acceptance criteria

- [x] `python gates/G_DISPATCH_PIPELINE_VSA.py --manifest <valid_manifest>` returns exit code 0.
- [x] `pytest tests/test_gate_dispatch_pipeline_vsa.py` passes all test cases proving bite per Law #13.
- [x] Gate appears in `python ecossistema.py audit` listing.
