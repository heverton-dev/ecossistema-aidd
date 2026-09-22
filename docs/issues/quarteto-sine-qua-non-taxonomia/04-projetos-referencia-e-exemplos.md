---
id: ISSUE-QUARTETO-0004
title: Canonical Reference Projects and Examples Alignment
status: done
blocked_by: [ISSUE-QUARTETO-0003]
created: 2026-09-21
source: Architecture Decision Record 21-09-2026 — Quarteto Sine Qua Non
---

# ISSUE-QUARTETO-0004 — Canonical Reference Projects and Examples Alignment

**Deliver:** Update reference example project `tools/aidd-enterprise/materiais-extras/examples/enterprise-suite-v4/src/server.py` to match the new taxonomy.

**Blocked by:** ISSUE-QUARTETO-0003.

## Scope

1. Update routes in `enterprise-suite-v4/src/server.py` to expose `/api`, `/webhook`, `/mcp`, `/docs`.
2. Ensure backward-compatibility redirects for `/docs` -> `/api` and `/webhooks` -> `/webhook`.
3. Verify compliance with `G_QUARTETO_SINE_QUA_NON.py`.

## Acceptance criteria

- [x] Reference project routes match new canonical taxonomy.
- [x] `G_QUARTETO_SINE_QUA_NON.py` passes with exit 0.
