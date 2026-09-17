# 🧠 MEMORY.md — Memória Estruturada e Contexto Operacional Consolidado

> **Repositório:** `https://github.com/heverton-dev/ecossistema-aidd`  
> **Última Atualização:** 2026-09-10  
> **Status:** PRODUÇÃO & ORQUESTRADO (ORCA ADE / ORC 3)  
> **Finalidade:** Memória persistente de longo prazo para guiar desenvolvedores e agentes de IA em qualquer harness, evitando amnésia de contexto e retrabalho.

---

## 1. IDENTIDADE E ARQUITETURA DO ECOSSISTEMA

O **Ecossistema AIDD** é um monorepo agnóstico que integra 7 ferramentas complementares de Engenharia Agêntica de Software:

- **AIDD Forge (`tools/aidd-forge`):** Bootstrap de governança, isolamento de fases e purge de contexto (`/forge`).
- **AIDD Generator (`tools/aidd-generator`):** Fábrica autônoma com pipeline de 8 fases e contratos JSON Schema (`/generate`).
- **AIDD Master (`tools/aidd-master`):** Monólito modular com fatias verticais, SQLite WAL e Result Monad (`/master`).
- **AIDD Enterprise (`tools/aidd-enterprise`):** Missão crítica com injeção de componentes SHA-256 e Zero-Trust (`/enterprise`).
- **AIDD Ops (`tools/aidd-ops`):** Meta-Orquestrador Agêntico de Infraestrutura (IaC, sizing de hardware, Helm, Ansible, Docker Swarm, `/ops`).
- **AIDD Factory (`tools/aidd-factory`):** Gerador de código de aplicação e integração para stacks multi-serviço (Gateway FastAPI BFF, Frontend Next.js, webhooks, compose unificado, `/factory`).
- **AIDD Bridge (`tools/aidd-bridge`):** Extrator, unificador e empacotador de projetos Low-Code (Lovable/Supabase) para VPS própria com PostgreSQL puro, PostgREST, Traefik/Kong e Docker Compose (`/bridge`).

**Fonte Física Canônica Única:** Todo componente (`skill`, `command`, `mcp`, `hook`, `spec`) reside estritamente em `componentes/<escopo>/<tipo>/`. As pastas `.agent/`, `.claude/`, `.gemini/`, `.agents/`, `skills/` são alvos de materialização gerados pelo script `scripts/gestor_componentes.py` (`python ecossistema.py components sync`).

---

## 2. AS 10 REGRAS DE OURO INEGOCIÁVEIS (`AGENTS.md`)

1. **Determinismo Primeiro (Zero Token Fallacy):** Nunca usar LLM para tarefas mecânicas determinísticas (usar scripts Python, AST, regex, JSON Schema).
2. **Qualidade Binária (Gates Determinísticos):** Toda validação produz saída binária (`exit 0` = aprovado, `exit 1` = bloqueado).
3. **Persistência Estruturada e Transparência Total:** Estado reside em arquivos auditáveis (JSON, SQLite WAL, Git), nunca na memória volátil do chat.
4. **Economia Extrema de Tokens (Tríade Caveman Ultra):** Thinking telegráfico Caveman, saídas concisas em PT-BR, purge de contexto entre fases.
5. **Zero Stubs / Zero Mocks Falsos em Produção:** Código gerado deve ser funcional, tipado e com testes reais.
6. **Supremacia Agnóstica (Universalidade Total):** Nenhuma dependência proprietária ou lock-in. Suporte idêntico entre sistemas operacionais (Windows, Linux, macOS) e harnesses (Claude Code, Antigravity, OpenCode, MimoCode, Gemini CLI, Hermes, Cursor).
7. **Desenvolvedor no Controle (Zero Subagentes Headless Paralelos):** Proibido disparar subagentes invisíveis em segundo plano (`invoke_subagent` ou subprocessos desassistidos). Execução sequencial governada pelo desenvolvedor no terminal.
8. **Anti-NIH (Not Invented Here):** Antes de escrever mecanismo novo com mais de 30-50 linhas para problema genérico, justificar por escrito por que nenhuma ferramenta OSS madura resolve.
9. **Honestidade de Rótulo:** Nenhuma mensagem de saída pode usar alegações de segurança/certificação maiores que a cobertura real testada. Verificado por `G_HONESTIDADE_ROTULO.py`.
10. **Comunicação Direta, Sem Jargão e Sem Formalidade:** Respostas diretas, sem rodeios, alta densidade e organização visual em tópicos/tabelas/negrito.

---

## 3. OS 11 META-QUALITY GATES UNIFICADOS (`python ecossistema.py audit`)

| Gate | Arquivo | Responsabilidade |
|---|---|---|
| **G1** | `gates/G_ECOSSISTEMA_INTEGRIDADE.py` | Audita presença estrutural, sintaxe Python (AST) e integridade dos subprojetos. |
| **G2** | `gates/G_DRIFT_NUCLEO_COMPARTILHADO.py` | Detecta divergências entre o núcleo compartilhado `aidd-master` e `aidd-enterprise`. |
| **G3** | `gates/G_HARNESS_COMPAT.py` | Garante sincronismo universal de componentes e correspondência entre gates e documentação. |
| **G4** | `gates/G_SEGREDOS.py` | Varredura de credenciais e tokens expostos via detect-secrets (stage manual). |
| **G5** | `gates/G_CLI_HELP_CONSISTENCIA.py` | Compara flags mencionadas em mensagens contra argumentos reais CLI. |
| **G6** | `gates/G_COMPONENTE_AGNOSTICO.py` | Audita integridade e cobertura multi-harness de componentes novos ou modificados. |
| **G7** | `gates/G_ZERO_HEADLESS.py` | Garante modo interativo mandatório e bloqueia execução headless oculta. |
| **G8** | `gates/G_INFRA_COMPOSE.py` | Audita integridade, sintaxe e segurança de Docker Compose (Checkov + PyYAML). |
| **G9** | `gates/G_HADOLINT.py` | Audita boas práticas e sintaxe OCI em Dockerfiles via Hadolint. |
| **G10** | `gates/G_TESTES_REAIS.py` | Roda pytest real em cada ferramenta e bloqueia se failed > 0. |
| **G11** | `gates/G_HONESTIDADE_ROTULO.py` | Verifica ausência de termos de marketing não comprovados por testes reais. |

---

## 4. MATRIZ DE SLASH COMMANDS UNIVERSAIS

| Slash Command | Skill Subjacente | CLI Universal Equivalente | Função |
|---|---|---|---|
| `/forge [caminho]` | `aidd-forge-runner` | `python ecossistema.py forge init [caminho]` | Bootstrap e blindagem de governança em novos projetos. |
| `/generate <ideia>` | `aidd-generator-runner` | `python ecossistema.py generate "<ideia>"` | Disparo da fábrica de 8 fases a partir de ideia. |
| `/master <modulo>` | `aidd-master-runner` | `python ecossistema.py master add-module <modulo>` | Criação de fatia vertical desacoplada em monólito modular. |
| `/enterprise <tipo> <nome>` | `aidd-enterprise-runner` | `python ecossistema.py enterprise inject <tipo> <nome>` | Injeção de componentes corporativos certificados SHA-256. |
| `/ops [requisito]` | `aidd-ops-runner` | `python ecossistema.py ops [requisito]` | Meta-Orquestrador de Infraestrutura: VPS, Docker, SSH, deploy. |
| `/orchestrate [plano]` | `orca-plan-orchestrator` | `python ecossistema.py orchestrate [plano]` | ORCA ADE — orquestração de planos de desenvolvimento via worktrees efêmeras. |
| `/plan <nome>` | `planos-auditoria-runner` | `python ecossistema.py plan init <nome>` | Estruturação determinística de planos de auditoria e evolução. |
| `/bridge [comando]` | `aidd-bridge-runner` | `python ecossistema.py bridge [scan\|convert-db\|merge\|pack]` | Extrai, unifica e empacota apps Lovable/Supabase para VPS com PostgREST e Docker. |
| `/aidd-grill` | `aidd-grill` | N/A (Chat Interativo / Headless Fallback) | Entrevista socrática pré-código para alinhamento de invariantes e edge cases. |
| `/aidd-grill-docs` | `aidd-grill-docs` | N/A (Chat Interativo) | Questionamento socrático ancorado em MEMORY.md e governança local. |
| `/aidd-spec` | `aidd-spec` | N/A (Chat / Plan Generator) | Especificação técnica determinística com não-escopos e critérios binários. |
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

## 7. INICIATIVAS ATIVAS (gerado automaticamente — não editar à mão)

> Bloco reescrito por `python scripts/atualizar_index_planos.py` toda vez que `docs/planos/` muda (via `.githooks/pre-commit`). Reflete o mesmo cálculo de status de `docs/planos/INDEX.md` — nunca edite manualmente, o script sobrescreve.

<!-- AUTO:INICIATIVAS:START -->
- ⏳ **Testes Motor Orquestrador** — `docs/planos/PLAN-0024-testes-motor-orquestrador/`
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
- ⏳ **Upgrade Stack Camadas** — `docs/planos/feitos/PLAN-0028-upgrade-stack-camadas/`
<!-- AUTO:INICIATIVAS:END -->
