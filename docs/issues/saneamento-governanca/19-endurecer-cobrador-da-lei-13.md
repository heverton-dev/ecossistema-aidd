---
id: ISSUE-0019
title: Endurecer o cobrador da Lei #13 (executar o teste, não procurar o texto)
status: resolved
blocked_by: []
created: 2026-09-19
resolved: 2026-09-19
source: open-decision sweep 2026-09-19 — verified against G_PORTAO_PROVA_QUE_MORDE
---

# ISSUE-0019 — Endurecer o cobrador da Lei #13

**Deliver:** the gate enforcing Law #13 stops pattern-matching test files and starts
executing them, and stops claiming 100% coverage it has not measured.

**Blocked by:** nothing. Start now. Every gate written from here inherits this one's
strictness.

## Verified this session

`gates/G_PORTAO_PROVA_QUE_MORDE.py` (178 lines, read in full) checks three things per
gate, all static:

1. A file `gates/test_g_<name>.py` exists.
2. It contains at least one `test_*()` function.
3. Its text matches one of eleven regex patterns asserting exit 1
   (`returncode == 1`, `assertEqual(..., 1)`, `SystemExit(1)`, …).

**It never runs the tests.** It confirms the right sentence is written in the file.
Then it prints `[SUCESSO] 100% dos 26 Quality Gates provam que mordem (exit 1)!`

Two defects:

- **Same family as the facade it replaced.** `G_ZERO_HEADLESS` grepped for two literal
  strings; this greps for eleven regexes. Better, still text inspection standing in for
  behaviour verification. A test can assert `returncode == 1` against a trivially
  broken input unrelated to the real invariant and pass this check.
- **Claim exceeds measurement (Law #8).** "100% provam que mordem" is asserted while
  ISSUE-0011 scope 3 — auditing whether the 18 pre-existing tests exercise a real
  failing path — has not run.

## Scope

1. Execute each gate's test suite and require the failing-path test to actually pass.
2. Require the failing scenario to touch the invariant the gate guards, not any exit-1
   path. Define how this is checked deterministically, or state the limit honestly.
3. Rewrite the output to claim only what was measured.

## Acceptance criteria

- [x] Gate executes each test suite; a test that pattern-matches but fails to run causes exit 1.
- [x] Output claim reduced to what is measured. No "100%" until ISSUE-0011 scope 3 has run.
- [x] Gates whose tests pass the pattern check but fail execution are listed, not silently counted.
- [x] Its own failing-path test, strict reading: supply a gate whose test asserts exit 1 but errors on execution; assert this gate exits 1.
- [x] Where deterministic verification of "touches the real invariant" is not achievable, the limit is written into the gate output rather than implied away.
