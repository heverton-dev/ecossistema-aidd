---
id: ISSUE-PIPE-0004
title: Compilador de Tickets de Planos Markdown para Handoff JSON
status: ready-for-agent
blocked_by: [ISSUE-PIPE-0001]
created: 2026-09-21
source: Relatório de Melhoria 21-09-2026 — Pipeline Unificado de Orquestração
---

# ISSUE-PIPE-0004 — Compilador de Tickets de Planos Markdown para Handoff JSON

**Deliver:** Deterministic CLI parser at `scripts/compilador_tickets_plano.py` that ingests markdown plan initiatives from `docs/planos/PLAN-<NNNN>-<slug>/` and compiles them into a validated `handoff_evolution.json`.

**Blocked by:** `ISSUE-PIPE-0001`.

## Scope

1. Parse directory `docs/planos/PLAN-<NNNN>-<slug>/`.
2. Extract initiative metadata from `00-PROCESSO-E-DECISOES.md`.
3. Extract work items from `01-*.md`, `02-*.md` etc., identifying tickets structured by `/aidd-tickets`.
4. Perform DAG topological sort on dependencies (`blocked_by`).
5. Assign tickets with `blocked_by: []` and disjoint `arquivos_alvo` to `fase_paralela_assincrona`.
6. Assign dependent tickets to `fase_sequencial_sincrona`.
7. Write output to `docs/planos/PLAN-<NNNN>-<slug>/handoff_evolution.json`.
8. Validate generated output against `handoff-execucao.schema.json`.

## Acceptance criteria

- [ ] CLI command `python scripts/compilador_tickets_plano.py --plano <path>` compiles plan into JSON.
- [ ] Compiles real plan fixture without loss of criteria or target files.
- [ ] Validates generated JSON through `gates/G_PIPELINE_HANDOFF.py` with exit 0.
- [ ] Exits 1 if input markdown contains unresolvable cycles or missing validation commands.
