---
id: ISSUE-0011
title: Todo portão precisa de um teste que prove que ele reprova
status: closed
blocked_by: []
created: 2026-09-19
closed: 2026-09-19
source: open-decision sweep 2026-09-19 — enforcement gap analysis
---

# ISSUE-0011 — Todo portão precisa provar que morde

**Deliver:** a gate counts as enforcement only once a test proves it **fails** when
the thing it guards is actually broken. Gates that pass regardless of system state
are decoration. This ticket finds them and fixes them.

**Blocked by:** nothing. Start now. Highest-leverage ticket of this batch.

## Verified this session

**All 26 gates in gates/ carry proven failing-path tests (asserting exit 1):**

| Group | Quantity | Status |
|---|---|---|
| Gates without initial test (Scope 2) | 8 | 100% with proven failing-path test (exit 1) |
| Gates with audited tests (Scope 3) | 18 | 100% with proven failing-path test (exit 1) |
| Authoring Meta-Gate (Scope 4) | 1 (`G_PORTAO_PROVA_QUE_MORDE.py`) | 100% active, tested (`test_g_portao_prova_que_morde.py`), integrated in pre-commit and `ecossistema.py` |

## Scope

1. [x] Write the rule: every gate ships with a test that **breaks the guarded condition
   and asserts exit 1**. Passing-path tests alone do not satisfy it.
   - Delivered in `docs/protocolos/CONVENCAO-AUTORIA-GATES.md`, `AGENTS.md` (Law #13) and `docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md`.
2. [x] Apply to the 8 gates above. Start with `G_ZERO_HEADLESS` and `G_TESTES_REAIS`.
   - Delivered with real reproduction via hooks and dedicated pytest suite.
3. [x] Audit the 18 gates that **do** have tests: confirm each exercises the failing
   path. A test asserting only exit 0 carries the same defect, just hidden. (Delivered in Session 2)
   - Diagnosed 10 gates with end-to-end failure test gaps (pure unit tests or asserted exit 0) and 1 fake test with useless assertion (`G_ESCRITOR_ATOMICO` asserted `os.path.isfile`).
   - All 10 tests updated with strict failure assertions (`exit 1` / `code == 1` / `returncode == 1`).
4. [x] Add a meta-gate enforcing rule 1 on any new gate. (Delivered in Session 2)
   - Delivered `gates/G_PORTAO_PROVA_QUE_MORDE.py`, `gates/test_g_portao_prova_que_morde.py`, hook `g-portao-prova-que-morde` in `.pre-commit-config.yaml` and `_GATES_AUDIT` list in `ecossistema.py`.

## Acceptance criteria

- [x] Rule written into the project gate-authoring convention (`docs/protocolos/CONVENCAO-AUTORIA-GATES.md`).
- [x] Each of the 8 untested gates has a test that breaks the guarded condition and asserts exit 1.
- [x] The 18 existing gate tests audited for a real failing-path assertion; gaps listed and fixed.
- [x] Every gate found unable to fail is recorded as a facade with its claim downgraded — never left asserting coverage it lacks (`G_ZERO_HEADLESS`).
- [x] Meta-gate blocks any new gate shipped without a failing-path test (`gates/G_PORTAO_PROVA_QUE_MORDE.py`).
- [x] `G_ZERO_HEADLESS` output stops claiming "zero risco" beyond what it actually tests.

