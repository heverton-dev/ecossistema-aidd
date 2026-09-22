---
id: ISSUE-MESO-0001
title: Schema Canônico do Grafo Topológico VSA de Despacho
status: done
blocked_by: []
created: 2026-09-21
source: Relatório de Melhoria 21-09-2026 — Meso-Camada da Tríade Canônica
---

# ISSUE-MESO-0001 — Schema Canônico do Grafo Topológico VSA de Despacho

**Deliver:** Formal JSON Schema at `componentes/compartilhado/specs/vsa-topological-dispatch.schema.json` defining the deterministic contract for Vertical Slice Architecture (VSA) DAG dispatch across Triad engines.

**Blocked by:** nothing. Start now.

## Scope

1. Create `componentes/compartilhado/specs/vsa-topological-dispatch.schema.json` compliant with JSON Schema Draft-07.
2. Define root structure:
   - `versao_schema`: string enum `["1.0.0"]`.
   - `projeto_slug`: string regex `^[a-z0-9_-]+$`.
   - `fluxo_alvo`: string enum `["fluxo_01_generator", "fluxo_02_factory", "fluxo_03_bridge"]`.
   - `grafo_fatias`: array of slice descriptors:
     - `slice_id`: string (e.g. `slice_auth`, `slice_pedidos`).
     - `modulo_ddd`: string matching Bounded Context name.
     - `dependencias`: array of strings (`slice_id` references forming a valid DAG).
     - `isolamento`: enum `["git-worktree"]`.
     - `arquivos_esperados`: array of string paths (e.g. `src/slices/<nome>`).
     - `barreira_validacao`: object containing `comandos_teste` (array of strings) and `quality_gates` (array of strings).
   - `convergencia_master`: object declaring target branch (`master`/`main`), fast-forward merge strategy, and post-merge suite.
3. Zero stubs: reject empty arrays or placeholder values.

## Acceptance criteria

- [x] File `componentes/compartilhado/specs/vsa-topological-dispatch.schema.json` exists and is valid JSON.
- [x] Schema compiles without error in `jsonschema.Draft7Validator.check_schema()`.
- [x] Valid dispatch manifest passes validation.
- [x] Invalid dispatch manifest (cyclic dependency or missing validation command) fails validation with actionable error.
