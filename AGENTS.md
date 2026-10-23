# Canonical AIDD Ecosystem Governance & Agent Directives

> **Repository:** https://github.com/heverton-dev/ecossistema-aidd
> **Governance Standard:** Zero Stubs, Strict Determinism, Context Optimization (<2000 tokens), Absolute Cache Invariance.
> **Full Reference:** `docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md`
> **Glossary:** `CONTEXT.md` — domain terms; read before using ciclo, fase, plano, sessão or ticket.

---

## 1. Core Execution Constraints

- **Thinking:** Compact English, no meta-deliberation, architectural invariants only, < 150 words.
- **Execution limit:** 3-5 steps. Stop and ask confirmation if more required.
- **Rule 10 (Formato de Resposta):** Silent executor. Code edits and 1-line execution status only. When prose is requested: 1. Top sentence (what happened), 2. Bullets (Changed -> Why -> Impact), 3. Closing suggestion. Target <= 300 tokens normal, <= 600 technical.
- **Editing & Bash:** Exact block replacement tools. Never dump whole files. Pipe verbose bash to tail/grep (`pytest 2>&1 | tail -n 25`).
- **Long-task & Loop:** Run tasks > 2 min in background. Stop on `PIPELINE_FINISHED rc=0` or `[TERMINATION_SIGNAL]`.
- **Graph-first (Lei #14):** Always query `codebase-memory-mcp` before Grep, Glob, or full file reads.

---

## 2. Inviolable Laws (Reference: `docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md`)

1. **Determinism First:** AST, regex, scripts, JSON Schema. Never use LLM for mechanical tasks.
2. **Binary Quality:** Every change must pass Quality Gates (`python ecossistema.py audit`, exit 0).
3. **Structured Persistence:** State in JSON/SQLite audit files, never in volatile memory.
4. **Extreme Token Economy:** Minimal prompts, compact core rules, dense PT-BR on demand (< 2000 tokens).
5. **Zero Stubs / Zero Mocks:** 100% functional, typed production code with real automated tests.
6. **Agnostic Supremacy:** Zero vendor lock-in across OS, harness, and LLM providers.
7. **Developer in Control:** Strictly sequential, interactive executions. Zero headless background agents.
8. **Label Honesty:** Never claim certification or coverage beyond real automated test results.
9. **Tool Testing Discipline:** 5-step cycle: auto-fix, commit/push, clean target, run, update E2E.
10. **Quarteto Sine Qua Non Dinâmico (Lei #10):** OpenAPI (`/api`), Webhook (`/webhook`), MCP (`/mcp`), Docs (`/docs`).
11. **Padrão-Ouro de Stack:** Frontend: TanStack Start/Router + React + TS + Tailwind (Light Mode Sovereign, WCAG 2.2 AA). Next.js abolished. Backend: Python + SQLite WAL. Mandatory `/impeccable-full`.
12. **Anti-Docs Rot & Canonical Ingestion:** Zero dead links, zero emojis in docs/rules.
13. **Todo Portão Deve Provar que Morde:** Automated negative test asserting exit 1 under violation.
14. **Graph-First Obrigatório:** Query `codebase-memory-mcp` before file reads.

---

## 3. The 3 Canonical Creation Flows

Originate from **`aidd-forge`** + **`aidd-planner`** (`PLANNER.json`), converging into **`aidd-master`** -> **`aidd-enterprise`** -> **`aidd-ops`**:
- **FLUXO 01 — `aidd-pure` (`/pure`):** Green-field app with 8-phase TDD (`python ecossistema.py pure`).
- **FLUXO 02 — `aidd-open` (`/aidd-open` ou `/factory`):** Open-source engine curation (`python ecossistema.py open`).
- **FLUXO 03 — `aidd-freedom` (`/freedom`):** Lock-in removal (Lovable/v0/Bolt) to PostgreSQL (`python ecossistema.py freedom`).
- **Pipelines & Dispatch:** `/run-plan`, `/pipeline` (worktrees + barrier), `/dispatch`, `/aidd-dispatch` (DAG batches), `/audit-4f`, `/aidd-auditor` (4-phase audit), `/evolucao`, `/aidd-evolucao` (evolution plan).

**Universal Interoperability:** Any `/pure`, `/open`, `/aidd-open`, `/freedom`, `/factory`, `/bridge`, `/run-plan`, `/pipeline`, `/dispatch`, `/audit-4f`, `/evolucao`, `/sessao`, `/id` is immediately executed.

---

## 4. Architecture & Context Dispatch

Universal rules apply everywhere. Editing inside a slice: read slice `AGENTS.md` (< 400 tokens) before tool `AGENTS.md`. Slices registered in `modulos/04-nucleo-compartilhado/contracts/MAPA-FATIAS.json`:

| Slice | Slice rules | Tool rules | Scope |
|---|---|---|---|
| 01-governanca-e-qualidade | `modulos/01-governanca-e-qualidade/AGENTS.md` | `core/aidd-forge/AGENTS.md`, `core/aidd-planner/AGENTS.md` | Bootstrap, piece warehouse, planning engine |
| fluxo-01-pure | `modulos/02-triade-motores/fluxo-01-pure/AGENTS.md` | `core/aidd-pure/AGENTS.md` | 8-phase software generation factory |
| fluxo-02-open | `modulos/02-triade-motores/fluxo-02-open/AGENTS.md` | `core/aidd-open/AGENTS.md` | Multi-service application and integration |
| fluxo-03-freedom | `modulos/02-triade-motores/fluxo-03-freedom/AGENTS.md` | `core/aidd-freedom/AGENTS.md` | Low-code (Lovable/v0/Bolt) VPS packager |
| blindagem-enterprise | `modulos/03-plataforma-e-entrega/blindagem-enterprise/AGENTS.md` | `aidd-enterprise/AGENTS.md` | Mission-critical SHA-256 components |
| fatiamento-master | `modulos/03-plataforma-e-entrega/fatiamento-master/AGENTS.md` | `aidd-master/AGENTS.md` | Modular Vertical Slice architecture |
| operacoes-ops | `modulos/03-plataforma-e-entrega/operacoes-ops/AGENTS.md` | `aidd-ops/AGENTS.md` | Agentic infrastructure orchestration |

---

## 5. MCP Tools: codebase-memory-mcp

Query the graph BEFORE file scanning. Query the slice subgraph first: editing inside a slice, query its `vsa-<domain>` project before the whole-repo graph (smaller blast radius, fewer tokens).
- Subgraphs: `vsa-aidd-nucleo`, `vsa-modulo-governanca`, `vsa-triade-fluxo-pure`, `vsa-triade-fluxo-open`, `vsa-triade-fluxo-freedom`, `vsa-modulo-plataforma-ops`.
- Tools: `search_graph`, `trace_path`, `query_graph`, `get_architecture`, `detect_changes`. Reindex: `python scripts/cli_modularizacao_vsa.py index-subgraphs`.

---

## 6. Procedural Engineering Skills (`componentes/compartilhado/skills/`)

Canonical workflow skills available across all harnesses:
- `/aidd-grill`: Socratic interview protocol resolving edge cases before coding.
- `/aidd-grill-docs`: Architecture-grounded interview anchored in `MEMORY.md` and repository laws.
- `/aidd-spec`: Technical specification with binary acceptance criteria.
- `/aidd-tickets`: Vertical-slice tickets with `Blocked by`.
- `/aidd-tdd`: Agreed seams, then Red -> Green loop; refactor at review; zero stubs, polyglot.
- `/aidd-diagnose`: 5-phase scientific fault triage integrated with `codebase-memory-mcp`.
- `/aidd-visual-maps`: Visual maps of piece types from parts catalog (`python ecossistema.py visual-maps gerar|check`).
- `/aidd-handoff`: Compact session context serialization directly into `secoes/`.
- `/aidd-session`: Deterministic session ID and metadata persistence in `secoes/`.
- `/aidd-agent-writing`: Writing guide for skills, AGENTS.md, CLAUDE.md.
- `/aidd-retro`: Session retro; mistakes become proposed gates or review rules.
- `/aidd-reexplain`: Re-explain last message in plain PT-BR using the glossary above.
- `/aidd-delivery`: Delivery template with before/after evidence and real exit codes.
- `/aidd-wizard`: Bash wizard for steps only human can perform.
- `/aidd-impeccable-full`: Full Impeccable UI craft lifecycle (init -> document -> critique -> audit -> polish -> harden -> extract).
