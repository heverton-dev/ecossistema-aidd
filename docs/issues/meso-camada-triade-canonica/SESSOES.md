# Sessões de Execução — Ordem Obrigatória

Iniciativa: **Meso-Camada da Tríade Canônica (`aidd-dispatch-pipeline`)**

Copy the prompt block, open a new conversation/session, paste and execute. Mark the checkbox upon completion.

---

## Sessão 1 — ISSUE-MESO-0001: Schema Canônico do Grafo Topológico VSA

**Touches:** `componentes/compartilhado/specs/vsa-topological-dispatch.schema.json` · **Blocked by:** nothing

```bash
Execute docs/issues/meso-camada-triade-canonica/01-schema-grafo-topologico-vsa.md.

Create canonical JSON schema componentes/compartilhado/specs/vsa-topological-dispatch.schema.json for deterministic VSA slice dispatch.
Must enforce:
- Schema versioning 1.0.0, target flow (fluxo_01_generator, fluxo_02_factory, fluxo_03_bridge).
- Array of slices: slice_id, modulo_ddd, dependencias, isolamento ('git-worktree'), arquivos_esperados.
- Validation barrier per slice: comandos_teste, quality_gates.
- Master convergence block with target branch and fast-forward strategy.
- Zero stubs allowed: reject empty arrays or missing validation commands.
- Verify schema validity using python jsonschema module. Stop and ask before commit.
```

---

## Sessão 2 — ISSUE-MESO-0002: Compilador de Grafo Topológico VSA no aidd-planner

**Touches:** `tools/aidd-planner/aidd_planner/core/planner_engine.py`, `tools/aidd-planner/aidd_planner/cli.py`, `tools/aidd-planner/tests/test_vsa_compiler.py` · **Blocked by:** Sessão 1

```bash
Execute docs/issues/meso-camada-triade-canonica/02-compilador-dag-vsa-planner.md.

Implement compilar_grafo_topologico_vsa() in tools/aidd-planner/aidd_planner/core/planner_engine.py.
Must enforce:
- Parse PLANNER.json (ddd_bounded_contexts, bdd_cenarios, payload_especifico_fluxo).
- Map each Bounded Context to an independent VSA slice with clear dependencies.
- Apply Kahn's topological sort to detect and reject cyclic dependencies deterministically.
- Populate validation commands and required gates per slice.
- Add CLI export command: 'python -m aidd_planner.cli export-dispatch <planner.json>'.
- Add comprehensive unit tests in tools/aidd-planner/tests/test_vsa_compiler.py.
- Stop and ask before commit.
```

---

## Sessão 3 — ISSUE-MESO-0003: Quality Gate G_DISPATCH_PIPELINE_VSA com Prova que Morde

**Touches:** `gates/G_DISPATCH_PIPELINE_VSA.py`, `tests/test_gate_dispatch_pipeline_vsa.py`, `ecossistema.py` · **Blocked by:** Sessão 1, Sessão 2

```bash
Execute docs/issues/meso-camada-triade-canonica/03-quality-gate-dispatch-vsa-morde.md.

Implement root quality gate gates/G_DISPATCH_PIPELINE_VSA.py adhering to Law #1, #2, #13.
Must enforce:
- Validate any incoming VSA dispatch manifest against vsa-topological-dispatch.schema.json.
- Assert exit 0 on compliant dispatch DAG.
- Assert exit 1 on cycles, stubs, unresolvable slice targets, or missing gates.
- Create automated test tests/test_gate_dispatch_pipeline_vsa.py asserting failure on synthetic violations (proves gate bites per Law #13).
- Register gate in gates list in ecossistema.py.
- Stop and ask before commit.
```

---

## Sessão 4 — ISSUE-MESO-0004: Motor de Despacho de Fatias em Git Worktrees

**Touches:** `tools/aidd-master/scripts/dispatch_pipeline.py` · **Blocked by:** Sessão 3

```bash
Execute docs/issues/meso-camada-triade-canonica/04-motor-dispatch-pipeline-worktrees.md.

Build deterministic dispatch engine tools/aidd-master/scripts/dispatch_pipeline.py.
Must enforce:
- Ingest validated VSA_DISPATCH.json manifest.
- Group independent topological slices into concurrent batches.
- Spawn ephemeral Git Worktrees: 'git worktree add -b slice/<id> .worktrees/<id>'.
- Ensure complete filesystem isolation per slice.
- Safely clean up all temporary worktrees ('git worktree remove --force') on completion, error, or interrupt.
- Stop and ask before commit.
```

---

## Sessão 5 — ISSUE-MESO-0005: Roteadores Especialistas para as 3 Engines da Tríade

**Touches:** `tools/aidd-master/scripts/engine_router.py`, `tools/aidd-master/tests/test_engine_router.py` · **Blocked by:** Sessão 4

```bash
Execute docs/issues/meso-camada-triade-canonica/05-roteadores-especialistas-engines-triade.md.

Implement polymorphic engine router tools/aidd-master/scripts/engine_router.py.
Must enforce:
- Dispatch Fluxo 01 (Pure): trigger aidd-generator with scoped TDD Red-Green arguments for the slice.
- Dispatch Fluxo 02 (Open): trigger aidd-factory with open-source integration arguments for the slice.
- Dispatch Fluxo 03 (Freedom): trigger aidd-bridge with low-code extraction and schema mapping arguments.
- Zero mock entities; inject real slice attributes from Bounded Contexts.
- Write unit tests in tools/aidd-master/tests/test_engine_router.py.
- Stop and ask before commit.
```

---

## Sessão 6 — ISSUE-MESO-0006: Barreira de Validação e Fusão Convergente no aidd-master

**Touches:** `tools/aidd-master/scripts/vsa_join_barrier.py`, `tools/aidd-master/tests/test_vsa_join_barrier.py` · **Blocked by:** Sessão 5

```bash
Execute docs/issues/meso-camada-triade-canonica/06-barreira-validacao-convergencia-master.md.

Implement synchronous validation barrier and merge tools/aidd-master/scripts/vsa_join_barrier.py.
Must enforce:
- Run slice-level unit tests and local quality gates inside worktree.
- Verify zero filesystem boundary leaks (slice cannot edit outside src/slices/<id>).
- On pass (exit 0), perform fast-forward merge of slice branch into main development branch.
- Aggregate slice routers into aidd-master Modular Monolith main router.
- Validate Quarteto Sine Qua Non endpoints (/docs, /webhooks, /mcp, /docs/guia).
- Write unit tests in tools/aidd-master/tests/test_vsa_join_barrier.py.
- Stop and ask before commit.
```

---

## Sessão 7 — ISSUE-MESO-0007: Integração no Orquestrador Síncrono e CLI

**Touches:** `scripts/orquestrador_sincrono.py`, `ecossistema.py` · **Blocked by:** Sessão 6

```bash
Execute docs/issues/meso-camada-triade-canonica/07-integracao-orquestrador-sincrono-cli.md.

Refactor scripts/orquestrador_sincrono.py and update ecossistema.py.
Must enforce:
- Eliminate hardcoded entity mocks (RegistroPrincipal dicts) in orquestrador_sincrono.py.
- Wire etapa_03_engine() to dispatch_pipeline.py using real compiled DAG.
- Wire etapa_04_master() to vsa_join_barrier.py.
- Add central CLI command: 'python ecossistema.py dispatch --planner <planner.json>'.
- Preserve all existing aliases (pure, open, freedom, run-fluxo).
- Test with 'python ecossistema.py pure --dry-run' and verify clean execution.
- Stop and ask before commit.
```

---

## Sessão 8 — ISSUE-MESO-0008: Skill Canônica Multi-Harness e Encadeamento de Intake

**Touches:** `componentes/compartilhado/skills/aidd-dispatch-runner/`, `componentes/compartilhado/skills/aidd-grill/SKILL.md`, `componentes/compartilhado/skills/aidd-spec/SKILL.md`, `componentes/compartilhado/skills/aidd-planner-runner/SKILL.md`, `AGENTS.md`, `GEMINI.md` · **Blocked by:** Sessão 7

```bash
Execute docs/issues/meso-camada-triade-canonica/08-skills-triade-intake-grill-spec-dispatch.md.

Create and distribute multi-harness skill aidd-dispatch-runner and cross-link intake flow.
Must enforce:
- Create componentes/compartilhado/skills/aidd-dispatch-runner/SKILL.md with clear triggers (/dispatch, dispatch).
- Cross-link intake chain: /aidd-grill -> /aidd-spec -> aidd-planner -> aidd-dispatch-pipeline.
- Sync skills across all 7 harnesses using 'python ecossistema.py components sync --tipo skills'.
- Verify distribution with 'python ecossistema.py components verify --tipo skills'.
- Update AGENTS.md and GEMINI.md documenting Meso-Layer canonical rules.
- Stop and ask before commit.
```
