---
id: ISSUE-0021
title: Gate de saída binária para a Lei #2 (sys.exit(0)/sys.exit(1) estrito)
status: closed
blocked_by: []
created: 2026-09-20
source: BACKLOG-LEIS-SEM-GATE.md item 2.2 — enforcement gap analysis
---

# ISSUE-0021 — Gate de saída binária para a Lei #2

**Deliver:** Law #2 stops being convention-only. A gate audits every file
under `gates/` and asserts its only exit points are `sys.exit(0)` or
`sys.exit(1)` — no bare `return`, no ambiguous numeric code, no unguarded
exception falling through to Python's implicit exit 0.

**Blocked by:** nothing. Start now.

## Scope

1. AST walk of each `gates/*.py`: find `sys.exit` call sites; flag any
   argument that is not literal `0` or `1`.
2. Flag any `gates/*.py` whose `if __name__ == "__main__"` block can fall
   through without an explicit `sys.exit` call.
3. Build `gates/G_SAIDA_BINARIA.py` running both checks against the full
   `gates/` directory.

## Acceptance criteria

- [x] Gate flags any gate file exiting with something other than literal 0/1.
- [x] Gate flags a gate file with no explicit `sys.exit` in its main block.
- [x] Own failing-path test: synthetic gate file with `sys.exit(2)`, assert
      exit 1.
- [x] False-positive check: an existing compliant gate (e.g.
      `G_HONESTIDADE_ROTULO.py`) passes.
- [x] Run against the current `gates/` directory; violations triaged
      individually, not bulk-suppressed.
- [x] Law #2 in `AGENTS.md` updated from `sem-gate` to name this gate.
- [x] `BACKLOG-LEIS-SEM-GATE.md` row for Lei #2 updated.
