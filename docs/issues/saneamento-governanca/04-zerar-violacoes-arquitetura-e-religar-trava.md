---
id: ISSUE-0004
title: Zerar as 18 violacoes de banco fora da camada e religar a trava de arquitetura
status: ready-for-agent
blocked_by: []
created: 2026-09-19
source: open-decision sweep 2026-09-19 / PLAN-0023 item 1
---

# ISSUE-0004 — Zerar as 18 violações de arquitetura e religar a trava

**Deliver:** the rule that database calls live only in the infrastructure layer is
enforced automatically again, instead of sitting disabled waiting on a backlog.

**Blocked by:** nothing. Start now.

## Verified this session

Ran the real hook (`pre-commit run --hook-stage manual g-arquitetura-deliverable
--all-files`): **exit 1, 18 real violations**, concentrated in four files — really
two mirrored pairs across the two tools:

| File | Violations |
|---|---|
| `tools/aidd-master/src/core/transaction_log.py` | 7 |
| `tools/aidd-enterprise/src/core/transaction_log.py` | 7 |
| `tools/aidd-master/src/core/mcp_server.py` | 2 |
| `tools/aidd-enterprise/src/core/mcp_server.py` | 2 |

**Scope discrepancy — resolve it, do not ignore it.** PLAN-0023 item 1 sizes this
work at "212 violations in templates". Today's measurement gives 18, in `src/core/`,
not templates. Either the backlog dropped hard since 2026-09-11, or the plan counted
something else. **If 194 template violations exist that the gate cannot see, the
defect is gate coverage, not backlog.** Settle which, in writing.

Files come in mirrored pairs enforced by a drift gate. Apply every fix on both sides.

## Acceptance criteria

- [ ] The 18-vs-212 gap is explained in writing: backlog cleared, or gate blind spot.
- [ ] DB calls move out of `transaction_log.py` and `mcp_server.py` into the infrastructure layer, in both tools.
- [ ] Master/enterprise drift gate still approves.
- [ ] Real hook exits 0.
- [ ] Gate leaves `stages: [manual]`; runs on every commit.
- [ ] PLAN-0023 item 1 updated with the real number and outcome.
