---
id: ISSUE-0001
title: Faxina de registros desatualizados (trava de honestidade, Lei 10, CircuitBreaker)
status: done
blocked_by: []
created: 2026-09-19
source: open-decision sweep 2026-09-19
---

# ISSUE-0001 — Faxina de registros desatualizados

**Deliver:** three project records stop describing a reality that no longer exists,
and one disabled gate goes back on. No behaviour change — truth on paper only.

**Blocked by:** nothing. Start now.

## Verified this session

1. **Label-honesty gate.** Set to `stages: [manual]` on 2026-09-08 pending a human
   decision about marketing wording in gate output. Ran the real hook
   (`pre-commit run --hook-stage manual g-honestidade-rotulo --all-files`):
   **exit 0**, 68 files audited, zero banned terms. The reason for disabling is gone.
2. **AGENTS.md Law #10** cites `/swagger` as the Swagger Studio path (lines 31, 55).
   No generated server serves that path — all use `/docs`. Flagged 2026-09-16, never fixed.
3. **CircuitBreaker is not dead code.** PLAN-0025 item 10 lists it as caller-less.
   Verified otherwise: used in the server-generating template (three breakers —
   webhooks, SSO, MCP), has a state endpoint, has tests. The `src/core/` file is a
   byte-identical copy of `templates/core/` (diff-confirmed) — mirror, not orphan.

## Acceptance criteria

- [x] Label-honesty gate leaves `stages: [manual]`; runs on every commit.
- [x] Drop the `.pre-commit-config.yaml` comments claiming a pending human decision for it.
- [x] Book Appendix E and equivalent sections stop listing it as open.
- [x] Law #10 cites only the real path (`/docs`).
- [x] PLAN-0025 item 10 records CircuitBreaker reclassified as template mirror, with diff evidence.
- [x] A test commit confirms the re-enabled gate blocks nothing legitimate.
