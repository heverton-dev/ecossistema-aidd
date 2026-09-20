---
id: ISSUE-0014
title: Portão de Contract Rot (rotas reais versus contrato escrito)
status: completed
blocked_by: []
created: 2026-09-19
source: docs/melhorias/19-09-2026_melhoria-taxonomia-prevencao-rot-ecossistema.md — category 6
---

# ISSUE-0014 — Portão de Contract Rot

**Deliver:** a route that changes status code, query param or field type without the
OpenAPI document following is blocked at commit.

**Blocked by:** nothing. Start now.

## Why this one is genuinely new

Checked against all 27 existing gates: none compares the live route tree against the
versioned `openapi.json`. `G_ECOSSISTEMA_INTEGRIDADE` checks route registration, not
schema fidelity.

Stakes: the Quarteto Sine Qua Non (`/docs`, `/webhooks`, `/mcp`, `/docs/guia`) is what
agent clients read to decide how to call the system. A drifted contract does not
produce an error — it produces confident wrong calls.

## Scope

Deterministic comparison: enumerate routes and response shapes as the generated
server actually exposes them, diff against the committed `openapi.json`. Exit 1 on
any divergence.

**Known trap, already measured:** `AGENTS.md` Law #10 cited `/swagger` while every
generated server serves `/docs` (see ISSUE-0001). Build the gate against the real
served paths, not the documented ones.

## Acceptance criteria

- [x] Gate enumerates routes from the running generated server, not from source comments.
- [x] Diffs status codes, query params and field types against committed `openapi.json`.
- [x] Exit 1 on divergence, with the diverging route named in the output.
- [x] Failing-path test, strict Law #13: mutate one route's status code, execute the gate, assert exit 1.
- [x] Output claims only what it checks. No coverage language beyond the diff performed (Law #8).
- [x] Declared against its law in `AGENTS.md`, per ISSUE-0010 convention.
