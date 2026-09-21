---
id: ISSUE-PIPE-0005
title: Exportador Nativo do aidd-planner para o Schema de Pipeline
status: ready-for-agent
blocked_by: [ISSUE-PIPE-0001]
created: 2026-09-21
source: Relatório de Melhoria 21-09-2026 — Pipeline Unificado de Orquestração
---

# ISSUE-PIPE-0005 — Exportador Nativo do aidd-planner para o Schema de Pipeline

**Deliver:** Native exporter in `tools/aidd-planner/src/core/planner_engine.py` translating `PLANNER.json` into the unified execution handoff schema for the Canonical Triad (Pure, Open, Freedom).

**Blocked by:** `ISSUE-PIPE-0001`.

## Scope

1. Implement `exportar_para_pipeline_execucao(plano: Dict[str, Any]) -> Dict[str, Any]`.
2. Map Bounded Contexts (DDD) into independent vertical slices in `fase_paralela_assincrona`.
3. Set validation commands using project test runner (e.g. `pytest tests/unit/test_<slice>.py`).
4. Map shared database migrations, API gateway routes, and Quarteto Sine Qua Non verification into `fase_sequencial_sincrona`.
5. Expose via CLI: `python -m aidd_planner.cli export <caminho> --formato pipeline`.
6. Assert output conforms strictly to `handoff-execucao.schema.json`.

## Acceptance criteria

- [ ] Command `python -m aidd_planner.cli export <path> --formato pipeline` outputs valid execution handoff.
- [ ] Exported output validates cleanly against `gates/G_PIPELINE_HANDOFF.py` with exit 0.
- [ ] Unit tests in `tools/aidd-planner/tests/` verify translation fidelity for Flows 1, 2, and 3.
