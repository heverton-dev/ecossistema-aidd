# Canonical AIDD Ecosystem Governance & Agent Directives

> **Repository:** https://github.com/heverton-dev/ecossistema-aidd
> **Governance Standard:** Zero Stubs, Strict Determinism, Context Optimization (<2000 tokens), Absolute Cache Invariance.
> **Full Reference:** `docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md`
> **Glossary:** `CONTEXT.md` — domain terms; read before using ciclo, fase, plano, sessão or ticket.

---

## 1. Core Execution Constraints

- **Thinking constraint:** Think strictly in compact English. No meta-deliberation. Focus only on architectural invariants and edge cases. Under 150 words of reasoning.
- **Execution limit:** Resolve tasks in 3 to 5 discrete steps. Stop and request confirmation if more steps are required.
- **Output format (Rule 10 — Formato de Resposta):** Silent executor. Return code edits and 1-line execution status only. Do not explain what was changed unless explicitly asked. Do not repeat code in conversational reply. (Distinct from Lei #10 (Quarteto).)
  - When prose is requested, strictly shape answers as:
    1. One top sentence stating what to do or what happened in practice. No preamble.
    2. Short bulleted body: facts, exact changes and practical results (What changed ➔ Why ➔ Concrete impact). No narration of steps taken or abstract high-level philosophies.
    3. One closing suggestion block, separated from the body.
    - Forbidden: polite greetings, restating the request, recapping what was just said, listing options without a recommendation, unexplained jargon, empty hermetic abstractions.
  - **Token budget — decide before writing, not after:** target ≤300 tokens for a
    normal answer, ≤600 for a technical one (code/tables). This is a pre-generation
    limit, not a post-hoc filter — plan the answer's length before writing the first
    word. A hook that blocks and forces a rewrite after the fact already cost the
    tokens of the rejected draft; treat any such block as a signal you planned wrong,
    not as the mechanism meant to enforce this.
- **Editing rule:** Always use exact search/replace block tools (`replace_file_content`). Never dump entire rewritten files into output.
- **Bash rule:** Always pipe verbose commands to tail/grep. E.g., `pytest 2>&1 | tail -n 25`. Never dump raw bundle outputs, logs, or lockfiles into context.
- **Long-task rule:** Run anything slower than ~2 minutes (full gate battery, `gate_final`, 4F pipeline) in the background and resume on its completion notice. Never ask the user to "call back in N minutes". One heavy cycle at a time: `scripts/fila_ciclos.py` queues the rest and notifies when each ends.
- **Graph-first (Lei #14):** Always query knowledge graph (`codebase-memory-mcp` MCP) before Grep, Glob, or full file reads.
- **Docs Ingestion constraint:** Read ONLY living canonical documentation (`docs/protocolos/`, `AGENTS.md`, `MEMORY.md`). Never ingest historical reports, superseded manuals, or past session logs as system truths.

---

## 2. Inviolable Laws

1. **Determinism First:** Use deterministic scripts, AST, regex, or JSON Schema. Never use LLM for mechanical tasks.
   - Portão: modulos/01-governanca-e-qualidade/gates/G_DETERMINISMO_LEI_1.py (provado)
   - Portão: modulos/04-nucleo-compartilhado/gates/G_PIPELINE_HANDOFF.py (provado)
   - Portão: modulos/03-plataforma-e-entrega/gates/G_DISPATCH_PIPELINE_VSA.py (provado)
   - Portão: modulos/04-nucleo-compartilhado/gates/G_ESCRITOR_ATOMICO.py (provado)
   - Portão: modulos/04-nucleo-compartilhado/gates/G_ORQUESTRADOR_SINCRONO.py (provado)
   - Portão: modulos/04-nucleo-compartilhado/gates/G_TRANSACTION_LOG_LRU.py (provado)
   - Portão: modulos/04-nucleo-compartilhado/gates/G_SYNC_CMD_ROT.py (provado) — forma canônica `components sync --tipo todos` e aliases públicos (`sync`, `--tipos`)
   - Portão: modulos/03-plataforma-e-entrega/gates/G_LAYOUT_ENTREGA.py (provado) — `resolve_pasta_entrega` e proibição de entrega aninhada sob `projetos/` com legado irmão
   - Portão: modulos/04-nucleo-compartilhado/gates/G_PACOTE_CORE.py (provado) — distribuição sem `*.db`, `requirements-dev*` e `docs/relatorios/`
   - Portão: modulos/04-nucleo-compartilhado/gates/G_RESUMO_USUARIO.py (provado) — encerramento com RESUMO-USUARIO e RELATORIO-TECNICO
   - Portão: modulos/02-triade-motores/fluxo-03-freedom/gates/G_ANT_LOCKIN_LEGADO.py (provado) — varredura lovable/supabase/firebase sem auto-delete
2. **Binary Quality:** Every change must pass Quality Gates (`python ecossistema.py audit`, exit 0 = pass, exit 1 = block).
   - Portão: modulos/04-nucleo-compartilhado/gates/G_SAIDA_BINARIA.py (provado)
   - Portão: modulos/04-nucleo-compartilhado/gates/G_ECOSSISTEMA_INTEGRIDADE.py (provado)
   - Portão: modulos/01-governanca-e-qualidade/gates/G_LEI_DECLARA_PORTAO.py (provado)
3. **Structured Persistence:** Persist state in audit files (JSON, SQLite), never in volatile conversation memory.
   - Portão: modulos/02-triade-motores/fluxo-03-freedom/gates/G_MIGRATION_ROT.py (provado)
   - Portão: modulos/04-nucleo-compartilhado/gates/G_ESTRUTURA_ESTADO.py (provado)
   - Portão: modulos/04-nucleo-compartilhado/gates/G_GESTOR_SESSOES.py (provado)
   - Portão: modulos/04-nucleo-compartilhado/gates/G_LIVRO_EVIDENCIA.py (provado)
4. **Extreme Token Economy:** Minimalist prompts, compact English core rules, dense PT-BR user responses only when requested.
   - Portão: modulos/04-nucleo-compartilhado/gates/G_IDIOMA_LEI_4.py (provado)
   - Portão: modulos/04-nucleo-compartilhado/gates/G_USER_FACING_PTBR.py (provado) — jargão explicado em README/`--help`/perfil leigo (Rule 10)
   - Portão: modulos/04-nucleo-compartilhado/gates/G_CLI_HELP_CONSISTENCIA.py (provado)
   - Portão: modulos/04-nucleo-compartilhado/gates/G_LLM_PROMPT_SHIELD.py (provado)
   - Portão: .claude/hooks/regra10_check.py (provado)
5. **Zero Stubs / Zero Mocks:** 100% functional, typed production code with real tests.
   - Portão: modulos/01-governanca-e-qualidade/gates/G_TESTES_REAIS.py (provado)
   - Portão: modulos/02-triade-motores/fluxo-01-pure/gates/G_PROTOTYPE_REWRITE.py (provado)
   - Portão: modulos/04-nucleo-compartilhado/gates/G_PROTOCOL_FALLBACK.py (provado)
   - Portão: modulos/04-nucleo-compartilhado/gates/G_SEGREDOS.py (provado)
6. **Agnostic Supremacy:** Zero vendor lock-in across OS, harness, and LLM providers.
   - Portão: modulos/02-triade-motores/fluxo-02-open/gates/G_COMPONENTE_AGNOSTICO.py (provado)
   - Portão: modulos/04-nucleo-compartilhado/gates/G_HARNESS_COMPAT.py (provado)
   - Portão: modulos/04-nucleo-compartilhado/gates/G_UNIVERSAL_HARNESS.py (provado)
   - Portão: modulos/04-nucleo-compartilhado/gates/G_DEPENDENCIAS_PIN_HASH.py (provado)
   - Portão: modulos/04-nucleo-compartilhado/gates/G_SUPPLY_CHAIN.py (provado)
7. **Developer in Control:** Strictly sequential, interactive executions. Zero invisible headless background subagents.
   - Portão: modulos/04-nucleo-compartilhado/gates/G_ZERO_HEADLESS.py (provado)
   - Portão: modulos/03-plataforma-e-entrega/gates/G_ISOLATION_AUDIT.py (provado)
   - Portão: modulos/02-triade-motores/fluxo-02-open/gates/G_HADOLINT.py (provado)
8. **Label Honesty:** Never claim certification or test coverage beyond real automated test results.
   - Portão: modulos/04-nucleo-compartilhado/gates/G_HONESTIDADE_ROTULO.py (provado)
   - Portão: modulos/04-nucleo-compartilhado/gates/G_mapa_pecas.py (provado) — integridade do catálogo de peças e mapas visuais (mapa-pecas, Ticket 6)
   - Portão: modulos/04-nucleo-compartilhado/gates/G_DRIFT_ANALYZER.py (provado)
   - Portão: modulos/04-nucleo-compartilhado/gates/G_DRIFT_NUCLEO_COMPARTILHADO.py (provado)
9. **Tool Testing Discipline:** Follow the 5-step cycle (`docs/protocolos/PROTOCOLO-TESTES-FERRAMENTAS.md`): 1. Auto-fix bugs until 100% conformant (zero inconsistencies), 2. Git commit & push, 3. Clean target project, 4. Execute cleanly, 5. Update `docs/teste-end-to-end/` report.
   - Portão: modulos/04-nucleo-compartilhado/gates/G_ENV_ROT.py (provado)
   - Portão: modulos/04-nucleo-compartilhado/gates/G_SKILL_ROT.py (provado)
   - Portão: modulos/04-nucleo-compartilhado/gates/G_SKILL_FORMATO.py (provado)
   - Portão: modulos/01-governanca-e-qualidade/gates/G_DISCIPLINA_TESTE_FERRAMENTA.py (provado)
   - Portão: modulos/01-governanca-e-qualidade/gates/G_TEMPLATE_FORGE_ROT.py (provado)
   - Portão: modulos/04-nucleo-compartilhado/gates/G_FRONTEIRA_FERRAMENTAS.py (provado) — arquivo de tools/ no dono certo do mapa de donos, modo aviso (fronteiras-ferramentas, Ticket 6)
   - Portão: modulos/01-governanca-e-qualidade/gates/G_amelhoria.py (provado) — quality gate da ferramenta `aidd-melhoria` (Fase 6, Ticket 6)
   - Portão: modulos/01-governanca-e-qualidade/gates/G_aidd_diagnose.py (provado) — quality gate da ferramenta `aidd-diagnose` (Fase 6, Ticket 6)
   - Portão: modulos/01-governanca-e-qualidade/gates/G_aidd_forge.py (provado) — quality gate da ferramenta `aidd-forge` (DoD 6 / D13)
   - Portão: modulos/03-plataforma-e-entrega/gates/G_aidd_enterprise.py (provado) — quality gate da ferramenta idd-enterprise (ciclo-01)
   - Portão: modulos/01-governanca-e-qualidade/gates/G_aidd_spec.py (provado) — quality gate da ferramenta `aidd-spec` (ciclo-01)
   - Portão: modulos/01-governanca-e-qualidade/gates/G_aidd_tdd.py (provado) — quality gate da ferramenta `aidd-tdd` (ciclo-01)
   - Portão: modulos/01-governanca-e-qualidade/gates/G_aidd_tickets.py (provado) — quality gate da ferramenta `aidd-tickets` (ciclo-01)
   - Portão: modulos/01-governanca-e-qualidade/gates/G_aidd_grill.py (provado) — quality gate da skill `aidd-grill` (ciclo-01)
   - Portão: modulos/01-governanca-e-qualidade/gates/G_aidd_handoff.py (provado) — quality gate da ferramenta `aidd-handoff` (ciclo-01)
   - Portão: modulos/01-governanca-e-qualidade/gates/G_aidd_plan.py (provado) — quality gate da ferramenta `aidd-plan` (ciclo-01)
   - Portão: modulos/01-governanca-e-qualidade/gates/G_aidd_planner_runner.py (provado) — quality gate da ferramenta `aidd-planner-runner` (ciclo-01)
   - Portão: modulos/04-nucleo-compartilhado/gates/G_aidd_visual_maps.py (provado) — quality gate da ferramenta `aidd-visual-maps` (ciclo-01)
   - Portão: modulos/01-governanca-e-qualidade/gates/G_aidd_session.py (provado) — quality gate da ferramenta `aidd-session` (ciclo-01)
   - Portão: modulos/01-governanca-e-qualidade/gates/G_PROVA_SKILLS_POCOCK.py (provado, manual) — uso real das skills do ciclo skills-pocock via modelo; fora do pre-commit (skills-pocock, Ticket 13)
   - Portão: modulos/01-governanca-e-qualidade/gates/G_HANDOFF_MELHORIA.py (provado) — integridade e assinatura HMAC do handoff de melhoria (Fase 8, Ticket 8)
   - Portão: modulos/03-plataforma-e-entrega/gates/G_INFRA_COMPOSE.py (provado)
   - Portão: modulos/04-nucleo-compartilhado/gates/G_MODULO_FRONTEIRA.py (provado) — fronteira entre fatias VSA: sys.path, caminho literal, tools/ e import cruzado só pelo interface.py (ciclo-03)
10. **Quarteto Sine Qua Non Dinâmico (Lei #10 — Quarteto; distinto de Rule 10 Formato de Resposta):** Todo projeto gerado ou evoluído no ecossistema DEVE nascer nativamente com 4 pilares completos: OpenAPI/Swagger Studio (`/api`), Webhook Studio (`/webhook`), MCP Studio (`/mcp`) e Central de Documentação / Guia do Utilizador (`/docs`). Todas as rotas e contratos devem cobrir 100% dos módulos do sistema e atualizar-se de forma autônoma e dinâmica a cada novo módulo (ex: autenticação).
   - Portão: modulos/03-plataforma-e-entrega/gates/G_CONTRACT_ROT.py (provado)
   - Portão: modulos/03-plataforma-e-entrega/gates/G_QUARTETO_SINE_QUA_NON.py (provado)
11. **Padrão-Ouro de Stack Tecnológica:** Todo fluxo (`generator`, `master`, `factory`, `bridge`) DEVE gerar o Frontend na stack Padrão-Ouro canônica soberana: **TanStack Start / TanStack Router + React + TypeScript + Tailwind CSS** (PWA e Offline-First resiliente com fila HMAC, Backend em Python puro + SQLite WAL, API em OpenAPI 3.1), conforme definido em `docs/protocolos/PADRAO-OURO-STACK-TECNOLOGICA.md` e `docs/padroes/PADRAO-OURO-ARQUITETURA-CAMADAS-MERCADO.md`. O framework Next.js está formalmente abolido do ecossistema devido ao acoplamento proprietário de runtime, fragilidade na navegação offline por RSC e ausência de type-safety nativa em Search Params.
   - Portão: modulos/02-triade-motores/fluxo-01-pure/gates/G_STACK_PADRAO_OURO.py (provado)
   - Portão: modulos/02-triade-motores/fluxo-01-pure/gates/G_TEMPLATE_TANSTACK_OFFLINE.py (provado)
   - Portão: modulos/02-triade-motores/fluxo-01-pure/gates/G_NOVE_CAMADAS_MERCADO.py (provado)
   - Portão: modulos/02-triade-motores/fluxo-01-pure/gates/G_FRONTEND_LAYERS.py (provado)
   - Portão: modulos/03-plataforma-e-entrega/gates/G_ARQUITETURA_DELIVERABLE.py (provado)
12. **Anti-Docs Rot & Canonical Ingestion:** Agentes nunca devem ingerir ou se basear em documentos rascunho, históricos ou sem validação factual com o código. A documentação técnica viva reside exclusivamente em `docs/protocolos/`, `AGENTS.md` e schemas/OpenAPI ativos. Documentos e links quebrados são ativamente bloqueados pelo gate determinístico `modulos/01-governanca-e-qualidade/gates/G_DOCS_ROT.py`.
   - Portão: modulos/01-governanca-e-qualidade/gates/G_DOCS_ROT.py (provado)
13. **Todo Portão Deve Provar que Morde:** Nenhum quality gate é aceito sem teste automatizado que deliberadamente quebre a condição resguardada e asserte `exit 1`. Testes de caminho feliz (exit 0) não satisfazem o requisito. Qualquer gate incapaz de reprovar sob violação real ou sintética comprovada deve ser registrado como fachada e ter seu claim rebaixado per Lei #8. Ver `docs/protocolos/CONVENCAO-AUTORIA-GATES.md`.
   - Portão: modulos/01-governanca-e-qualidade/gates/G_PORTAO_PROVA_QUE_MORDE.py (provado)
14. **Graph-First Obrigatório:** Todo agente pesquisa o código do ecossistema primeiro pelo `codebase-memory-mcp` (`search_graph`, `get_code_snippet`, `trace_path`, `query_graph`). Grep, Glob e leitura de arquivo inteiro só entram depois do graph, ou para texto literal que o graph não indexa. No pipeline 4F, fase cujo agente não fez nenhuma chamada ao graph reprova antes do `gate_fase` e nada é commitado.
   - Portão: modulos/04-nucleo-compartilhado/gates/G_GRAPH_FIRST.py (provado) — lê o histórico do agente; cobre o claude (`~/.claude/projects/*.jsonl`); agy, opencode e mimo não gravam histórico legível e só recebem aviso (fronteiras-ferramentas, Bloco 2)

---

## 3. The 3 Canonical Creation Flows (A Tríade Canônica)

Every robust application in the ecosystem originates from **`aidd-forge`** (supreme governance and rule dictatorship) and an interactive **`PRÉ-PLANO`** intake (`aidd-planner`), allowing the developer or user to derive 3 distinct specialized paths with zero friction (CLI or Slash Commands):

- **FLUXO 01 — `aidd-pure` (Do Zero Puro | Slash: `/pure`):** `[FORGE -> PLANNER] -> GENERATOR -> [MASTER -> ENTERPRISE -> OPS]`
  - Engine: `aidd-pure` (8-phase pipeline, TDD Red-Green, Monólito Modular VSA + Next.js).
  - CLI: `python ecossistema.py pure` ou `python ecossistema.py run-fluxo --fluxo pure`
  - Skill: `aidd-pure`
- **FLUXO 02 — `aidd-open` (Motores Open-Source | Slash: `/aidd-open` ou `/open` ou `/factory`):** `[FORGE -> PLANNER] -> FACTORY -> [MASTER -> ENTERPRISE -> OPS]`
  - Engine: `aidd-open` (Open-source engine curation, VSA integration slices, compose).
  - CLI: `python ecossistema.py open` (ou `python ecossistema.py aidd-open`) ou `python ecossistema.py run-fluxo --fluxo open`
  - Skill: `aidd-open`
  - *Aviso de Namespace:* No Antigravity CLI (`agy`), o comando `/open <path>` é reservado internamente pela ferramenta para abrir arquivos no editor do sistema. Por isso, no AGY/Antigravity utilize `/aidd-open` ou `/factory` para acionar este fluxo sem colisão.
- **FLUXO 03 — `aidd-freedom` (Low-Code / Apps Unificadas | Slash: `/freedom`):** `[FORGE -> PLANNER] -> BRIDGE -> [MASTER -> ENTERPRISE -> OPS]`
  - Engine: `aidd-freedom` (Vendor lock-in eradication, Lovable/v0/Bolt cleanup, PostgreSQL, UI preservation).
  - CLI: `python ecossistema.py freedom` ou `python ecossistema.py run-fluxo --fluxo freedom`
  - Skill: `aidd-freedom` (operações atômicas da ferramenta via `aidd-freedom`)
- **EXECUÇÃO DETERMINÍSTICA DE PIPELINE & PLANOS (Slash: `/run-plan` e `/pipeline`):**
  - Engine: `modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/scripts/orchestrator_pipeline.py` & `scripts/compilador_tickets_plano.py` (Worktrees efêmeras + Join Barrier).
  - CLI: `python ecossistema.py run-plan <plano>` e `python ecossistema.py pipeline --handoff <json>`
  - Skill: `aidd-pipeline`
- **MESO-CAMADA VSA — DESPACHO TOPOLÓGICO EM WORKTREES (Slash: `/dispatch` e `/aidd-dispatch`):**
  - Engine: `modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/scripts/dispatch_pipeline.py` & `engine_router.py` & `vsa_join_barrier.py` (Kahn DAG, worktrees efêmeras, barreira de validação e convergência master).
  - CLI: `python ecossistema.py dispatch --planner <plano>` ou `python ecossistema.py dispatch --dispatch <json>`
  - Skill: `aidd-dispatch`
- **PIPELINE LINEAR DE AUDITORIA 4 FASES (Slash: `/audit-4f` e `/aidd-auditor`):**
  - Engine: `docs/protocolos/PIPELINE-AUDITORIA-4F.md` & `componentes/compartilhado/skills/aidd-audit-4f` (Execução 4F: Inspetor, Arquiteto, Construtor, Retorno).
  - CLI: `python ecossistema.py audit-4f --manifest <json>`
  - Skill: `aidd-audit-4f`
- **PIPELINE DE EVOLUÇÃO TÉCNICA (Slash: `/evolucao` e `/aidd-evolucao`):**
  - Engine: `docs/auditoria/ARQUITETURA-SCAFFOLD.md` & `componentes/compartilhado/skills/aidd-evolution` & `scripts/compilador_plano_evolucao.py` (Execução sequencial dos tickets do Plano de Evolução).
  - CLI: `python ecossistema.py evolucao <tool>` ou `python ecossistema.py evolucao --manifest <json>`
  - Skill: `aidd-evolution`

- **PIPELINE CANÔNICO CALIBRADO (Fluxo de 9 Etapas com Gates em 2 Níveis e Schemas SHA-256):**
  - Encadeamento Canônico Estrito:
    ```
    [1. FORGE] ➔ [2. PLANNER (SHA-256)] ➔ [3. MASTER (Fatiamento VSA)]
          ➔ [4. DISPATCH (Worktrees + Micro-Gates)] ➔ [5. ENGINE (Execução das Fatias)]
          ➔ [6. BARREIRA (Rebase Sync)] ➔ [7. ENTERPRISE & OPS] ➔ [8. 54 MACRO-GATES]
          ➔ [9. COMMIT CONSOLIDADO]
    ```
  - **Papel das Etapas e dos Motores da Tríade:**
    - O `aidd-master` atua antes da execução do código compilando o manifesto `VSA_DISPATCH.json` a partir da planta baixa do `aidd-planner`.
    - O `aidd-dispatch` gera as Git Worktrees paralelas/efêmeras.
    - O **Motor da Tríade** (`aidd-pure` | `aidd-open` | `aidd-freedom`) executa *dentro das worktrees*, materializando as fatias sob isolamento rigoroso.
    - A **Barreira de Sincronização** valida os micro-gates, executa o rebase preventivo e consolida as fatias na branch de integração antes da injeção de infraestrutura e conectores corporativos.
  - **Contratos e Handoff Formal:** Todos os contratos centrais (`PLANNER.json`, `VSA_DISPATCH.json`, `handoff_evolution.json`) exigem integridade criptográfica `payload_sha256` calculada sobre o payload canônico. Se o hash divergir, o bastão é bloqueado imediatamente (exit 1).
  - **Gates em 2 Níveis (Shift-Left):**
    - *Nível 1 (Micro-Gates de Worktree):* Execução rápida (< 2s) em isolamento da fatia (`py_compile`, verificação de stubs/Lei #5, testes unitários da fatia, verificação de fronteiras). Reprovação aborta a worktree antes do merge.
    - *Nível 2 (54 Macro-Gates Globais):* Executados pós-convergência via `python ecossistema.py audit` / `pre-commit run --all-files`.
  - **Barreira de Sincronização (--barrier-sync):** Rebase preventivo da branch de integração na worktree antes do merge. Em caso de conflito, executa rollback automático e grava `dispatch_rollback_report.json`.

**Interoperabilidade Universal dos Slash Commands:** Em harnesses sem suporte a slash commands customizados na UI ou com colisões de namespace (como `/open` no Google Antigravity CLI), qualquer entrada do usuário referenciando `/pure`, `pure`, `/open`, `/aidd-open`, `open`, `/freedom`, `freedom`, `/factory`, `/bridge`, `/run-plan`, `run-plan`, `/pipeline`, `pipeline`, `/dispatch`, `dispatch`, `/aidd-dispatch`, `/audit-4f`, `audit-4f`, `/aidd-auditor`, `/evolucao`, `evolucao`, `/aidd-evolucao`, `/sessao`, `sessao`, `/session`, `session`, `/id` DEVE ser interceptada pelo agente como a invocação imediata do respectivo fluxo ou comando do ecossistema. Silêncio ou erro de "comando não suportado" é estritamente proibido.

**Universal Convergence Funnel:** All 3 flows mandatorily converge into `aidd-master` (Harmonização em Monólito Modular: VSA de domínio + camada horizontal compartilhada) -> `aidd-enterprise` (SHA-256 resilience and audit) -> `aidd-ops` (VPS deployment, sops+age, and Uptime Kuma), delivering the dynamic *Quarteto Sine Qua Non* (`/api`, `/webhook`, `/mcp`, `/docs`).

---

## 4. Architecture & Context Dispatch

Core rules are universal. Dispatch: editing inside a slice, read that slice's `AGENTS.md` first (slice invariants, < 400 tokens), then the tool's `AGENTS.md`. Slices come from `modulos/04-nucleo-compartilhado/contracts/MAPA-FATIAS.json`; `validador_fractalidade_vsa` requires `AGENTS.md` + `README.md` in every slice.

| Slice | Slice rules | Tool rules | Scope |
|---|---|---|---|
| 01-governanca-e-qualidade | `modulos/01-governanca-e-qualidade/AGENTS.md` | `core/aidd-forge/AGENTS.md`, `core/aidd-planner/AGENTS.md` | Bootstrap, piece warehouse, planning engine and Triad fuel |
| fluxo-01-pure | `modulos/02-triade-motores/fluxo-01-pure/AGENTS.md` | `core/aidd-pure/AGENTS.md` | 8-phase software generation factory |
| fluxo-02-open | `modulos/02-triade-motores/fluxo-02-open/AGENTS.md` | `core/aidd-open/AGENTS.md` | Multi-service application and integration generator |
| fluxo-03-freedom | `modulos/02-triade-motores/fluxo-03-freedom/AGENTS.md` | `core/aidd-freedom/AGENTS.md` | Low-code (Lovable/v0/Bolt) VPS packager |
| blindagem-enterprise | `modulos/03-plataforma-e-entrega/blindagem-enterprise/AGENTS.md` | `aidd-enterprise/AGENTS.md` | Mission-critical SHA-256 injected components |
| fatiamento-master | `modulos/03-plataforma-e-entrega/fatiamento-master/AGENTS.md` | `aidd-master/AGENTS.md` | Modular Vertical Slice architecture |
| operacoes-ops | `modulos/03-plataforma-e-entrega/operacoes-ops/AGENTS.md` | `aidd-ops/AGENTS.md` | Agentic infrastructure meta-orchestration |

---

## 5. MCP Tools: codebase-memory-mcp

Query the graph BEFORE file scanning. Query the slice subgraph first: editing inside a slice, query its `vsa-<domain>` project before the whole-repo graph (smaller blast radius, fewer tokens). Domains (`componentes/compartilhado/src-core/subgrafos_federados.py`, `DOMINIOS_VSA`): `vsa-aidd-nucleo` (04), `vsa-modulo-governanca` (01), `vsa-triade-fluxo-pure`, `vsa-triade-fluxo-open`, `vsa-triade-fluxo-freedom`, `vsa-modulo-plataforma-ops` (03: enterprise, master, ops). Reindex: `python scripts/cli_modularizacao_vsa.py index-subgraphs`. `scripts/` and root files live only in the whole-repo graph.
- `search_graph`: Query functions, types, and references by name/regex pattern.
- `trace_path`: Trace callers (inbound), callees (outbound), or blast radius with depth limit.
- `query_graph`: Cypher-based structural queries on code relationships.
- `get_architecture`: High-level system architecture and component structure overview.
- `detect_changes`: Change blast radius, diff analysis, and affected flows.

---

## 6. Procedural Engineering Skills (`componentes/compartilhado/skills/`)

Authoring rules: `docs/protocolos/CONVENCAO-AUTORIA-SKILLS.md` (checked by `G_SKILL_FORMATO`, `G_SKILL_ROT` and `G_IDIOMA_LEI_4`).

Canonical workflow skills available across all harnesses to eliminate vibe coding and ensure rigorous pre-code alignment:
- `/aidd-grill`: Socratic interview protocol to resolve edge cases and invariants before code modification.
- `/aidd-grill-docs`: Architecture-grounded questioning anchored in `MEMORY.md` and repository laws.
- `/aidd-spec`: Deterministic technical specification generator with binary acceptance criteria.
- `/aidd-tickets`: Vertical-slice tickets (one verifiable behavior each) with `Blocked by`.
- `/aidd-tdd`: Agreed seams, then Red → Green loop; refactor at review; zero stubs, polyglot.
- `/aidd-diagnose`: 5-phase scientific fault triage integrated with `codebase-memory-mcp`.
- `/aidd-visual-maps`: Visual maps of each piece type from the parts catalog; `python ecossistema.py visual-maps gerar|check` (gate `G_aidd_visual_maps`).
- `/aidd-handoff`: Compact session context serialization directly into `secoes/`.
- `/aidd-session`: Deterministic session ID and metadata persistence in `secoes/` for instant recovery.
- `/aidd-agent-writing`: Writing guide for skills, AGENTS.md, CLAUDE.md.
- `/aidd-retro`: Session retro; mistakes become proposed gates or review rules.
- `/aidd-reexplain`: Re-explain last message in plain PT-BR using the glossary above.
- `/aidd-delivery`: Delivery template with before/after evidence and real exit codes.
- `/aidd-wizard`: Bash wizard for steps only the human can do.
