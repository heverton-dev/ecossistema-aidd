# Canonical AIDD Ecosystem Governance & Agent Directives

> **Repository:** https://github.com/heverton-dev/ecossistema-aidd
> **Governance Standard:** Zero Stubs, Strict Determinism, Context Optimization (<2000 tokens), Absolute Cache Invariance.
> **Full Reference:** `docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md`

---

## 1. Core Execution Constraints

- **Thinking constraint:** Think strictly in compact English. No meta-deliberation. Focus only on architectural invariants and edge cases. Under 150 words of reasoning.
- **Execution limit:** Resolve tasks in 3 to 5 discrete steps. Stop and request confirmation if more steps are required.
- **Output format (Rule 10 — Formato de Resposta):** Silent executor. Return code edits and 1-line execution status only. Do not explain what was changed unless explicitly asked. Do not repeat code in conversational reply. (Distinct from Lei #10 (Quarteto).)
  - When prose is requested, strictly shape answers as:
    1. One top sentence stating what to do or what happened. No preamble.
    2. Short bulleted body. Facts, numbers, findings. No narration of steps taken.
    3. One closing suggestion block, separated from the body.
    - Forbidden: polite greetings, restating the request, recapping what was just said, listing options without a recommendation, unexplained jargon.
  - **Token budget — decide before writing, not after:** target ≤300 tokens for a
    normal answer, ≤600 for a technical one (code/tables). This is a pre-generation
    limit, not a post-hoc filter — plan the answer's length before writing the first
    word. A hook that blocks and forces a rewrite after the fact already cost the
    tokens of the rejected draft; treat any such block as a signal you planned wrong,
    not as the mechanism meant to enforce this.
- **Editing rule:** Always use exact search/replace block tools (`replace_file_content`). Never dump entire rewritten files into output.
- **Bash rule:** Always pipe verbose commands to tail/grep. E.g., `pytest 2>&1 | tail -n 25`. Never dump raw bundle outputs, logs, or lockfiles into context.
- **Graph-first:** Always query knowledge graph (`code-review-graph` MCP) before Grep, Glob, or full file reads.
- **Docs Ingestion constraint:** Read ONLY living canonical documentation (`docs/protocolos/`, `AGENTS.md`, `MEMORY.md`). Never ingest historical reports, superseded manuals, or past session logs as system truths.

---

## 2. Inviolable Laws

1. **Determinism First:** Use deterministic scripts, AST, regex, or JSON Schema. Never use LLM for mechanical tasks.
   - Portão: gates/G_DETERMINISMO_LEI_1.py (provado)
   - Portão: gates/G_PIPELINE_HANDOFF.py (provado)
   - Portão: gates/G_DISPATCH_PIPELINE_VSA.py (provado)
   - Portão: gates/G_SYNC_CMD_ROT.py (provado) — forma canônica `components sync --tipo todos` e aliases públicos (`sync`, `--tipos`)
   - Portão: gates/G_LAYOUT_ENTREGA.py (provado) — `resolve_pasta_entrega` e proibição de entrega aninhada sob `projetos/` com legado irmão
   - Portão: gates/G_PACOTE_CORE.py (provado) — distribuição sem `*.db`, `requirements-dev*` e `docs/relatorios/`
   - Portão: gates/G_RESUMO_USUARIO.py (provado) — encerramento com RESUMO-USUARIO e RELATORIO-TECNICO
   - Portão: gates/G_ANT_LOCKIN_LEGADO.py (provado) — varredura lovable/supabase/firebase sem auto-delete
2. **Binary Quality:** Every change must pass Quality Gates (`python ecossistema.py audit`, exit 0 = pass, exit 1 = block).
   - Portão: gates/G_SAIDA_BINARIA.py (provado)
3. **Structured Persistence:** Persist state in audit files (JSON, SQLite), never in volatile conversation memory.
   - Portão: gates/G_MIGRATION_ROT.py (provado)
   - Portão: gates/G_ESTRUTURA_ESTADO.py (provado)
   - Portão: gates/G_GESTOR_SESSOES.py (provado)
4. **Extreme Token Economy:** Minimalist prompts, compact English core rules, dense PT-BR user responses only when requested.
   - Portão: gates/G_IDIOMA_LEI_4.py (provado)
   - Portão: gates/G_USER_FACING_PTBR.py (provado) — jargão explicado em README/`--help`/perfil leigo (Rule 10)
   - Portão: .claude/hooks/regra10_check.py (provado)
5. **Zero Stubs / Zero Mocks:** 100% functional, typed production code with real tests.
   - Portão: gates/G_TESTES_REAIS.py (provado)
6. **Agnostic Supremacy:** Zero vendor lock-in across OS, harness, and LLM providers.
   - Portão: gates/G_COMPONENTE_AGNOSTICO.py (provado)
7. **Developer in Control:** Strictly sequential, interactive executions. Zero invisible headless background subagents.
   - Portão: gates/G_ZERO_HEADLESS.py (provado)
8. **Label Honesty:** Never claim certification or test coverage beyond real automated test results.
   - Portão: gates/G_HONESTIDADE_ROTULO.py (provado)
9. **Tool Testing Discipline:** Follow the 5-step cycle (`docs/protocolos/PROTOCOLO-TESTES-FERRAMENTAS.md`): 1. Auto-fix bugs until 100% conformant (zero inconsistencies), 2. Git commit & push, 3. Clean target project, 4. Execute cleanly, 5. Update `docs/teste-end-to-end/` report.
   - Portão: gates/G_ENV_ROT.py (provado)
   - Portão: gates/G_SKILL_ROT.py (provado)
   - Portão: gates/G_DISCIPLINA_TESTE_FERRAMENTA.py (provado)
   - Portão: gates/G_TEMPLATE_FORGE_ROT.py (provado)
   - Portão: gates/G_amelhoria.py (provado) — quality gate da ferramenta `aidd-melhoria` (Fase 6, Ticket 6)
   - Portão: gates/G_HANDOFF_MELHORIA.py (provado) — integridade e assinatura HMAC do handoff de melhoria (Fase 8, Ticket 8)
10. **Quarteto Sine Qua Non Dinâmico (Lei #10 — Quarteto; distinto de Rule 10 Formato de Resposta):** Todo projeto gerado ou evoluído no ecossistema DEVE nascer nativamente com 4 pilares completos: OpenAPI/Swagger Studio (`/api`), Webhook Studio (`/webhook`), MCP Studio (`/mcp`) e Central de Documentação / Guia do Utilizador (`/docs`). Todas as rotas e contratos devem cobrir 100% dos módulos do sistema e atualizar-se de forma autônoma e dinâmica a cada novo módulo (ex: autenticação).
   - Portão: gates/G_CONTRACT_ROT.py (provado)
   - Portão: gates/G_QUARTETO_SINE_QUA_NON.py (provado)
11. **Padrão-Ouro de Stack Tecnológica:** Todo fluxo (`generator`, `master`, `factory`, `bridge`) DEVE gerar o Frontend em **Next.js + TypeScript + Tailwind CSS** (Backend em Python puro + SQLite WAL, API em OpenAPI 3.1), conforme definido em `docs/protocolos/PADRAO-OURO-STACK-TECNOLOGICA.md` — padrão validado em `proj_ctt`. Só muda se o plano estruturado ou o prompt do usuário especificar outra stack de forma explícita para aquela camada; silêncio nunca é licença para gerar outra coisa (ex.: HTML Python simples só é aceitável se pedido expressamente).
   - Portão: gates/G_STACK_PADRAO_OURO.py (provado)
12. **Anti-Docs Rot & Canonical Ingestion:** Agentes nunca devem ingerir ou se basear em documentos rascunho, históricos ou sem validação factual com o código. A documentação técnica viva reside exclusivamente em `docs/protocolos/`, `AGENTS.md` e schemas/OpenAPI ativos. Documentos e links quebrados são ativamente bloqueados pelo gate determinístico `gates/G_DOCS_ROT.py`.
   - Portão: gates/G_DOCS_ROT.py (provado)
13. **Todo Portão Deve Provar que Morde:** Nenhum quality gate é aceito sem teste automatizado que deliberadamente quebre a condição resguardada e asserte `exit 1`. Testes de caminho feliz (exit 0) não satisfazem o requisito. Qualquer gate incapaz de reprovar sob violação real ou sintética comprovada deve ser registrado como fachada e ter seu claim rebaixado per Lei #8. Ver `docs/protocolos/CONVENCAO-AUTORIA-GATES.md`.
   - Portão: gates/G_PORTAO_PROVA_QUE_MORDE.py (provado)

---

## 3. The 3 Canonical Creation Flows (A Tríade Canônica)

Every robust application in the ecosystem originates from **`aidd-forge`** (supreme governance and rule dictatorship) and an interactive **`PRÉ-PLANO`** intake (`aidd-planner`), allowing the developer or user to derive 3 distinct specialized paths with zero friction (CLI or Slash Commands):

- **FLUXO 01 — `aidd-pure` (Do Zero Puro | Slash: `/pure`):** `[FORGE -> PLANNER] -> GENERATOR -> [MASTER -> ENTERPRISE -> OPS]`
  - Engine: `aidd-generator` (8-phase pipeline, TDD Red-Green, Monólito Modular VSA + Next.js).
  - CLI: `python ecossistema.py pure` ou `python ecossistema.py run-fluxo --fluxo pure`
  - Skills: `aidd-pure`, `fluxo-01-runner`
- **FLUXO 02 — `aidd-open` (Motores Open-Source | Slash: `/aidd-open` ou `/open` ou `/factory`):** `[FORGE -> PLANNER] -> FACTORY -> [MASTER -> ENTERPRISE -> OPS]`
  - Engine: `aidd-factory` (Open-source engine curation, VSA integration slices, compose).
  - CLI: `python ecossistema.py open` (ou `python ecossistema.py aidd-open`) ou `python ecossistema.py run-fluxo --fluxo open`
  - Skills: `aidd-open`, `open`, `fluxo-02-runner`
  - *Aviso de Namespace:* No Antigravity CLI (`agy`), o comando `/open <path>` é reservado internamente pela ferramenta para abrir arquivos no editor do sistema. Por isso, no AGY/Antigravity utilize `/aidd-open` ou `/factory` para acionar este fluxo sem colisão.
- **FLUXO 03 — `aidd-freedom` (Low-Code / Apps Unificadas | Slash: `/freedom`):** `[FORGE -> PLANNER] -> BRIDGE -> [MASTER -> ENTERPRISE -> OPS]`
  - Engine: `aidd-bridge` (Vendor lock-in eradication, Lovable/v0/Bolt cleanup, PostgreSQL, UI preservation).
  - CLI: `python ecossistema.py freedom` ou `python ecossistema.py run-fluxo --fluxo freedom`
  - Skills: `aidd-freedom`, `freedom`, `fluxo-03-runner` (operações atômicas da ferramenta via `aidd-bridge-runner`)
- **EXECUÇÃO DETERMINÍSTICA DE PIPELINE & PLANOS (Slash: `/run-plan` e `/pipeline`):**
  - Engine: `tools/aidd-master/scripts/orchestrator_pipeline.py` & `scripts/compilador_tickets_plano.py` (Worktrees efêmeras + Join Barrier).
  - CLI: `python ecossistema.py run-plan <plano>` e `python ecossistema.py pipeline --handoff <json>`
  - Skills: `aidd-pipeline-runner`
- **MESO-CAMADA VSA — DESPACHO TOPOLÓGICO EM WORKTREES (Slash: `/dispatch` e `/aidd-dispatch`):**
  - Engine: `tools/aidd-master/scripts/dispatch_pipeline.py` & `engine_router.py` & `vsa_join_barrier.py` (Kahn DAG, worktrees efêmeras, barreira de validação e convergência master).
  - CLI: `python ecossistema.py dispatch --planner <plano>` ou `python ecossistema.py dispatch --dispatch <json>`
  - Skills: `aidd-dispatch-runner`
- **PIPELINE LINEAR DE AUDITORIA 4 FASES (Slash: `/audit-4f` e `/aidd-auditor`):**
  - Engine: `docs/protocolos/PIPELINE-AUDITORIA-4F.md` & `componentes/compartilhado/skills/aidd-auditor-4f-runner` (Execução 4F: Inspetor, Arquiteto, Construtor, Retorno).
  - CLI: `python ecossistema.py audit-4f --manifest <json>`
  - Skills: `aidd-auditor-4f-runner`
- **PIPELINE DE EVOLUÇÃO TÉCNICA (Slash: `/evolucao` e `/aidd-evolucao`):**
  - Engine: `docs/auditoria/ARQUITETURA-SCAFFOLD.md` & `componentes/compartilhado/skills/aidd-evolucao-runner` & `scripts/compilador_plano_evolucao.py` (Execução sequencial dos tickets do Plano de Evolução).
  - CLI: `python ecossistema.py evolucao <tool>` ou `python ecossistema.py evolucao --manifest <json>`
  - Skills: `aidd-evolucao-runner`

**Interoperabilidade Universal dos Slash Commands:** Em harnesses sem suporte a slash commands customizados na UI ou com colisões de namespace (como `/open` no Google Antigravity CLI), qualquer entrada do usuário referenciando `/pure`, `pure`, `/open`, `/aidd-open`, `open`, `/freedom`, `freedom`, `/factory`, `/bridge`, `/run-plan`, `run-plan`, `/pipeline`, `pipeline`, `/dispatch`, `dispatch`, `/aidd-dispatch`, `/audit-4f`, `audit-4f`, `/aidd-auditor`, `/evolucao`, `evolucao`, `/aidd-evolucao`, `/sessao`, `sessao`, `/session`, `session`, `/id` DEVE ser interceptada pelo agente como a invocação imediata do respectivo fluxo ou comando do ecossistema. Silêncio ou erro de "comando não suportado" é estritamente proibido.

**Universal Convergence Funnel:** All 3 flows mandatorily converge into `aidd-master` (Harmonização em Monólito Modular: VSA de domínio + camada horizontal compartilhada) -> `aidd-enterprise` (SHA-256 resilience and audit) -> `aidd-ops` (VPS deployment, sops+age, and Uptime Kuma), delivering the dynamic *Quarteto Sine Qua Non* (`/api`, `/webhook`, `/mcp`, `/docs`).

---

## 4. Architecture & Context Dispatch

Core rules are universal. Domain and tool-specific instructions reside in their respective directories:
- `tools/aidd-forge/AGENTS.md` -> Bootstrap, templates, and environment shielding.
- `tools/aidd-planner/AGENTS.md` -> Planning engine, SDD/BDD intake, and Triad fuel generation.
- `tools/aidd-generator/AGENTS.md` -> 8-phase software generation factory.
- `tools/aidd-master/AGENTS.md` -> Modular Vertical Slice architecture.
- `tools/aidd-enterprise/AGENTS.md` -> Mission-critical SHA-256 injected components.
- `tools/aidd-ops/AGENTS.md` -> Agentic infrastructure meta-orchestration.
- `tools/aidd-factory/AGENTS.md` -> Multi-service application & integration code generator.
- `tools/aidd-bridge/AGENTS.md` -> Low-code (Lovable/v0/Bolt) VPS packager.

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
- `/aidd-sessao`: Deterministic session ID and metadata persistence in `secoes/` for instant recovery.
