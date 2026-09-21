# Canonical AIDD Governance & Directives

> **Governance Standard:** Zero Stubs, Strict Determinism, Context Optimization (<1500 tokens), Absolute Cache Invariance.

---

## 1. Core Execution Constraints

- **Thinking constraint:** Think strictly in compact English. No meta-deliberation. Focus only on architectural invariants and edge cases. Under 150 words of reasoning.
- **Execution limit:** Resolve tasks in 3 to 5 discrete steps. Stop and request confirmation if more steps are required.
- **Output format (Rule 10):** Silent executor. Return code edits and 1-line execution status only. Do not explain what was changed unless explicitly asked. Do not repeat code in conversational reply.
  - When prose is requested, strictly shape answers as:
    1. One top sentence stating what to do or what happened. No preamble.
    2. Short bulleted body. Facts, numbers, findings. No narration of steps taken.
    3. One closing suggestion block, separated from the body.
  - **Token budget:** Target ≤300 tokens for normal answer, ≤600 for technical answer.
- **Editing rule:** Always use exact search/replace block tools (`replace_file_content`). Never dump entire rewritten files into output.
- **Bash rule:** Always pipe verbose commands to tail/grep. E.g., `pytest 2>&1 | tail -n 25`. Never dump raw bundle outputs, logs, or lockfiles into context.
- **Graph-first:** Query knowledge graph (`code-review-graph` MCP) before Grep, Glob, or full file reads.
- **Docs Ingestion constraint:** Read ONLY living canonical documentation (`docs/protocolos/`, `AGENTS.md`, `MEMORY.md`).

---

## 2. Inviolable Laws

1. **Determinism First:** Use deterministic scripts, AST, regex, or JSON Schema. Never use LLM for mechanical tasks.
2. **Binary Quality:** Every change must pass Quality Gates (`python ecossistema.py audit`, exit 0 = pass, exit 1 = block).
3. **Structured Persistence:** Persist state in audit files (JSON, SQLite), never in volatile conversation memory.
4. **Extreme Token Economy:** Minimalist prompts, compact English core rules, dense PT-BR user responses only when requested.
5. **Zero Stubs / Zero Mocks:** 100% functional, typed production code with real tests.
6. **Agnostic Supremacy:** Zero vendor lock-in across OS, harness, and LLM providers.
7. **Developer in Control:** Strictly sequential, interactive executions. Zero invisible headless background subagents.
8. **Label Honesty:** Never claim certification or test coverage beyond real automated test results.
9. **Tool Testing Discipline:** Follow the 5-step cycle (auto-fix, commit & push, clean target, clean execute, update report).
10. **Quarteto Sine Qua Non Dinâmico:** Every project generated or evolved MUST natively expose 4 pillars: Swagger Studio (`/docs`), Webhook Studio (`/webhooks`), MCP Studio (`/mcp`) and User Guide (`/docs/guia`).
11. **Padrão-Ouro de Stack Tecnológica:** Frontend in Next.js + TypeScript + Tailwind CSS; Backend in Python Modular VSA + SQLite WAL + OpenAPI 3.1.
12. **Anti-Docs Rot & Canonical Ingestion:** Never ingest stale docs. Living docs reside in `docs/protocolos/` and active schemas.
13. **Todo Portão Deve Provar que Morde:** Every quality gate must prove it blocks invalid inputs with exit 1 in automated tests.

---

## 3. The 3 Canonical Creation Flows (A Tríade Canônica)

- **FLUXO 01 (`/pure`):** `[FORGE -> PLANNER] -> GENERATOR -> [MASTER -> ENTERPRISE -> OPS]` (From Scratch, TDD Red-Green).
- **FLUXO 02 (`/aidd-open` ou `/factory`):** `[FORGE -> PLANNER] -> FACTORY -> [MASTER -> ENTERPRISE -> OPS]` (Open-Source Engines).
- **FLUXO 03 (`/freedom`):** `[FORGE -> PLANNER] -> BRIDGE -> [MASTER -> ENTERPRISE -> OPS]` (Low-Code Lock-in Eradication).

Convergence Funnel: All flows converge into `aidd-master` (Modular VSA) -> `aidd-enterprise` (SHA-256) -> `aidd-ops` (VPS Docker Compose).

---

## 4. Procedural Skills

- `/aidd-grill`: Socratic interview protocol to resolve edge cases and invariants before code modification.
- `/aidd-spec`: Deterministic technical specification generator with binary acceptance criteria.
- `/aidd-tickets`: Atomic tracer-bullet task decomposition with bounded blast radius.
- `/aidd-tdd`: Strict Red-Green-Refactor cycle with zero stubs invariant across all language runtimes.
- `/aidd-diagnose`: 5-phase scientific fault triage integrated with `code-review-graph`.
- `/aidd-handoff`: Compact session context serialization directly into `secoes/`.
