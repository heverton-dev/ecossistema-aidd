---
id: ISSUE-0018
title: Reconciliar as 6 categorias de ROT que duplicam portões existentes
status: ready-for-agent
blocked_by: []
created: 2026-09-19
source: docs/melhorias/19-09-2026_melhoria-taxonomia-prevencao-rot-ecossistema.md — categories 1,2,3,4,5,10
---

# ISSUE-0018 — Reconciliar as 6 categorias de ROT duplicadas

**Deliver:** each duplicated ROT category resolves into deepening an existing gate or
an existing open ticket — never into a new gate by default. Plus the source document
stops carrying four false statements.

**Blocked by:** nothing. Start now. Analysis before construction.

## Verified this session

The source document proposes 10 gates. **Six duplicate what already exists**, which
the project's own anti-NIH direction forbids:

| Proposed | Already covered by |
|---|---|
| `G_ARCH_DRIFT` | `G_ARQUITETURA_DELIVERABLE`, `G_FRONTEND_LAYERS`, `G_DRIFT_ANALYZER`, `G_DRIFT_NUCLEO_COMPARTILHADO`, ISSUE-0004 |
| `G_DEPENDENCY_ROT` | `G_DEPENDENCIAS_PIN_HASH`, `G_SUPPLY_CHAIN` |
| `G_TEST_ROT` | `G_TESTES_REAIS`, ISSUE-0011, PLAN-0016 item 9 (mutation gate, already drafted) |
| `G_CONTEXT_ROT` | ISSUE-0012, ISSUE-0005, PLAN-0022 item 4 |
| `G_PROMPT_ROT` | `G_LLM_PROMPT_SHIELD`, `G_DOCS_ROT`, ISSUE-0012 |
| `G_DEAD_CODE` | ISSUE-0007, PLAN-0025 item 10 |

**Four false statements in the source document**, each verified against the repo:

| Statement | Reality |
|---|---|
| "Lei #9 (Execução Limpa em Máquina Nova)" | Law #9 is Tool Testing Discipline. No law by that name exists |
| Architecture Rot mapped to Law #6 | Law #6 is Agnostic Supremacy (vendor lock-in), unrelated to slice boundaries |
| "combate via `sandeco-token-reduce`" | Proven inert in ISSUE-0008: nothing calls it, its availability check always fails |
| Docs Rot homologated; Law #13 exists | **Both correct.** Verified: `G_DOCS_ROT` exits 0; Law #13 present in `AGENTS.md` |

## Scope

For each of the six: decide deepen-existing, fold-into-open-ticket, or genuinely-new.
Record the decision and the evidence. Default is not "new gate".

Then correct the four statements in the source document — an uncorrected document is
exactly how documentation rots, which is the thing it proposes to prevent.

## Acceptance criteria

- [ ] Each of the six categories resolved with a written decision and the gate or ticket it folds into.
- [ ] Any category ruled genuinely new gets its own ticket, with the evidence showing no existing gate covers it.
- [ ] The four false statements corrected in `docs/melhorias/19-09-2026_melhoria-taxonomia-prevencao-rot-ecossistema.md`.
- [ ] Document status changed from "Proposta" to reflect what was accepted and what was rejected, with reasons.
- [ ] No new gate created for a category an existing gate already covers.
