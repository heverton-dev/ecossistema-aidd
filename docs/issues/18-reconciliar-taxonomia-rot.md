---
id: ISSUE-0018
title: Reconciliar as 6 categorias de ROT que duplicam portões existentes
status: closed
blocked_by: []
created: 2026-09-19
closed: 2026-09-20
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

## Decisions and Evidence for the Six Duplicated Categories

1. **`G_ARCH_DRIFT` (Architecture Rot) — REJECT NEW GATE:**
   - **Decision:** Deepen existing gate `G_ARQUITETURA_DELIVERABLE.py` and fold into open ticket **ISSUE-0004**.
   - **Evidence:** `gates/G_ARQUITETURA_DELIVERABLE.py` already performs AST-based boundary enforcement (forbids SQL outside `infrastructure/`, enforces domain isolation, and clean routes). Frontend boundary is guarded by `gates/G_FRONTEND_LAYERS.py`. Cross-tool drift is guarded by `gates/G_DRIFT_ANALYZER.py` and `gates/G_DRIFT_NUCLEO_COMPARTILHADO.py`. ISSUE-0004 is already open specifically to clear real architecture violations and restore permanent pre-commit enforcement.

2. **`G_DEPENDENCY_ROT` (Dependency Rot) — REJECT NEW GATE:**
   - **Decision:** 100% covered by existing gates **`G_DEPENDENCIAS_PIN_HASH.py`** and **`G_SUPPLY_CHAIN.py`**.
   - **Evidence:** `gates/G_DEPENDENCIAS_PIN_HASH.py` enforces exact version pins (`==`), SHA-256 hashes in lockfiles, and CI `--require-hashes`. `gates/G_SUPPLY_CHAIN.py` runs real `pip-audit` against PyPA/OSV advisory databases, detects critical vulnerabilities, blocks typosquatting, and forbids loose VCS/unauthenticated dependencies. Any future check (e.g. npm audit) is an incremental addition to these gates, not a new gate.

3. **`G_TEST_ROT` (Test Rot) — REJECT NEW GATE:**
   - **Decision:** Deepen **`G_TESTES_REAIS.py`** and fold into **ISSUE-0011** and **PLAN-0016 item 9**.
   - **Evidence:** `gates/G_TESTES_REAIS.py` executes real pytest suites across tools and enforces a strict skip budget via `gates/allowlist_skipped_testes.json`. Law #13 / `gates/G_PORTAO_PROVA_QUE_MORDE.py` (delivered in ISSUE-0011) already enforces that tests must break and assert `exit 1`. Mutation testing is already architected and scheduled in PLAN-0016 item 9.

4. **`G_CONTEXT_ROT` (Context Rot) — REJECT NEW GATE:**
   - **Decision:** Fold into open tickets **ISSUE-0005**, **ISSUE-0012**, and **PLAN-0022 item 4**.
   - **Evidence:** Token budget enforcement (< 2,000 tokens) and removal of rule duplication are the exact core deliverables of ISSUE-0005 (modular split of `AGENTS.md`) and ISSUE-0012 (Law #4 language and token density gate).

5. **`G_PROMPT_ROT` (Prompt Rot) — REJECT NEW GATE:**
   - **Decision:** Deepen existing **`G_DOCS_ROT.py`** and **`G_LLM_PROMPT_SHIELD.py`**, fold into **ISSUE-0012**.
   - **Evidence:** Prompt rot is documentation/rule rot applied to agent instructions. `gates/G_DOCS_ROT.py` already audits file references, living links, and canonical ingestion (Law #12). `gates/G_LLM_PROMPT_SHIELD.py` audits LLM invocation ASTs. ISSUE-0012 handles prompt language and compact rule enforcement.

6. **`G_DEAD_CODE` (Code Rot) — REJECT NEW GATE:**
   - **Decision:** Fold into open ticket **ISSUE-0007**, **PLAN-0025 item 10**, and skip budget in **`G_TESTES_REAIS.py`**.
   - **Evidence:** Dead code remediation is actively tracked per component (e.g., `SagaOrchestrator` in ISSUE-0007 / PLAN-0025 item 10). Indefinite skips are already blocked by `gates/allowlist_skipped_testes.json` in `G_TESTES_REAIS.py`.

## Status of the 4 Genuinely New Categories

The remaining four categories have no existing gate coverage and are already assigned dedicated tickets:
- **Contract Rot:** ISSUE-0014 (`G_CONTRACT_ROT.py`)
- **Env Rot:** ISSUE-0015 (`G_ENV_ROT.py`)
- **Skill Rot:** ISSUE-0016 (`G_SKILL_ROT.py`)
- **Migration Rot:** ISSUE-0017 (`G_MIGRATION_ROT.py`)

## Acceptance criteria

- [x] Each of the six categories resolved with a written decision and the gate or ticket it folds into.
- [x] Any category ruled genuinely new gets its own ticket, with the evidence showing no existing gate covers it (ISSUE-0014..0017).
- [x] The four false statements corrected in `docs/melhorias/19-09-2026_melhoria-taxonomia-prevencao-rot-ecossistema.md`.
- [x] Document status changed from "Proposta" to reflect what was accepted and what was rejected, with reasons.
- [x] No new gate created for a category an existing gate already covers.
