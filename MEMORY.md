# 🧠 MEMORY.md — Memória Estruturada e Contexto Operacional Consolidado

> **Repositório:** `https://github.com/heverton-dev/ecossistema-aidd`  
> **Última Atualização:** 2026-09-21  
> **Status:** PRODUÇÃO & ORQUESTRADO (ORCA ADE / ORC 3 / VSA TOPOLOGICAL DISPATCH)  
> **Finalidade:** Memória persistente de longo prazo para guiar desenvolvedores e agentes de IA em qualquer harness, evitando amnésia de contexto e retrabalho.

---

## 1. IDENTIDADE E ARQUITETURA DO ECOSSISTEMA

O **Ecossistema AIDD** é um monorepo agnóstico que integra 8 ferramentas complementares de Engenharia Agêntica de Software e a Tríade Canônica de Criação:

- **AIDD Forge (`tools/aidd-forge`):** Bootstrap de governança, isolamento de fases e purge de contexto (`/forge`).
- **AIDD Planner (`tools/aidd-planner`):** Planejamento BDD/SDD, compilador topológico DAG VSA e contratos de handoff (`/planner`).
- **AIDD Generator (`tools/aidd-generator`):** Fábrica autônoma com pipeline de 8 fases, TDD Red-Green e Clean Architecture (`/generate` ou `/pure`).
- **AIDD Master (`tools/aidd-master`):** Monólito modular VSA com fatias verticais, motor de despacho `dispatch_pipeline.py`, convergência master, Next.js Padrão-Ouro (Lei #11) e OpenAPI (`/master`).
- **AIDD Enterprise (`tools/aidd-enterprise`):** Missão crítica com injeção de componentes SHA-256 e Zero-Trust (`/enterprise`).
- **AIDD Ops (`tools/aidd-ops`):** Meta-Orquestrador de Infraestrutura (IaC, sizing, Docker Swarm, Ansible, deploy VPS, `/ops`).
- **AIDD Factory (`tools/aidd-factory`):** Integração e fatiamento VSA de motores open-source com compose (`/factory` ou `/open` ou `/aidd-open`).
- **AIDD Bridge (`tools/aidd-bridge`):** Desacoplamento anti-lockin de plataformas Low-Code (Lovable/v0) preservando a UI (`/bridge` ou `/freedom`).

### A Tríade Canônica de Criação (Nomenclatura Oficial):
1. **`aidd-pure` (Fluxo 01 — Do Zero Puro | Slash: `/pure`):** `[FORGE -> PLANNER] -> GENERATOR -> [MASTER -> ENTERPRISE -> OPS]`
2. **`aidd-open` (Fluxo 02 — Motores Open-Source | Slash: `/aidd-open` ou `/open`):** `[FORGE -> PLANNER] -> FACTORY -> [MASTER -> ENTERPRISE -> OPS]`
3. **`aidd-freedom` (Fluxo 03 — Desacoplamento Low-Code | Slash: `/freedom`):** `[FORGE -> PLANNER] -> BRIDGE -> [MASTER -> ENTERPRISE -> OPS]`

**Execução e Orquestração Determinística:**
- **Orquestrador Síncrono:** `python ecossistema.py run-fluxo --fluxo <pure|open|freedom>`
- **Pipeline em Worktrees & Join Barrier:** `python ecossistema.py run-plan <plano>` e `python ecossistema.py pipeline --handoff <json>`
- **Meso-Camada VSA (Topological Dispatch):** `python ecossistema.py dispatch --planner <plano>`

**Fonte Física Canônica Única:** Todo componente (`skill`, `command`, `mcp`, `hook`, `spec`) reside estritamente em `componentes/<escopo>/<tipo>/`. As pastas `.agents/`, `.claude/`, `.gemini/`, `.cursor/`, `.opencode/`, `.mimocode/`, `.codebuddy/` são alvos de materialização gerados por `scripts/gestor_componentes.py` (`python ecossistema.py components sync --tipo todos`).

---

## 2. AS 13 LEIS CANÔNICAS INEGOCIÁVEIS (`AGENTS.md`)

1. **Determinismo Primeiro (Lei #1):** Uso de scripts determinísticos, AST, regex, JSON Schema. LLM estritamente proibido para tarefas mecânicas. (`G_DETERMINISMO_LEI_1.py`, `G_PIPELINE_HANDOFF.py`, `G_DISPATCH_PIPELINE_VSA.py`).
2. **Qualidade Binária (Lei #2):** Toda validação produz saída binária estrita (`exit 0` = aprovado, `exit 1` = bloqueado). (`G_SAIDA_BINARIA.py`).
3. **Persistência Estruturada (Lei #3):** Estado reside em arquivos auditáveis (JSON, SQLite WAL, Git), nunca na memória volátil do chat. (`G_ESTRUTURA_ESTADO.py`, `G_MIGRATION_ROT.py`).
4. **Economia Extrema de Tokens (Lei #4):** Thinking telegráfico Caveman, saídas concisas em PT-BR, purge de contexto entre fases. (`G_IDIOMA_LEI_4.py`, `regra10_check.py`).
5. **Zero Stubs / Zero Mocks (Lei #5):** Código gerado deve ser funcional, tipado e com testes reais. Rejeição mecânica de TODO/FIXME. (`G_TESTES_REAIS.py`).
6. **Supremacia Agnóstica (Lei #6):** Universalidade total across OS e harnesses. (`G_COMPONENTE_AGNOSTICO.py`).
7. **Desenvolvedor no Controle (Lei #7):** Execuções estritamente sequenciais e interativas. Zero subagentes invisíveis ou headless em background. (`G_ZERO_HEADLESS.py`).
8. **Honestidade de Rótulo (Lei #8):** Nenhuma mensagem ou alegação de segurança/certificação além da cobertura real testada. (`G_HONESTIDADE_ROTULO.py`).
9. **Disciplina de Teste de Ferramentas (Lei #9):** Ciclo de 5 passos obrigatório com atualização contemporânea em `docs/teste-end-to-end/`. (`G_DISCIPLINA_TESTE_FERRAMENTA.py`, `G_ENV_ROT.py`, `G_SKILL_ROT.py`).
10. **Quarteto Sine Qua Non Dinâmico (Lei #10):** Todo projeto gerado ou evoluído provê dinamicamente OpenAPI/Swagger Studio (`/api`), Webhook Studio (`/webhook`), MCP Studio (`/mcp`) e Central de Documentação / Guia (`/docs`). (`G_QUARTETO_SINE_QUA_NON.py`, `G_CONTRACT_ROT.py`).
11. **Padrão-Ouro de Stack Tecnológica (Lei #11):** Frontend Next.js + TypeScript + Tailwind CSS; Backend Python + SQLite WAL + OpenAPI 3.1. (`G_STACK_PADRAO_OURO.py`).
12. **Anti-Docs Rot & Ingestão Canônica (Lei #12):** Proibido ingerir relatórios históricos ou rascunhos. Documentação viva estritamente em `docs/protocolos/` e `AGENTS.md`. (`G_DOCS_ROT.py`).
13. **Todo Portão Deve Provar que Morde (Lei #13):** Nenhum Quality Gate é aceito sem teste automatizado que force a violação e asserte `exit 1`. (`G_PORTAO_PROVA_QUE_MORDE.py`).

---

## 3. OS META-QUALITY GATES UNIFICADOS (`python ecossistema.py audit`)

| Gate | Arquivo | Responsabilidade |
|---|---|---|
| **G_DETERMINISMO_LEI_1** | `gates/G_DETERMINISMO_LEI_1.py` | Bloqueia chamadas LLM em rotas e scripts mecânicos. |
| **G_SAIDA_BINARIA** | `gates/G_SAIDA_BINARIA.py` | Audita saída estritamente binária (0/1) em todos os gates. |
| **G_ESTRUTURA_ESTADO** | `gates/G_ESTRUTURA_ESTADO.py` | Audita persistência estruturada e validação de schemas. |
| **G_IDIOMA_LEI_4** | `gates/G_IDIOMA_LEI_4.py` | Assegura inglês compacto no núcleo/tickets para economia de tokens. |
| **G_TESTES_REAIS** | `gates/G_TESTES_REAIS.py` | Executa suítes reais de pytest em cada ferramenta (zero mocks). |
| **G_COMPONENTE_AGNOSTICO** | `gates/G_COMPONENTE_AGNOSTICO.py` | Audita conformidade e integridade multi-harness. |
| **G_ZERO_HEADLESS** | `gates/G_ZERO_HEADLESS.py` | Garante modo interativo e bloqueia subagentes headless. |
| **G_HONESTIDADE_ROTULO** | `gates/G_HONESTIDADE_ROTULO.py` | Bloqueia alegações de marketing não comprovadas. |
| **G_DISCIPLINA_TESTE_FERRAMENTA** | `gates/G_DISCIPLINA_TESTE_FERRAMENTA.py` | Exige relatório end-to-end atualizado para mudanças em tools/. |
| **G_QUARTETO_SINE_QUA_NON** | `gates/G_QUARTETO_SINE_QUA_NON.py` | Valida `/docs`, `/webhooks`, `/mcp`, `/docs/guia` nos deliverables. |
| **G_STACK_PADRAO_OURO** | `gates/G_STACK_PADRAO_OURO.py` | Audita aderência ao padrão Next.js/TS/Tailwind + Py/WAL. |
| **G_PORTAO_PROVA_QUE_MORDE** | `gates/G_PORTAO_PROVA_QUE_MORDE.py` | Garante que todo gate possui teste unitário comprovando `exit 1`. |
| **G_PIPELINE_HANDOFF** | `gates/G_PIPELINE_HANDOFF.py` | Validação determinística de manifestos JSON de execução de pipeline. |
| **G_DISPATCH_PIPELINE_VSA** | `gates/G_DISPATCH_PIPELINE_VSA.py` | Validação formal de grafos DAG topológicos e fatias VSA. |
| **G_DOCS_ROT** | `gates/G_DOCS_ROT.py` | Bloqueia documentação rot e links quebrados na documentação viva. |

---

## 4. MATRIZ DE SLASH COMMANDS UNIVERSAIS

| Slash Command | Skill Subjacente | CLI Universal Equivalente | Função |
|---|---|---|---|
| `/pure <ideia>` | `aidd-pure`, `fluxo-01-runner` | `python ecossistema.py pure` (ou `run-fluxo --fluxo pure`) | **Tríade Fluxo 01:** Execução síncrona do zero puro com TDD Red-Green (Generator + Master + Enterprise + Ops). |
| `/open <ideia>` | `aidd-open`, `fluxo-02-runner` | `python ecossistema.py open` (ou `run-fluxo --fluxo open`) | **Tríade Fluxo 02:** Execução síncrona com motores Open-Source curados (Factory + Master + Enterprise + Ops). |
| `/freedom <origem> <nome>` | `aidd-freedom`, `fluxo-03-runner` | `python ecossistema.py freedom` (ou `run-fluxo --fluxo freedom`) | **Tríade Fluxo 03:** Execução síncrona libertando Low-Code (Lovable/v0) para VPS própria (Bridge + Master + Enterprise + Ops). |
| `/aidd-orchestrator` | `aidd-orchestrator-runner` | `python ecossistema.py run-fluxo` | Orquestrador Mestre Síncrono da Tríade Canônica com validação formal de contratos. |
| `/forge [caminho]` | `aidd-forge-runner` | `python ecossistema.py forge init [caminho]` | Bootstrap e blindagem de governança em novos projetos. |
| `/generate <ideia>` | `aidd-generator-runner` | `python ecossistema.py generate "<ideia>"` | Disparo da fábrica de 8 fases a partir de ideia. |
| `/master <modulo>` | `aidd-master-runner` | `python ecossistema.py master add-module <modulo>` | Criação de fatia vertical desacoplada em monólito modular. |
| `/enterprise <tipo> <nome>` | `aidd-enterprise-runner` | `python ecossistema.py enterprise inject <tipo> <nome>` | Injeção de componentes corporativos certificados SHA-256. |
| `/ops [requisito]` | `aidd-ops-runner` | `python ecossistema.py ops [requisito]` | Meta-Orquestrador de Infraestrutura: VPS, Docker, SSH, deploy. |
| `/orchestrate [plano]` | `orca-plan-orchestrator` | `python ecossistema.py orchestrate [plano]` | ORCA ADE — orquestração de planos de desenvolvimento via worktrees efêmeras. |
| `/run-plan <plano>` | `aidd-pipeline-runner` | `python ecossistema.py run-plan <plano>` | Executa pipeline determinístico de planos Markdown em Git Worktrees com Join Barrier. |
| `/pipeline <handoff>` | `aidd-pipeline-runner` | `python ecossistema.py pipeline --handoff <json>` | Executa pipeline determinístico a partir de manifesto JSON de handoff. |
| `/dispatch [args]` | `aidd-dispatch-runner` | `python ecossistema.py dispatch --planner <plano>` | Despacha fatias verticais VSA em Git Worktrees efêmeras com ordenação DAG topológica e convergência master. |
| `/aidd-dispatch` | `aidd-dispatch-runner` | `python ecossistema.py dispatch` | Alias canônico para o despacho da Meso-Camada VSA. |
| `/plan <nome>` | `planos-auditoria-runner` | `python ecossistema.py plan init <nome>` | Estruturação determinística de planos de auditoria e evolução. |
| `/bridge [comando]` | `aidd-bridge-runner` | `python ecossistema.py bridge [scan\|convert-db\|merge\|pack]` | Extrai, unifica e empacota apps Lovable/Supabase para VPS com PostgREST e Docker. |
| `/aidd-grill` | `aidd-grill` | N/A (Chat Interativo / Headless Fallback) | Entrevista socrática pré-código para alinhamento de invariantes e edge cases (handoff para `/aidd-spec`). |
| `/aidd-grill-docs` | `aidd-grill-docs` | N/A (Chat Interativo) | Questionamento socrático ancorado em MEMORY.md e governança local. |
| `/aidd-spec` | `aidd-spec` | N/A (Chat / Plan Generator) | Especificação técnica determinística com critérios binários (handoff para `/aidd-planner`). |
| `/aidd-tickets` | `aidd-tickets` | N/A (Chat / Vertical Slicing) | Decomposição em tickets atômicos tracer-bullet com blast radius restrito. |
| `/aidd-tdd` | `aidd-tdd` | N/A (Protocolo de Execução) | Ciclo Red-Green-Refactor estrito com regra Zero Stubs e suporte poliglota. |
| `/aidd-diagnose` | `aidd-diagnose` | N/A (Triage Científica) | Método de 5 fases para triage de incidentes integrado ao code-review-graph. |
| `/aidd-handoff` | `aidd-handoff` | N/A (Preservação de Sessão) | Serialização de contexto em secoes/ para rotação e continuidade entre agentes. |

---

## 5. TRAVAS ANTI-HEADLESS E PROTOCOLO ORCA ADE

- **Modo Interativo Mandatório:** O orquestrador (`orchestrator_engine.py`) opera com `interactive: bool = True` por padrão.
- **Flag Perigosa Requerida:** Qualquer tentativa de execução não assistida deve explicitar `--dangerously-force-headless` na CLI do `ecossistema.py`.
- **Abort Atômico (`Ctrl+C`):** Se o desenvolvedor interromper a execução no terminal, o motor captura o sinal, atualiza o estado para `FAILED`, executa a purga imediata da worktree efêmera e libera os locks git.
- **Prévia de Escopo:** Antes de iniciar a worktree, o comando a ser executado, o harness atribuído e a worktree são impressos no terminal para confirmação do desenvolvedor.
- **Seleção Interativa de Harness por Frente:** Durante o pré-voo, o usuário escolhe se quer harness único ou definir um harness específico para cada frente (ex: Claude para arquitetura, Mimo para implementação, Agy para validação).

---

## 6. HISTÓRICO CONSOLIDADO DE DECISÕES ARQUITETURAIS

- **2026-09-04:** Criação dos gates de integridade inicial, baseline de núcleo compartilhado e varredura de segredos.
- **2026-09-05:** Centralização de componentes em `componentes/` e automação multi-harness via `gestor_componentes.py`.
- **2026-09-06:**
  - Resolução do Achado #1 do `aidd-enterprise` (exposição do `--tipo-ambiguo` na CLI com testes reais aprovados).
  - Universalização dos comandos `/orchestrate` e `/plan` para todos os harnesses (`.agent/commands/` e `.claude/commands/`).
  - Implementação da seleção interativa de harness executor por frente no pré-voo da orquestração.
  - Implementação da Regra de Ouro #7 no `AGENTS.md` e criação do 7º Quality Gate (`G_ZERO_HEADLESS.py`).
  - Estabelecimento do padrão de trabalho com abort atômico e bloqueio completo de subagentes headless.
- **2026-09-07 — Auditoria "sem maquiagem" (achado grave: gate verde ≠ software funcionando):**
  - Rodando `pytest` ao vivo (não a telemetria do repo) e subindo de verdade os projetos gerados por cada ferramenta, a auditoria encontrou 12 testes reais falhando (2 aidd-master, 2 aidd-enterprise, 8 aidd-ops) no mesmo commit em que `python ecossistema.py audit` reportava 8/8 gates verdes — nenhum gate roda `pytest`.
  - `PLANO-EXECUCAO-ESTRUTURADO.json` (raiz) estava desatualizado/errado em 3 das 5 ferramentas (aidd-ops alegava 0/0/0, tinha 48 passed/8 failed reais).
  - Achados de execução real: CORS inseguro (`allow_origins=["*"]` + `allow_credentials=True`) no app gerado pelo generator; deploy Docker quebrado no módulo gerado pelo master (Dockerfile sem `pip install`, pasta `nginx/` inexistente, JWT secret em texto plano); gate "G_SEGURANCA" do enterprise majoritariamente grep/config vestido de "blindagem militar/homologação global" (~4 de 21 checks são funcionais de verdade); porta 3000 duplicada no docker-compose gerado pelo ops + dashboard cujo endpoint `/api/preflight` retorna JSON hardcoded fabricando "sem colisão"; "teste integrado" do ecossistema não comprova composição real entre ferramentas (orquestração nunca rodou, `harness_count: 0`).
  - Relatório completo: `docs/relatorios/relatorio-auditoria-ecossistema-aidd-sem-maquiagem.html`.
  - Plano de correção aberto (rascunho, aguardando aprovação item a item): `docs/planos/a-fazer/01-correcao-pos-auditoria-sem-maquiagem/` (14 itens, com sugestão de modelo/harness por item).
  - Camada estratégica aberta (rascunho): `docs/planos/a-fazer/02-direcionamento-estrategico-anti-nih/` (6 itens — o que fica/troca, north star, sequenciamento da troca de motor, reauditoria, investimento em diferencial).
  - Levantamento NIH salvo em `docs/features/08-09-2026_feature-oportunidades-reaproveitamento-nih.md` (26 itens de ferramenta OSS reaproveitável) e guia cross-projeto salvo fora do repo em `C:\Users\trcnologia\Desktop\CONSTRUA-SO-O-QUE-NINGUEM-CONSTRUIU.md`.
  - `docs/planos/` reorganizado em `feitos/`/`fazendo/`/`a-fazer/`, mantido automaticamente por `python scripts/atualizar_index_planos.py` (move a iniciativa de subpasta conforme o status real muda, nunca por alegação) — 3 planos soltos superados (`PLANO-CORRECAO-SKILLS-AGNOSTICAS.md`, `PLANO-EVOLUCAO-NOTAS-AUDITORIA.md`, `PLANO-EXECUCAO-ECOSSISTEMA-AIDD.md`) removidos por já estarem absorvidos e concluídos em iniciativas mais novas.
- **2026-09-08 / 2026-09-09 — Qualidade, Pre-commit e Anti-NIH:**
  - Migração para o framework `pre-commit` unificado (`.pre-commit-config.yaml`).
  - Regras #8 (Anti-NIH), #9 (Honestidade de Rótulo) e #10 (Comunicação Direta) incorporadas na governança.
  - Correção de XSS armazenado em `get_studio_html`, conclusão da migração para `click` em todos os CLI points e estreitamento de exceções genéricas (`except Exception`).
  - Conclusão da iniciativa `02-direcionamento-estrategico-anti-nih/`.
- **2026-09-10 — Chegada do AIDD Bridge e Self-Hosted Stack:**
  - Criação e integração do **AIDD Bridge** (`tools/aidd-bridge`): scanner Lovable, data bridge SQL (compatível com auth.uid(), auth.jwt(), PostgREST), multi-app unifier e DevOps packager com suporte a Swarm/Traefik e Kong Gateway + Postgres oficial Supabase + Storage.
  - Suíte completa de testes no `tools/aidd-bridge/tests/test_bridge.py` 100% verde (12 passed).
  - Sincronização automatizada e movimentação do plano `aidd-bridge` para `docs/planos/feitos/aidd-bridge/`.
  - Atualização completa do grafo de conhecimento (`code-review-graph`) e telemetria de integridade.
- **2025-07-19 — Auditoria de Stack por Camada (diagnóstico tecnológico comparativo):**
  - Relatório completo gerado em `docs/reports/analise-stack-por-camada.{md,html,pdf,typ}`.
  - **Nota média geral do ecossistema: 6.5/10 → 8.5/10 (projetado).**
  - **Maiores gaps encontrados:**
    - Frontend (4/10): Vanilla HTML+JS+Tailwind CDN → Recomenda React 19+Vite+shadcn/ui
    - Backend (5/10): Python http.server+RouteRegistry(NIH) → FastAPI 0.141+ (JÁ instalado em requirements.txt)
    - Monitoramento (6/10): Custom Prometheus(NIH) → prometheus_client+structlog+OpenTelemetry
  - **Camadas sólidas (7-8/10):** Database (SQLite WAL+Postgres+SQLAlchemy+Alembic+sqlglot), Infra (Docker+Traefik+Authentik), Eventos (EventBus+Redis Streams+Transactional Outbox), Auth (JWT+OIDC+Authentik), Testes (pytest+16 gates)
  - **Upgrade de maior ROI:** Migrar server.py para FastAPI — elimina 500+ linhas de NIH sem adicionar dependência nova (FastAPI+uvicorn já estão em requirements.txt)
- **2025-07-19 — Implementações realizadas pós-auditoria:**
  - **server_fastapi.py criado** (535 linhas vs. 989 do http.server original = **-46% de código**)
    - FastAPI nativo com OpenAPI 3.1 automático (elimina RouteRegistry para docs)
    - Pydantic models para validação de body (elimina body_schema manual)
    - OWASP headers via middleware (elimina handler manual de 200+ linhas)
    - CORS configurável via env var
    - ReDoc (/redoc) como segunda opção de docs
    - Uvicorn async server (substitui ThreadingTCPServer)
  - **metrics.py atualizado** para dual-path: prometheus_client (battle-tested) com fallback NIH
    - prometheus_client já está instalado — fallback nunca será used em produção
    - Elimina ~100 linhas de código NIH em runtime
  - **Notas pós-implementação:** Backend 5→8 (+3), Monitoramento 6→7 (+1)
- **2025-07-19 — PLAN-0028 Executado (6/6 itens concluídos):**
  - **Frontend:** React 19+Vite+shadcn/ui SPA (4→8). 32 arquivos, 6 pages, 9 UI components, 5 hooks. Build 130KB gzipped.
  - **Auth:** JWT migrado para PyJWT + Argon2id (7→8). 8 testes de integração passando.
  - **Testes:** 16 property-based tests com Hypothesis (7→9). 37/37 testes verdes.
  - **Observabilidade:** logging_config.py (structlog + OpenTelemetry) + server_fastapi.py v6.1 (7→9).
  - **Database:** AsyncPostgresAdapter + asyncpg para PostgreSQL async (8→9).
  - **Eventos:** RedisBLPOPWorker já existente confirmado (outbox_worker.py v5.2, 431 linhas).
- **2026-09-16 — Integração Canônica de Skills Procedimentais de Engenharia (PLAN-0030):**
  - Integração das 7 skills procedimentais de engenharia inspiradas nas práticas de Matt Pocock, adaptadas para serem 100% poliglotas e concisas:
    - `/aidd-grill` e `/aidd-grill-docs`: entrevista socrática e alinhamento pré-código (com fallback não-bloqueante para pipelines autônomos).
    - `/aidd-spec` e `/aidd-tickets`: especificação formal determinística e decomposição atômica tracer-bullet.
    - `/aidd-tdd`: ciclo Red-Green-Refactor poliglota com tolerância zero a stubs.
    - `/aidd-diagnose`: método científico de 5 fases para triage de bugs integrado ao `code-review-graph`.
    - `/aidd-handoff`: serialização compacta de sessão salva diretamente em `secoes/`.
  - Todas as 7 skills criadas estritamente em **Compact English** na fonte canônica `componentes/compartilhado/skills/` (padrão Core para economia de tokens BPE).
  - Sincronização e verificação física multi-harness em 7 ambientes (.agents, .claude, .cursor, .gemini, .opencode, .mimocode, .codebuddy) com 100% de hashes SHA-256 validados via `python ecossistema.py components verify --tipo skill`.
  - Vinculação formal nos `AGENTS.md` das ferramentas `aidd-generator` (Fases 1 e 2), `aidd-master` (Vertical Slices), `aidd-enterprise` (Selo TDD) e `aidd-ops` (Diagnose).
  - Plano oficial arquivado em `docs/planos/feitos/PLAN-0030-integracao-skills-matt-pocock/plano.md`.
- **2026-09-21 — Orquestração de Pipeline e Meso-Camada da Tríade Canônica (VSA Topological Dispatch):**
  - **Iniciativa Pipeline de Orquestração (`docs/issues/pipeline-orquestracao-triade/` — 7/7 tickets DONE):**
    - Schema canônico `handoff-execucao.schema.json` e Quality Gate `G_PIPELINE_HANDOFF` com prova que morde (`exit 1`).
    - Motor determinístico em Git Worktrees efêmeras (`tools/aidd-master/scripts/orchestrator_pipeline.py`) com Join Barrier e limpeza de 100% dos recursos em `try-finally`.
    - Compilador de planos Markdown (`scripts/compilador_tickets_plano.py`) e exportador nativo em `aidd-planner`.
    - Skill canônica multi-harness `aidd-pipeline-runner` e comandos universais `/run-plan` e `/pipeline`.
  - **Iniciativa Meso-Camada da Tríade Canônica (`docs/issues/meso-camada-triade-canonica/` — 8/8 tickets DONE):**
    - Schema formal `vsa-topological-dispatch.schema.json` e Quality Gate `G_DISPATCH_PIPELINE_VSA` com prova que morde (10/10 testes PASS).
    - Compilador topológico DAG VSA em `aidd-planner` com algoritmo de Kahn e detecção mecânica de ciclos.
    - Motor de despacho topológico `tools/aidd-master/scripts/dispatch_pipeline.py` com isolamento estrito de fatias em Git Worktrees efêmeras (`.worktrees/<slice_id>`).
    - Roteador especialista de engines da Tríade (`tools/aidd-master/scripts/engine_router.py`) com injeção do Quarteto Sine Qua Non (`/docs`, `/webhooks`, `/mcp`, `/docs/guia`).
    - Barreira de validação e convergência master (`tools/aidd-master/scripts/vsa_join_barrier.py`) com validação de fronteiras de arquivos via `git status --porcelain -uall` e manifesto com SHA-256 para `aidd-enterprise`.
    - Integração no `scripts/orquestrador_sincrono.py` eliminando stubs/mocks estáticos e exposição do comando CLI `python ecossistema.py dispatch`.
    - Skill canônica multi-harness `aidd-dispatch-runner` e encadeamento de intake formal `/aidd-grill` ➔ `/aidd-spec` ➔ `/aidd-planner` ➔ `/aidd-dispatch-runner`.
  - **Evolução da Taxonomia do Quarteto Sine Qua Non (`PLAN-0036`):**
    - Atualização da Lei #10: de `[/docs, /webhooks, /mcp, /docs/guia]` para a convenção canônica `[/api, /webhook, /mcp, /docs]`.
    - `/api` passa a ser a rota oficial do OpenAPI/Swagger Studio.
    - `/webhook` passa a ser a rota do Webhook Studio (mantendo `/webhooks` como fallback).
    - `/mcp` permanece a rota do MCP Studio.
    - `/docs` é promovido a Central de Documentação e Guia do Utilizador Humano.


## 7. INICIATIVAS ATIVAS (gerado automaticamente — não editar à mão)

> Bloco reescrito por `python scripts/atualizar_index_planos.py` toda vez que `docs/planos/` muda (via `.githooks/pre-commit`). Reflete o mesmo cálculo de status de `docs/planos/INDEX.md` — nunca edite manualmente, o script sobrescreve.

<!-- AUTO:INICIATIVAS:START -->
- 🔒 **Teste E2E Ferramentas** — `docs/planos/a-fazer/PLAN-0029-teste-e2e-ferramentas/`
- 🔶 **Qualidade Testes Mutacao** — `docs/planos/fazendo/PLAN-0016-qualidade-testes-mutacao/`
- 🔶 **Resiliencia Concorrencia Integridade** — `docs/planos/fazendo/PLAN-0017-resiliencia-concorrencia-integridade/`
- 🔶 **Seguranca Zero Trust** — `docs/planos/fazendo/PLAN-0018-seguranca-zero-trust/`
- 🔶 **Bootstrap Ambiente Preflight** — `docs/planos/fazendo/PLAN-0019-bootstrap-ambiente-preflight/`
- 🔶 **Codigo Limpo Profundo** — `docs/planos/fazendo/PLAN-0021-codigo-limpo-profundo/`
- 🔶 **Config Arquivos Tokens** — `docs/planos/fazendo/PLAN-0022-config-arquivos-tokens/`
- 🔶 **Evolucao Engenharia Software** — `docs/planos/fazendo/PLAN-0023-evolucao-engenharia-software/`
- 🔶 **Conclusao Auditoria Maquiagem** — `docs/planos/fazendo/PLAN-0025-conclusao-auditoria-maquiagem/`
- ⏳ **Implementacao Aidd Factory** — `docs/planos/fazendo/PLAN-0027-implementacao-aidd-factory/`
- ⏳ **Completude Factory V2** — `docs/planos/fazendo/PLAN-0028-completude-factory-v2/`
- 🔶 **Upgrade Ferramentas Enterprise** — `docs/planos/fazendo/PLAN-0034-upgrade-ferramentas-enterprise/`
- ⏳ **Direcionamento Estrategico Anti Nih** — `docs/planos/feitos/PLAN-0010-direcionamento-estrategico-anti-nih/`
- ⏳ **Otimizacao Tokenomics Latencia** — `docs/planos/feitos/PLAN-0015-otimizacao-tokenomics-latencia/`
- ⏳ **Testes Motor Orquestrador** — `docs/planos/feitos/PLAN-0024-testes-motor-orquestrador/`
- ⏳ **Upgrade Stack Camadas** — `docs/planos/feitos/PLAN-0028-upgrade-stack-camadas/`
- ⏳ **Taxonomia Quarteto Sine Qua Non** — `docs/planos/feitos/PLAN-0036-taxonomia-quarteto-sine-qua-non/`
<!-- AUTO:INICIATIVAS:END -->
