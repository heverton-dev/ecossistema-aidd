---
id: ISSUE-QUARTETO-0003
title: Core Server Implementations and Templates Alignment
status: done
blocked_by: [ISSUE-QUARTETO-0002]
created: 2026-09-21
source: Architecture Decision Record 21-09-2026 — Quarteto Sine Qua Non
---

# ISSUE-QUARTETO-0003 — Core Server Implementations and Templates Alignment

**Deliver:** Update HTTP route handlers in master and enterprise core servers and templates to serve new canonical routes with backward-compatible aliases.

**Blocked by:** ISSUE-QUARTETO-0002.

## Scope

1. Update `tools/aidd-master/src/server.py`, `tools/aidd-master/templates/core/server.py`, `tools/aidd-master/templates/v2/server.py`:
   - Set `/api` as primary Swagger/OpenAPI endpoint; redirect `/docs` to `/api` or documentation center.
   - Set `/webhook` as primary webhook endpoint; alias `/webhooks`.
   - Set `/docs` as documentation center; alias `/docs/guia`.
2. Update `tools/aidd-enterprise/src/server.py`, `tools/aidd-enterprise/templates/core/server.py`, `tools/aidd-enterprise/templates/v2/server.py` with identical contract.
3. Validate drift prevention with `G_DRIFT_NUCLEO_COMPARTILHADO.py`.

## Acceptance criteria

- [x] All 6 server files expose `/api`, `/webhook`, `/mcp`, `/docs`.
- [x] `G_DRIFT_NUCLEO_COMPARTILHADO.py` passes with exit 0.
