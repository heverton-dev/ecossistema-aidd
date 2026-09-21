---
id: ISSUE-MESO-0006
title: Barreira de Validação por Fatia e Fusão Convergente no aidd-master
status: ready-for-agent
blocked_by: [ISSUE-MESO-0005]
created: 2026-09-21
source: Relatório de Melhoria 21-09-2026 — Meso-Camada da Tríade Canônica
---

# ISSUE-MESO-0006 — Barreira de Validação por Fatia e Fusão Convergente no aidd-master

**Deliver:** Synchronous validation barrier and merge orchestrator `tools/aidd-master/scripts/vsa_join_barrier.py`.

**Blocked by:** `ISSUE-MESO-0005`

## Scope

1. Implement `tools/aidd-master/scripts/vsa_join_barrier.py`:
   - `executar_barreira_fatia(worktree_path: str, slice_info: Dict[str, Any]) -> bool`:
     - Runs declared unit and contract tests in worktree.
     - Runs Quality Gates locally: `G_PORTAO_PROVA_QUE_MORDE`, `G_TESTES_REAIS`, `G_SAIDA_BINARIA`.
     - Validates slice isolation: verifies no slice wrote outside its designated directory boundaries (`src/slices/<slice_id>`, `tests/slices/<slice_id>`).
     - Returns `True` only if 100% of tests and gates pass with exit code 0.
   - `executar_convergencia_master(target_repo: str, slices_aprovadas: List[str]) -> bool`:
     - Merges validated slice branches into main development branch via fast-forward or squash merge.
     - Registers slices in `aidd-master` modular monolith registry (`main.py` router aggregation).
     - Validates end-to-end Quarteto Sine Qua Non endpoints (`/docs`, `/webhooks`, `/mcp`, `/docs/guia`).
     - Prepares output for handoff to `aidd-enterprise` (SHA-256 integrity seal).
2. Unit tests in `tools/aidd-master/tests/test_vsa_join_barrier.py`.

## Acceptance criteria

- [ ] Slices with failing tests or violated quality gates are blocked from merging.
- [ ] Cross-slice file collision is detected and blocked before merge.
- [ ] Approved slices are seamlessly aggregated into `aidd-master` main router.
