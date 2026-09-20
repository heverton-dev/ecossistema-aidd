---
id: ISSUE-0023
title: Gate de disciplina de teste de ferramentas para a Lei #9
status: closed
blocked_by: []
created: 2026-09-20
source: BACKLOG-LEIS-SEM-GATE.md item 2.5 — enforcement gap analysis
---

# ISSUE-0023 — Gate de disciplina de teste de ferramentas para a Lei #9

**Deliver:** Law #9's 5-step cycle (`PROTOCOLO-TESTES-FERRAMENTAS.md`) stops
depending on the developer remembering it. A check blocks a commit that
touches a tool under `tools/` without a matching, freshly-dated report under
`docs/teste-end-to-end/`.

**Blocked by:** nothing. Start now.

## Scope

1. Define "touches a tool": diff includes files under a `tools/<name>/`
   path.
2. Build `gates/G_DISCIPLINA_TESTE_FERRAMENTA.py`: for each touched tool,
   require a report file under `docs/teste-end-to-end/` whose git-log
   timestamp is not older than the commit touching the tool.
3. Wire into the same pre-commit path as the other gates.

## Acceptance criteria

- [x] Gate blocks a commit touching `tools/<name>/` with no correspondingly
      fresh report.
- [x] Own failing-path test: synthetic commit touching a tool dir with a
      stale/missing report, assert exit 1.
- [x] False-positive check: a commit with a same-day updated report passes.
- [x] Law #9 in `AGENTS.md` updated from `sem-gate` to name this gate.
- [x] `BACKLOG-LEIS-SEM-GATE.md` row for Lei #9 updated.
