---
id: ISSUE-MESO-0005
title: Roteadores Especialistas para as 3 Engines da Tríade
status: ready-for-agent
blocked_by: [ISSUE-MESO-0004]
created: 2026-09-21
source: Relatório de Melhoria 21-09-2026 — Meso-Camada da Tríade Canônica
---

# ISSUE-MESO-0005 — Roteadores Especialistas para as 3 Engines da Tríade

**Deliver:** Dispatch engine router `tools/aidd-master/scripts/engine_router.py` connecting the slice dispatch runner to the specialized engines.

**Blocked by:** `ISSUE-MESO-0004`

## Scope

1. Implement `tools/aidd-master/scripts/engine_router.py`:
   - `despachar_fatia(slice_info: Dict[str, Any], fluxo: str, worktree_path: str) -> bool`:
     - **Fluxo 01 (`fluxo_01_generator` / Pure):** Invokes `aidd-generator` with TDD Red-Green arguments targeting solely the designated vertical slice paths (`src/slices/<slice_id>`), generating schemas, router, models, and domain tests.
     - **Fluxo 02 (`fluxo_02_factory` / Open):** Invokes `aidd-factory` with open-source service integration params, creating reverse-proxy routes and VSA integration slices inside the worktree.
     - **Fluxo 03 (`fluxo_03_bridge` / Freedom):** Invokes `aidd-bridge` with low-code extraction configs, performing table mapping, entity decoupling, and UI route wiring for the slice.
   - Inject the Quarteto Sine Qua Non configuration (`/docs`, `/webhooks`, `/mcp`, `/docs/guia`) into each slice router definition dynamically.
2. Provide deterministic unit tests in `tools/aidd-master/tests/test_engine_router.py`.

## Acceptance criteria

- [ ] Generator router successfully calls `aidd-generator` sub-process with slice scope.
- [ ] Factory router adapts open-source curation parameters to slice integration scope.
- [ ] Bridge router adapts low-code decoupling parameters to slice scope.
- [ ] Zero hardcoded entity mocks; all parameters originate from slice definition.
