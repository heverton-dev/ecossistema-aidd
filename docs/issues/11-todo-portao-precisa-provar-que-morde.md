---
id: ISSUE-0011
title: Todo portão precisa de um teste que prove que ele reprova
status: in-progress (escopos 1 e 2 concluidos; 3 e 4 para sessao 2)
blocked_by: []
created: 2026-09-19
source: open-decision sweep 2026-09-19 — enforcement gap analysis
---

# ISSUE-0011 — Todo portão precisa provar que morde

**Deliver:** a gate counts as enforcement only once a test proves it **fails** when
the thing it guards is actually broken. Gates that pass regardless of system state
are decoration. This ticket finds them and fixes them.

**Blocked by:** nothing. Start now. Highest-leverage ticket of this batch.

## Verified this session

**8 of 26 gates have no test at all:**

| Gate | Lines | Status Teste Reprovação (Exit 1) |
|---|---|---|
| `G_ZERO_HEADLESS` | 37 | Entregue (`gates/test_g_zero_headless.py`) + Claim rebaixado per Lei #8 |
| `G_TESTES_REAIS` | 283 | Entregue (`gates/test_g_testes_reais.py`) |
| `G_UNIVERSAL_HARNESS` | 125 | Entregue (`gates/test_g_universal_harness.py`) + Hook registrado |
| `G_HARNESS_COMPAT` | 147 | Entregue (`gates/test_g_harness_compat.py`) |
| `G_COMPONENTE_AGNOSTICO` | 176 | Entregue (`gates/test_g_componente_agnostico.py`) |
| `G_LIVRO_EVIDENCIA` | 245 | Entregue (`gates/test_g_livro_evidencia.py`) + Hook registrado |
| `G_DRIFT_NUCLEO_COMPARTILHADO` | 266 | Entregue (`gates/test_g_drift_nucleo_compartilhado.py`) |
| `G_ARQUITETURA_DELIVERABLE` | 542 | Entregue (`gates/test_g_arquitetura_deliverable.py`) |

## Scope

1. [x] Write the rule: every gate ships with a test that **breaks the guarded condition
   and asserts exit 1**. Passing-path tests alone do not satisfy it.
   - Entregue em `docs/protocolos/CONVENCAO-AUTORIA-GATES.md`, `AGENTS.md` (Lei #13) e `docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md`.
2. [x] Apply to the 8 gates above. Start with `G_ZERO_HEADLESS` and `G_TESTES_REAIS`.
   - Entregue com reprodução real via hooks e suíte pytest dedicada.
3. [ ] Audit the 18 gates that **do** have tests: confirm each exercises the failing
   path. A test asserting only exit 0 carries the same defect, just hidden. (Sessão 2)
4. [ ] Add a meta-gate enforcing rule 1 on any new gate. (Sessão 2)

## Acceptance criteria

- [x] Rule written into the project gate-authoring convention (`docs/protocolos/CONVENCAO-AUTORIA-GATES.md`).
- [x] Each of the 8 untested gates has a test that breaks the guarded condition and asserts exit 1.
- [ ] The 18 existing gate tests audited for a real failing-path assertion; gaps listed. (Sessão 2)
- [x] Every gate found unable to fail is recorded as a facade with its claim downgraded — never left asserting coverage it lacks (`G_ZERO_HEADLESS`).
- [ ] Meta-gate blocks any new gate shipped without a failing-path test. (Sessão 2)
- [x] `G_ZERO_HEADLESS` output stops claiming "zero risco" beyond what it actually tests.
