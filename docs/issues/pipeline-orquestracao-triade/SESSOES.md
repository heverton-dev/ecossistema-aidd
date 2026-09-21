# Sessões de Execução — Ordem Obrigatória

Iniciativa: **Pipeline de Orquestração com Acionamento Tríade e Git Worktrees**

Copy the prompt block, open a new conversation/session, paste and execute. Mark the checkbox upon completion.

---

## Sessão 1 — ISSUE-PIPE-0001: Schema Canônico de Handoff

**Touches:** `componentes/compartilhado/specs/handoff-execucao.schema.json` · **Blocked by:** nothing

```bash
Execute docs/issues/pipeline-orquestracao-triade/01-schema-contrato-handoff-execucao.md.

Create canonical JSON schema components/compartilhado/specs/handoff-execucao.schema.json for deterministic execution dispatch.
Must enforce:
- Schema versioning and target flow definition (evolution, pure, open, freedom).
- Phase separation: parallel_async_steps (partitioned into Git Worktrees) vs sequential_sync_steps (join barrier).
- Ticket schema: id, title, target_files, command_red, command_green, validation_gate.
- Zero stubs allowed: reject empty steps, placeholder strings, or missing validation commands.
- Verify schema validity using python jsonschema module. Stop and ask before commit.
```

---

## Sessão 2 — ISSUE-PIPE-0002: Quality Gate G_PIPELINE_HANDOFF

**Touches:** `gates/G_PIPELINE_HANDOFF.py`, `tests/test_gate_pipeline_handoff.py` · **Blocked by:** Sessão 1

```bash
Execute docs/issues/pipeline-orquestracao-triade/02-quality-gate-pipeline-handoff.md.

Implement root quality gate gates/G_PIPELINE_HANDOFF.py adhering to Law #1, #2, #13.
Must enforce:
- Validate any incoming handoff JSON against handoff-execucao.schema.json.
- Assert exit 0 on compliant handoff manifest.
- Assert exit 1 on missing fields, stubs, unresolvable file targets, or missing gates.
- Create automated test tests/test_gate_pipeline_handoff.py executing real failing scenarios (proves gate bites per Law #13).
- Register gate in gates list in ecossistema.py. Stop and ask before commit.
```

---

## Sessão 3 — ISSUE-PIPE-0003: Motor de Execução por Git Worktrees

**Touches:** `tools/aidd-master/scripts/orchestrator_pipeline.py` · **Blocked by:** Sessão 2

```bash
Execute docs/issues/pipeline-orquestracao-triade/03-motor-execucao-worktrees-join-barrier.md.

Build deterministic pipeline runner tools/aidd-master/scripts/orchestrator_pipeline.py.
Must enforce:
- Ingest validated handoff JSON manifest.
- For parallel_async_steps: create ephemeral git worktrees via 'git worktree add -b <branch> <path>', run tests/edits in isolated tree, assert zero conflict.
- Join Barrier: execute required Quality Gates on each branch before merge.
- For sequential_sync_steps: rebase and merge validated branches to target, run migrations, global integration test suite.
- Clean up all temporary worktrees ('git worktree remove --force') on both success and failure.
- Stop and ask before commit.
```

---

## Sessão 4 — ISSUE-PIPE-0004: Compilador de Tickets do Plan

**Touches:** `scripts/compilador_tickets_plano.py` · **Blocked by:** Sessão 1

```bash
Execute docs/issues/pipeline-orquestracao-triade/04-compilador-tickets-plano-para-handoff.md.

Implement deterministic CLI parser scripts/compilador_tickets_plano.py.
Must enforce:
- Parse docs/planos/PLAN-<NNNN>-<slug>/ initiative directories.
- Read 00-PROCESSO-E-DECISOES.md and front work items (01-*.md, 02-*.md).
- Extract atomic tracer-bullet tickets structured by /aidd-tickets.
- Identify independent tickets (async) vs dependent tickets (sync) using topological DAG sort.
- Output validated handoff_evolution.json compliant with handoff-execucao.schema.json.
- Stop and ask before commit.
```

---

## Sessão 5 — ISSUE-PIPE-0005: Exportador Nativo do aidd-planner

**Touches:** `tools/aidd-planner/src/core/planner_engine.py`, `tools/aidd-planner/src/aidd_planner/cli.py` · **Blocked by:** Sessão 1

```bash
Execute docs/issues/pipeline-orquestracao-triade/05-exportador-planner-para-pipeline.md.

Add native pipeline export function to aidd-planner engine.
Must enforce:
- Function exportar_para_pipeline_execucao(plano: Dict[str, Any]) -> Dict[str, Any].
- Map bounded contexts and vertical slices into parallel_async_steps worktrees.
- Map shared core integration, migration scripts, and Quarteto Sine Qua Non verification to sequential_sync_steps.
- Expose via CLI: 'python -m aidd_planner.cli export <caminho> --formato pipeline'.
- Add unit tests verifying exported shape passes G_PIPELINE_HANDOFF. Stop and ask before commit.
```

---

## Sessão 6 — ISSUE-PIPE-0006: Acionamento Tríade Universal (CLI, Slash, Skill)

**Touches:** `ecossistema.py`, `componentes/compartilhado/skills/aidd-pipeline-runner/`, harnesses · **Blocked by:** Sessão 3, 4, 5

```bash
Execute docs/issues/pipeline-orquestracao-triade/06-triade-acionamento-cli-slash-skill.md.

Wire universal triad execution dispatch across ecosystem:
1. CLI: Add 'python ecossistema.py run-plan <plano>' and 'python ecossistema.py pipeline --handoff <json>' to ecossistema.py.
2. Skill Runner: Create componentes/compartilhado/skills/aidd-pipeline-runner/SKILL.md and mirror to all 7 harnesses via python scripts/gestor_componentes.py sync --tipo skill.
3. Slash Command: Wire /run-plan and /pipeline universal interception in AGENTS.md and GEMINI.md.
Must enforce Law #6 (Agnostic Supremacy) and Law #7 (Developer in Control). Stop and ask before commit.
```

---

## Sessão 7 — ISSUE-PIPE-0007: Testes E2E e Fechamento da Iniciativa

**Touches:** `tests/test_e2e_pipeline_orquestracao.py`, `docs/issues/pipeline-orquestracao-triade/INDEX.md` · **Blocked by:** Sessão 6

```bash
Execute docs/issues/pipeline-orquestracao-triade/07-integracao-e-testes-end-to-end.md.

Run end-to-end integration and regression suite:
- Execute real synthetic plan with 20 steps (15 parallel, 5 sequential) in temporary git repository.
- Verify worktrees are created, isolation maintained, join barrier validated, clean merge executed, and all worktrees cleaned up.
- Run full ecosystem audit: 'python ecossistema.py audit'.
- Update ticket statuses to 'done' in INDEX.md. Stop and ask before commit.
```
