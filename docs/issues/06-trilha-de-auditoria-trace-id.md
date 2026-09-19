---
id: ISSUE-0006
title: Trilha de auditoria (X-Trace-Id) — entregar de verdade ou parar de prometer
status: ready-for-agent
blocked_by: []
created: 2026-09-19
source: open-decision sweep 2026-09-19 / PLAN-0025 item 10
---

# ISSUE-0006 — Trilha de auditoria (X-Trace-Id): entregar ou parar de prometer

**Deliver:** either generated projects really do stamp a trace id on every request
and log, or the documentation stops claiming they do.

**Blocked by:** nothing. Start now.

## Verified this session

Most serious finding of the sweep. Not clutter — a compliance promise with no
implementation behind it.

The architecture doc describes Module 1.5 as: *"Universal propagation of the
X-Trace-Id header across requests, logs and async events... complete audit
traceability in compliance with data protection law"* (LGPD, GDPR), with a named
verifier gate.

Measured:

1. The piece that would do it (`TraceContextMiddleware`) is built by a factory
   (`create_trace_middleware`). **Nothing calls that factory.** Its only mention is
   the usage example inside the file's own docstring.
2. Worse than uncalled: it **could not** be mounted. It extends Starlette
   `BaseHTTPMiddleware`; the generated server uses stdlib `http.server`. Incompatible
   fittings — a three-pin plug at a two-pin socket.
3. Occurrences of "trace" in the generated server template: **zero**.

A partial mechanism exists in the template (a correlation variable imported from
`core.logs`), but it is not what the documentation describes.

## Two routes

- **Route A — deliver.** Implement header propagation in the server actually
  generated (`http.server`), with a test proving: request arrives carrying
  `X-Trace-Id`, same value returns in the response and appears in the log. The
  existing Starlette piece becomes either a FastAPI adapter or deleted.
- **Route B — stop promising.** Remove the dead piece and **correct the architecture
  doc**, dropping the LGPD/GDPR traceability compliance claim the product does not meet.

Route B is not defeat — it is Law #8 (label honesty) working. What cannot continue
is today's state: promise on paper, silence in code.

## Acceptance criteria

- [ ] Route chosen and justified.
- [ ] Route A: real end-to-end test proves the trace id enters, traverses and exits. The piece merely existing does not count.
- [ ] Route B: architecture doc Module 1.5 and the book corrected; compliance claim removed.
- [ ] Either route: no dead piece left in `src/core/opentelemetry.py` nor in the template and `componentes/compartilhado/` mirrors.
- [ ] Full suite still passes.
