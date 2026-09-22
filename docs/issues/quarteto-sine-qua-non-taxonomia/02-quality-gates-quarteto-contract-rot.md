---
id: ISSUE-QUARTETO-0002
title: Quality Gates and Route Validation Logic Migration
status: done
blocked_by: [ISSUE-QUARTETO-0001]
created: 2026-09-21
source: Architecture Decision Record 21-09-2026 — Quarteto Sine Qua Non
---

# ISSUE-QUARTETO-0002 — Quality Gates and Route Validation Logic Migration

**Deliver:** Update `gates/G_QUARTETO_SINE_QUA_NON.py` and test suite `gates/test_g_quarteto_sine_qua_non.py` to assert new canonical taxonomy while preserving backward compatibility.

**Blocked by:** ISSUE-QUARTETO-0001.

## Scope

1. Update `gates/G_QUARTETO_SINE_QUA_NON.py`:
   - Detect `/api` for API Studio (with legacy fallback `/docs`).
   - Detect `/webhook` for Webhook Studio (with legacy fallback `/webhooks`).
   - Detect `/mcp` for MCP Studio.
   - Detect `/docs` for Documentation Center (with legacy fallback `/docs/guia`).
2. Update unit tests in `gates/test_g_quarteto_sine_qua_non.py` validating both canonical routes and legacy redirects.
3. Verify Law #13 proof requirement (`exit 1` on missing pillar).

## Acceptance criteria

- [x] `gates/test_g_quarteto_sine_qua_non.py` passes 6/6 tests.
- [x] Gate strictly fails with exit 1 when any required pillar is missing.
- [x] Gate passes with exit 0 on projects adopting new taxonomy.
