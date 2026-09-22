---
id: ISSUE-QUARTETO-0001
title: Governance, Laws and Canonical Reference Taxonomy Update
status: done
blocked_by: []
created: 2026-09-21
source: Architecture Decision Record 21-09-2026 — Quarteto Sine Qua Non
---

# ISSUE-QUARTETO-0001 — Governance, Laws and Canonical Reference Taxonomy Update

**Deliver:** Update Law #10 definition across core governance documents to `[/api, /webhook, /mcp, /docs]`.

**Blocked by:** nothing. Start now.

## Scope

1. Update `AGENTS.md`: Law #10 text reflecting new canonical routes: `/api` (OpenAPI Studio), `/webhook` (Webhook Studio), `/mcp` (MCP Studio), `/docs` (Documentation / User Guide).
2. Update `MEMORY.md`: record architectural decision and route matrix.
3. Update `docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md`: align Quarteto Sine Qua Non section.
4. Update `GEMINI.md` and harness pointers.

## Acceptance criteria

- [x] `AGENTS.md` explicitly defines Law #10 with routes `[/api, /webhook, /mcp, /docs]`.
- [x] `MEMORY.md` contains architectural record of taxonomy migration.
- [x] `G_HARNESS_COMPAT.py` passes with exit 0.
