# 🧠 MEMORY.md — Memória Estruturada e Contexto Operacional Consolidado

> **Repositório:** `https://github.com/heverton-dev/ecossistema-aidd`  
> **Última Atualização:** 2026-09-10  
> **Status:** PRODUÇÃO & ORQUESTRADO (ORCA ADE / ORC 3)  
> **Finalidade:** Memória persistente de longo prazo para guiar desenvolvedores e agentes de IA em qualquer harness, evitando amnésia de contexto e retrabalho.

---

## 1. IDENTIDADE E ARQUITETURA DO ECOSSISTEMA

O **Ecossistema AIDD** é um monorepo agnóstico que integra 6 ferramentas complementares de Engenharia Agêntica de Software:

- **AIDD Forge (`tools/aidd-forge`):** Bootstrap de governança, isolamento de fases e purge de contexto (`/forge`).
- **AIDD Generator (`tools/aidd-generator`):** Fábrica autônoma com pipeline de 8 fases e contratos JSON Schema (`/generate`).
- **AIDD Master (`tools/aidd-master`):** Monólito modular com fatias verticais, SQLite WAL e Result Monad (`/master`).
- **AIDD Enterprise (`tools/aidd-enterprise`):** Missão crítica com injeção de componentes SHA-256 e Zero-Trust (`/enterprise`).
- **AIDD Ops (`tools/aidd-ops`):** Meta-Orquestrador Agêntico de Infraestrutura (IaC, sizing de hardware, Helm, Ansible, Docker Swarm).
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

## 7. INICIATIVAS ATIVAS (gerado automaticamente — não editar à mão)

> Bloco reescrito por `python scripts/atualizar_index_planos.py` toda vez que `docs/planos/` muda (via `.githooks/pre-commit`). Reflete o mesmo cálculo de status de `docs/planos/INDEX.md` — nunca edite manualmente, o script sobrescreve.

<!-- AUTO:INICIATIVAS:START -->
- ⏳ **Otimizacao Tokenomics Latencia** — `docs/planos/a-fazer/02-otimizacao-tokenomics-latencia/`
- ⏳ **Qualidade Testes E Mutacao** — `docs/planos/a-fazer/03-qualidade-testes-e-mutacao/`
- ⏳ **Resiliencia Concorrencia E Integridade** — `docs/planos/a-fazer/04-resiliencia-concorrencia-e-integridade/`
- ⏳ **Seguranca Zero Trust E Supply Chain** — `docs/planos/a-fazer/05-seguranca-zero-trust-e-supply-chain/`
- ⏳ **Bootstrap Ambiente E Preflight Host** — `docs/planos/a-fazer/06-bootstrap-ambiente-e-preflight-host/`
- 🔒 **Evolucao Engenharia Software Ecossistema** — `docs/planos/a-fazer/evolucao-engenharia-software-ecossistema/`
- 🔶 **Correcao Pos Auditoria Sem Maquiagem** — `docs/planos/fazendo/01-correcao-pos-auditoria-sem-maquiagem/`
- 🔶 **Codigo Limpo Profundo Ecossistema** — `docs/planos/fazendo/codigo-limpo-profundo-ecossistema/`
<!-- AUTO:INICIATIVAS:END -->
