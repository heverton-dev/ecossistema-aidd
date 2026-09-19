# Canonical AIDD Ecosystem Governance & Agent Directives

> **Repository:** https://github.com/heverton-dev/ecossistema-aidd
> **Governance Standard:** Zero Stubs, Strict Determinism, Context Optimization (<2000 tokens), Absolute Cache Invariance.
> **Full Reference:** `docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md`

---

## 1. Core Execution Constraints

- **Thinking constraint:** Think strictly in compact English. No meta-deliberation. Focus only on architectural invariants and edge cases. Under 150 words of reasoning.
- **Execution limit:** Resolve tasks in 3 to 5 discrete steps. Stop and request confirmation if more steps are required.
- **Output format:** Silent executor. Return code edits and 1-line execution status only. Do not explain what was changed unless explicitly asked. Do not repeat code in conversational reply.
- **Editing rule:** Always use exact search/replace block tools (`replace_file_content`). Never dump entire rewritten files into output.
- **Bash rule:** Always pipe verbose commands to tail/grep. E.g., `pytest 2>&1 | tail -n 25`. Never dump raw bundle outputs, logs, or lockfiles into context.
- **Graph-first:** Always query knowledge graph (`code-review-graph` MCP) before Grep, Glob, or full file reads.

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
9. **Tool Testing Discipline:** Follow the 5-step cycle (`docs/protocolos/PROTOCOLO-TESTES-FERRAMENTAS.md`): 1. Auto-fix bugs until 100% conformant (zero inconsistencies), 2. Git commit & push, 3. Clean target project, 4. Execute cleanly, 5. Update `docs/teste-end-to-end/` report.
10. **Quarteto Sine Qua Non Dinâmico:** Todo projeto gerado ou evoluído no ecossistema DEVE nascer nativamente com 4 pilares completos: Swagger Studio (`/swagger` ou `/docs`), Webhook Studio (`/webhooks`), MCP Studio (`/mcp`) e Guia/Documentação do Utilizador (`/docs/guia` ou `/guia`). Todas as rotas e contratos devem cobrir 100% dos módulos do sistema e atualizar-se de forma autônoma e dinâmica a cada novo módulo (ex: autenticação).
11. **Padrão-Ouro de Stack Tecnológica:** Todo fluxo (`generator`, `master`, `factory`, `bridge`) DEVE gerar o Frontend em **Next.js + TypeScript + Tailwind CSS** (Backend em Python puro + SQLite WAL, API em OpenAPI 3.1), conforme definido em `docs/protocolos/PADRAO-OURO-STACK-TECNOLOGICA.md` — padrão validado em `proj_ctt`. Só muda se o plano estruturado ou o prompt do usuário especificar outra stack de forma explícita para aquela camada; silêncio nunca é licença para gerar outra coisa (ex.: HTML Python simples só é aceitável se pedido expressamente).

---

## 3. The 3 Canonical Creation Flows (A Tríade Canônica)

Every robust application in the ecosystem originates from **`aidd-forge`** (supreme governance and rule dictatorship) and an interactive **`PRÉ-PLANO`** intake (`aidd-planner`), allowing the developer or user to derive 3 distinct specialized paths with zero friction (CLI or Slash Commands):

- **FLUXO 01 — `aidd-pure` (Do Zero Puro | Slash: `/pure`):** `[FORGE -> PLANNER] -> GENERATOR -> [MASTER -> ENTERPRISE -> OPS]`
  - Engine: `aidd-generator` (8-phase pipeline, TDD Red-Green, Monólito Modular VSA + Next.js).
  - CLI: `python ecossistema.py run-fluxo --fluxo pure`
- **FLUXO 02 — `aidd-open` (Motores Open-Source | Slash: `/open`):** `[FORGE -> PLANNER] -> FACTORY -> [MASTER -> ENTERPRISE -> OPS]`
  - Engine: `aidd-factory` (Open-source engine curation, VSA integration slices, compose).
  - CLI: `python ecossistema.py run-fluxo --fluxo open`
- **FLUXO 03 — `aidd-bridge` (Low-Code / Apps Unificadas | Slash: `/bridge`):** `[FORGE -> PLANNER] -> BRIDGE -> [MASTER -> ENTERPRISE -> OPS]`
  - Engine: `aidd-bridge` (Vendor lock-in eradication, Lovable/v0/Bolt cleanup, PostgreSQL, UI preservation).
  - CLI: `python ecossistema.py run-fluxo --fluxo bridge`

**Universal Convergence Funnel:** All 3 flows mandatorily converge into `aidd-master` (Harmonização em Monólito Modular: VSA de domínio + camada horizontal compartilhada) -> `aidd-enterprise` (SHA-256 resilience and audit) -> `aidd-ops` (VPS deployment, sops+age, and Uptime Kuma), delivering the dynamic *Quarteto Sine Qua Non* (`/swagger`, `/webhooks`, `/mcp`, `/docs`).

---

## 4. Architecture & Context Dispatch

Core rules are universal. Domain and tool-specific instructions reside in their respective directories:
- `tools/aidd-forge/AGENTS.md` -> Bootstrap, templates, and environment shielding.
- `tools/aidd-generator/AGENTS.md` -> 8-phase software generation factory.
- `tools/aidd-master/AGENTS.md` -> Modular Vertical Slice architecture.
- `tools/aidd-enterprise/AGENTS.md` -> Mission-critical SHA-256 injected components.
- `tools/aidd-ops/AGENTS.md` -> Agentic infrastructure meta-orchestration.
- `tools/aidd-factory/AGENTS.md` -> Multi-service application & integration code generator.
- `tools/aidd-bridge/` -> Low-code (Lovable/v0/Bolt) VPS packager.

---

## 5. MCP Tools: code-review-graph

Query the graph BEFORE file scanning:
- `detect_changes_tool`: Analyze change blast radius and risk score.
- `get_review_context_tool`: Token-efficient code snippets.
- `get_impact_radius_tool` / `get_affected_flows_tool`: Trace affected paths.
- `query_graph_tool`: Trace callers, callees, imports, tests.

---

## 6. Procedural Engineering Skills (`componentes/compartilhado/skills/`)

Canonical workflow skills available across all harnesses to eliminate vibe coding and ensure rigorous pre-code alignment:
- `/aidd-grill`: Socratic interview protocol to resolve edge cases and invariants before code modification.
- `/aidd-grill-docs`: Architecture-grounded questioning anchored in `MEMORY.md` and repository laws.
- `/aidd-spec`: Deterministic technical specification generator with binary acceptance criteria.
- `/aidd-tickets`: Atomic tracer-bullet task decomposition with bounded blast radius.
- `/aidd-tdd`: Strict Red-Green-Refactor cycle with zero stubs invariant across all language runtimes.
- `/aidd-diagnose`: 5-phase scientific fault triage integrated with `code-review-graph`.
- `/aidd-handoff`: Compact session context serialization directly into `secoes/`.
