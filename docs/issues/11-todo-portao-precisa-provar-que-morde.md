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

**Todos os 26 gates em gates/ possuem teste de reprovação real (exit 1) comprovado:**

| Grupo | Quantidade | Status |
|---|---|---|
| Gates sem teste inicial (Escopo 2) | 8 | 100% com teste de reprovação (exit 1) comprovado |
| Gates com testes auditados (Escopo 3) | 18 | 100% com teste de reprovação (exit 1) comprovado |
| Meta-Gate de Autoria (Escopo 4) | 1 (`G_PORTAO_PROVA_QUE_MORDE.py`) | 100% ativo, testado (`test_g_portao_prova_que_morde.py`), integrado ao pre-commit e `ecossistema.py` |

## Scope

1. [x] Write the rule: every gate ships with a test that **breaks the guarded condition
   and asserts exit 1**. Passing-path tests alone do not satisfy it.
   - Entregue em `docs/protocolos/CONVENCAO-AUTORIA-GATES.md`, `AGENTS.md` (Lei #13) e `docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md`.
2. [x] Apply to the 8 gates above. Start with `G_ZERO_HEADLESS` and `G_TESTES_REAIS`.
   - Entregue com reprodução real via hooks e suíte pytest dedicada.
3. [x] Audit the 18 gates that **do** have tests: confirm each exercises the failing
   path. A test asserting only exit 0 carries the same defect, just hidden. (Entregue na Sessão 2)
   - Diagnosticados 10 gates com gaps de teste de reprovação ponta a ponta (eram puramente unitários ou assertavam exit 0) e 1 teste falso com asserção inútil (`G_ESCRITOR_ATOMICO` assertava `os.path.isfile`).
   - Todos os 10 testes foram atualizados com asserções estritas de reprovação (`exit 1` / `code == 1` / `returncode == 1`).
4. [x] Add a meta-gate enforcing rule 1 on any new gate. (Entregue na Sessão 2)
   - Entregue `gates/G_PORTAO_PROVA_QUE_MORDE.py`, `gates/test_g_portao_prova_que_morde.py`, hook `g-portao-prova-que-morde` no `.pre-commit-config.yaml` e lista `_GATES_AUDIT` em `ecossistema.py`.

## Acceptance criteria

- [x] Rule written into the project gate-authoring convention (`docs/protocolos/CONVENCAO-AUTORIA-GATES.md`).
- [x] Each of the 8 untested gates has a test that breaks the guarded condition and asserts exit 1.
- [x] The 18 existing gate tests audited for a real failing-path assertion; gaps listed and corrigidos.
- [x] Every gate found unable to fail is recorded as a facade with its claim downgraded — never left asserting coverage it lacks (`G_ZERO_HEADLESS`).
- [x] Meta-gate blocks any new gate shipped without a failing-path test (`gates/G_PORTAO_PROVA_QUE_MORDE.py`).
- [x] `G_ZERO_HEADLESS` output stops claiming "zero risco" beyond what it actually tests.

