---
id: ISSUE-MESO-0002
title: Compilador de Grafo Topológico VSA no aidd-planner
status: done
blocked_by: [ISSUE-MESO-0001]
created: 2026-09-21
source: Relatório de Melhoria 21-09-2026 — Meso-Camada da Tríade Canônica
---

# ISSUE-MESO-0002 — Compilador de Grafo Topológico VSA no aidd-planner

**Deliver:** Deterministic compiler function in `tools/aidd-planner/aidd_planner/core/planner_engine.py` and CLI command in `tools/aidd-planner/aidd_planner/cli.py` to translate `PLANNER.json` into `VSA_DISPATCH.json`.

**Blocked by:** `ISSUE-MESO-0001`

## Scope

1. In `planner_engine.py`, implement `compilar_grafo_topologico_vsa(plano: Dict[str, Any]) -> Dict[str, Any]`:
   - Inspect `ddd_bounded_contexts`, `bdd_cenarios`, and `payload_especifico_fluxo`.
   - Map each context into an independent Vertical Slice (VSA).
   - Infer slice dependencies based on cross-entity references or explicit flow requirements.
   - Detect and reject cycles using Kahn's topological sort algorithm (raise `PlannerValidationError` if cycle detected).
   - Generate validation commands and required quality gates per slice (`G_PORTAO_PROVA_QUE_MORDE`, unit tests).
   - Output valid data conforming strictly to `vsa-topological-dispatch.schema.json`.
2. In `aidd_planner/cli.py`, add CLI command:
   - `python -m aidd_planner.cli export-dispatch <caminho_planner.json> [--output <caminho>]`
3. Add unit and integration tests in `tools/aidd-planner/tests/test_vsa_compiler.py`.

## Acceptance criteria

- [x] `compilar_grafo_topologico_vsa` handles all 3 flows (`fluxo_01_generator`, `fluxo_02_factory`, `fluxo_03_bridge`).
- [x] Cyclic dependency triggers explicit exception.
- [x] Output complies 100% with `vsa-topological-dispatch.schema.json`.
- [x] All tests in `test_vsa_compiler.py` pass cleanly.
