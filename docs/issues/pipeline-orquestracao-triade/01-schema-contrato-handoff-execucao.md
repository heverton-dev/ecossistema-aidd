---
id: ISSUE-PIPE-0001
title: Schema Canônico de Contrato de Handoff de Execução
status: done
blocked_by: []
created: 2026-09-21
source: Relatório de Melhoria 21-09-2026 — Pipeline Unificado de Orquestração
---

# ISSUE-PIPE-0001 — Schema Canônico de Contrato de Handoff de Execução

**Deliver:** Formal JSON Schema at `componentes/compartilhado/specs/handoff-execucao.schema.json` defining the universal execution handoff interface for both evolution plans (`aidd-plan`) and triad applications (`aidd-planner`).

**Blocked by:** nothing. Start now.

## Scope

1. Define root schema with mandatory keys:
   - `versao_schema`: exact semantic version string (e.g. `"1.0.0"`).
   - `origem_plano`: `"evolucao"` (plan/tickets) or `"criacao"` (planner triad).
   - `meta`: project name, target repository, execution timestamp.
   - `fase_paralela_assincrona`: list of independent vertical slices/tickets to execute in isolated Git Worktrees.
   - `barreira_sincronizacao`: list of quality gates required to pass before merging worktree branches.
   - `fase_sequencial_sincrona`: list of ordered dependent tasks (migrations, monorepo wiring, E2E tests).
2. Define ticket/slice item schema:
   - `id`: unique string (e.g. `"TICKET-01"`).
   - `titulo`: concise imperative action.
   - `arquivos_alvo`: explicit list of relative file paths.
   - `comando_validacao`: exact test/gate command with exit code 0 expectation.
   - `isolamento`: `"git-worktree"`.
3. Zero stubs: prohibit empty arrays or placeholder values.

## Acceptance criteria

- [x] Schema file `componentes/compartilhado/specs/handoff-execucao.schema.json` exists and is valid JSON.
- [x] Schema passes `jsonschema.Draft7Validator.check_schema()`.
- [x] Positive fixture test passes validation.
- [x] Negative fixture test (empty fields, missing validation command) fails validation with clear diagnostic error.
