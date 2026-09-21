---
id: ISSUE-PIPE-0007
title: Integração Completa de Ponta a Ponta e Testes de Regressão
status: ready-for-agent
blocked_by: [ISSUE-PIPE-0006]
created: 2026-09-21
source: Relatório de Melhoria 21-09-2026 — Pipeline Unificado de Orquestração
---

# ISSUE-PIPE-0007 — Integração Completa de Ponta a Ponta e Testes de Regressão

**Deliver:** Comprehensive end-to-end test suite verifying the complete pipeline from intake compilation to worktree execution, join barrier, and audit verification.

**Blocked by:** `ISSUE-PIPE-0006`.

## Scope

1. Create `tests/test_e2e_pipeline_orquestracao.py`.
2. Test Scenario 1: Synthetic 20-step refactor plan (15 parallel async, 5 sequential sync):
   - Compiles markdown tickets to `handoff_evolution.json`.
   - Executes 15 worktrees in parallel without filesystem conflict.
   - Join barrier verifies gates and merges cleanly.
   - Executes 5 sequential steps to completion.
   - Asserts 100% cleanup of worktrees and branches.
3. Test Scenario 2: Error injection:
   - Deliberate test failure in step 8 of 15.
   - Asserts join barrier catches failure, aborts merge, cleans up worktrees, and returns exit 1.
4. Run full repository audit: `python ecossistema.py audit`.
5. Update `docs/teste-end-to-end/` with contemporany execution evidence per Law #9.

## Acceptance criteria

- [ ] `pytest tests/test_e2e_pipeline_orquestracao.py` passes 100% of scenarios.
- [ ] Subprocess run in temporary repository leaves zero orphaned worktrees.
- [ ] `python ecossistema.py audit` exits 0 with all 26 Quality Gates green.
- [ ] Contemporany report committed in `docs/teste-end-to-end/` per Law #9.
