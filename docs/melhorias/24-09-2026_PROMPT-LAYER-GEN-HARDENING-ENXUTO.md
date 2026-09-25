# Prompt — Layer-Gen Hardening (versão enxuta)

Origem: revisão de 24/09/2026 do prompt "Meso-layer code-gen pipeline" sugerido por agente externo.
Descartado do original: Zod/Drizzle/Result-monad TS no backend (viola Lei #11), Fases 5 e 6
(Quarteto e gates já existem — PLAN-0036, `G_QUARTETO_SINE_QUA_NON`, `G_FRONTEND_LAYERS`,
`G_DISPATCH_PIPELINE_VSA`, `G_PORTAO_PROVA_QUE_MORDE`).

```text
ROLE: AIDD Lead Systems Architect & Auditor. Repo: ecossistema-aidd.
MODE: Investigation + Plan Draft only. NO code. STOP at approval (Law #7).

HARD CONSTRAINTS
- Respect Law #11: backend = Python/FastAPI + SQLite WAL + OpenAPI 3.1. Frontend = Next.js + TS + Tailwind.
- Contract types in Python = Pydantic. Frontend client types = generated from OpenAPI. No Zod/Drizzle in backend.
- Zero stubs. Zero mocks. Every claim = file:line + real command + real exit code.
- Reproduce before fixing: each phase starts with a failing test that proves the gap. No failing test = drop the phase.
- Do not duplicate existing assets. Reuse: PLANNER.json, componentes/compartilhado/specs/*.schema.json,
  gates/G_FRONTEND_LAYERS.py, gates/G_CONTRACT_ROT.py, gates/G_QUARTETO_SINE_QUA_NON.py,
  gates/G_STACK_PADRAO_OURO.py, tools/aidd-master/scripts/gates/G_AST_BOUNDED_CONTEXT.py,
  tools/aidd-master/scripts/dispatch_pipeline.py.
- Plan location: docs/planos/ (new PLAN-NNNN, next free number). Eval report: docs/melhorias/.
- Answer in PT-BR.

STEP 1 — INVESTIGATE (evidence only)
- Trace /aidd-grill -> /aidd-spec -> aidd-planner -> PLANNER.json -> engine (generator/factory/bridge).
- Answer with file:line:
  - Does PLANNER.json carry a formal OpenAPI 3.1 contract before engine dispatch? (expected: no)
  - Where does each engine get endpoint/schema info today? Free text, LLM prompt, or schema?
  - Does any engine emit a frontend API client from OpenAPI? (expected: no)
  - Flow 03 (bridge): SQLite WAL vs PostgreSQL — do generated schemas diverge? Prove with a real run.
- Run existing gates against one real generated project (e.g. proj_ctt). Record exit codes.
- Score layer-gen maturity 0-10 per layer (DB, BFF, Frontend, Contract). Each score = evidence list.
- Write docs/melhorias/<DD-MM-YYYY>_EVAL-LAYER-GEN.json.

STEP 2 — PLAN DRAFT (3 phases max)
- Phase 1 — Contract-First in Planner.
  - Planner compiles OpenAPI 3.1 (paths + Pydantic-derived schemas) into PLANNER.json before dispatch.
  - New/extended schema in componentes/compartilhado/specs/ (extend handoff-planner-to-engine.schema.json; do not fork).
  - Gate: dispatch refuses PLANNER.json without valid OpenAPI block (exit 1). Test proves bite.
- Phase 2 — Frontend client from contract.
  - Generate typed client + TanStack Query hooks via Orval from the Phase 1 OpenAPI.
  - Output only into lib/api/ or hooks/ (already allowed by G_FRONTEND_LAYERS).
  - Gate: generated client matches contract (drift = exit 1). Reuse G_CONTRACT_ROT if possible; extend, not duplicate.
- Phase 3 — DB divergence in Flow 03 (conditional).
  - Run only if Step 1 proved real SQLite/Postgres divergence.
  - Scope: bridge migration output only. Deterministic migration diff check. Seed validation.
  - If Step 1 found no divergence: record "sem evidência" and drop phase.
- Each phase: files touched, failing test first, gate, acceptance criteria, rollback.

OUTPUT (console, PT-BR, short)
- Score per layer + top 3 bottlenecks (with file:line).
- Path of eval JSON.
- Plan overview (phases kept/dropped + reason).
- End with exactly: "Aprova este plano para seguir com a execução via /orchestrate?"
```
