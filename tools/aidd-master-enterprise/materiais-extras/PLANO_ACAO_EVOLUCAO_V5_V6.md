# Plano de Ação Estruturado: Evolução Arquitetural AIDD (v4 -> v5 / v6)

> **Documento de Engenharia:** Plano de Ação e Execução Técnica para as Próximas Fases.  
> **Base Estratégica:** `ANALISE_TECNICA_E_POSICIONAMENTO_REALISTA.md` e `MATRIZ_QUALIDADE_ATOMICA_V4.md`.  
> **Diretrizes Inegociáveis:** Determinismo Matemático, Zero Acoplamento, 100% de Testabilidade e Economia Extrema de Tokens.

---

## 1. Visão Geral das 4 Ondas de Implementação

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                     CRONOGRAMA E ONDAS DE EVOLUÇÃO (v5 e v6)                     │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ONDA 1: PERSISTÊNCIA POLIGLOTA & TRANSACTIONAL OUTBOX (v5.0-Alpha)              │
│  ├── Iniciativa 1.1: Driver Abstrato de Banco (DatabaseAdapter: SQLite/Postgres) │
│  └── Iniciativa 1.2: Transactional Outbox Pattern (_outbox_events)               │
│                                                                                  │
│  ONDA 2: MENSAGERIA DISTRIBUÍDA & JOBS RESILIENTES (v5.0-Beta)                   │
│  ├── Iniciativa 2.1: Distributed EventBus com Redis Streams / NATS               │
│  └── Iniciativa 2.2: JobQueue Persistente com Retentativas e Dead Letter Queue   │
│                                                                                  │
│  ONDA 3: FRONT-END HÍBRIDO & ENTERPRISE IDENTITY (v5.0-Release)                  │
│  ├── Iniciativa 3.1: Exportador Next.js / React TypeScript (--frontend nextjs)   │
│  └── Iniciativa 3.2: Autenticação Corporativa SSO (OAuth2 / OIDC & RBAC)         │
│                                                                                  │
│  ONDA 4: IA RECURSIVA BDD & CLOUD NATIVE IaC (v6.0-Enterprise)                   │
│  ├── Iniciativa 4.1: Subagente de Refinamento de Domínio com BDD (Behave/Gherkin)│
│  ├── Iniciativa 4.2: Orquestração Declarativa Kubernetes Helm & Terraform IaC    │
│  └── Iniciativa 4.3: Telemetria OpenTelemetry & Métricas Prometheus (/metrics)   │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Detalhamento Técnico das Iniciativas

---

### ONDA 1: Persistência Poliglota & Resiliência Transacional

#### Iniciativa 1.1: Driver Abstrato de Banco de Dados (`DatabaseAdapter`)
- **O Que Fazer:**  
  Refatorar `src/core/database.py` para utilizar o padrão *Bridge/Adapter*, suportando SQLite WAL local e PostgreSQL/Supabase remoto de forma transparente através da mesma interface de repositório.
- **Por Que Fazer:**  
  Permite que a aplicação nasça em SQLite para desenvolvimento local com zero atrito e migre para PostgreSQL em produção com uma única variável de ambiente (`DATABASE_URL`), sem alterar uma única linha de código nos módulos.
- **Como Fazer:**
  1. Definir a interface abstrata `DatabaseAdapter` com métodos `get_connection()`, `execute()`, `fetchall()`, `init_schema()`.
  2. Implementar `SQLiteAdapter` (nativo) e `PostgresAdapter` (usando `psycopg3` ou `pg8000`).
  3. Atualizar o comando CLI: `python scripts/aidd.py compose --db [sqlite|postgres]`.
- **Quality Gate Validador:** `G_ESTRUTURA` e `G_TESTES` (rodando contra banco efêmero).
- **Critério de Aceite:** 100% dos testes unitários de `services.py` passam sem modificação em ambos os drivers.

---

#### Iniciativa 1.2: Transactional Outbox Pattern (`_outbox_events`)
- **O Que Fazer:**  
  Garantir que qualquer mutação de estado e seu respectivo evento no `EventBus` sejam gravados atomicamente na mesma transação SQL dentro da tabela `_outbox_events`.
- **Por Que Fazer:**  
  Elimina o problema de *Dual-Write* (onde o banco é atualizado, mas o envio do evento/webhook falha por queda de rede ou reinicialização do processo), assegurando entrega garantida (*At-Least-Once Delivery*).
- **Como Fazer:**
  1. Criar tabela `_outbox_events (id TEXT, event_name TEXT, payload JSON, status TEXT, criado_em TEXT, processado_em TEXT)`.
  2. Nos métodos `criar()`, `atualizar()` e `deletar()` de `services.py`, inserir o registro no outbox dentro do bloco `with conn:`.
  3. Criar um worker leve em `src/core/outbox_worker.py` que lê eventos pendentes e despacha para os listeners.
- **Quality Gate Validador:** `G_TESTES` e `G_SEGURANCA`.
- **Critério de Aceite:** Simulação de interrupção de processo com recuperação e despacho 100% íntegro de eventos pendentes.

---

### ONDA 2: Mensageria Distribuída & Background Workers

#### Iniciativa 2.1: Distributed EventBus com Driver Redis Streams / NATS
- **O Que Fazer:**  
  Adicionar ao `src/core/events.py` suporte a brokers de mensageria distribuída (Redis Streams ou NATS) quando configurado via `EVENTBUS_URL`.
- **Por Que Fazer:**  
  Permite escalar o sistema horizontalmente em múltiplos containers/instâncias sem perder a sincronização de eventos entre fatias verticais.
- **Como Fazer:**
  1. Criar interface `EventBusDriver` com implementações: `InMemoryEventBusDriver` (padrão) e `RedisStreamsDriver`.
  2. Implementar grupos de consumidores (*Consumer Groups*) para distribuição de carga entre instâncias.
- **Quality Gate Validador:** `G_HARNESS_COMPAT` e `G_CONTRACTS`.
- **Critério de Aceite:** Evento emitido na Instância A é processado com sucesso pelo listener na Instância B.

---

#### Iniciativa 2.2: JobQueue Persistente com Dead Letter Queue (DLQ)
- **O Que Fazer:**  
  Evoluir `src/core/jobs.py` para armazenar o estado das tarefas em tabela SQLite/PostgreSQL (`_jobs`), com política de retentativas exponenciais (3 tentativas) e encaminhamento para *Dead Letter Queue* em caso de falha definitiva.
- **Por Que Fazer:**  
  Garante que disparos de webhooks externos, relatórios pesados e integrações com terceiros sejam executados com tolerância a falhas e visibilidade para suporte.
- **Como Fazer:**
  1. Criar tabela `_jobs (id, func, args, status, tentativas, max_tentativas, proxima_execucao, erro)`.
  2. Implementar backoff exponencial: $t_{retry} = 2^{tentativa} \times 5s$.
  3. Expor painel de jobs em `/jobs` para inspeção e reprocessamento manual.
- **Quality Gate Validador:** `G_TESTES` e `G_QUALIDADE`.
- **Critério de Aceite:** Tarefa com erro simulado tenta 3 vezes com intervalo crescente antes de ir para status `DLQ`.

---

### ONDA 3: Front-End Híbrido & Enterprise Identity

#### Iniciativa 3.1: Exportador de Componentes Next.js / TypeScript
- **O Que Fazer:**  
  Implementar na CLI a opção `python scripts/aidd.py export-frontend --stack nextjs`, gerando uma aplicação Next.js 14+ (App Router) com componentes tipados em TypeScript (`.tsx`) e Tailwind CSS.
- **Por Que Fazer:**  
  Permite que equipes que exigem ecossistema React/Next.js consumam as fatias verticais e APIs geradas com total tipagem gerada a partir dos esquemas OpenAPI 3.1.
- **Como Fazer:**
  1. Criar gerador de tipos TypeScript a partir de `openapi.json` (`src/openapi_to_ts.py`).
  2. Gerar páginas `app/<modulo>/page.tsx` com React Hook Form, TanStack Table e Lucide Icons consumindo as rotas `/api/<modulo>/*`.
- **Quality Gate Validador:** `G_ESTRUTURA` e `G_CONTRACTS`.
- **Critério de Aceite:** Build estático `next build` executa com código de saída 0 sem erros de lint ou tipagem.

---

#### Iniciativa 3.2: Autenticação Corporativa SSO (OAuth2 / OIDC & RBAC)
- **O Que Fazer:**  
  Evoluir `src/core/security.py` para suportar fluxo Authorization Code com PKCE para provedores OAuth2/OIDC (Google Workspace, Microsoft Entra ID, GitHub, Okta).
- **Por Que Fazer:**  
  Elimina a necessidade de senhas locais em ambientes corporativos e viabiliza a venda da solução para empresas que exigem SSO obrigatório.
- **Como Fazer:**
  1. Adicionar endpoints `/api/auth/oauth/login` e `/api/auth/oauth/callback`.
  2. Troca de authorization code por ID Token e validação criptográfica de chaves públicas JWKS.
  3. Mapeamento de grupos corporativos para os papéis do sistema (`admin`, `operador`, `leitor`).
- **Quality Gate Validador:** `G_SEGURANCA` (Camada 2).
- **Critério de Aceite:** Login simulado via mock OIDC gera token JWT assinado com claims de usuário corporativo.

---

### ONDA 4: IA Recursiva BDD & Cloud Native IaC

#### Iniciativa 4.1: Subagente de Refinamento de Domínio com BDD (`behave` / Gherkin)
- **O Que Fazer:**  
  Adicionar o subagente `agent_domain_refiner` e o comando `python scripts/aidd.py refine-module <modulo> --spec <arquivo.feature>`.
- **Por Que Fazer:**  
  Supera a limitação de gerar apenas CRUD genérico. O agente lê cenários comportamentais em Gherkin (`Dado que... Quando... Então...`) e implementa os cálculos e algoritmos de domínio em `services.py` até que a suíte BDD passe 100%.
- **Como Fazer:**
  1. Adicionar suporte a `behave` em `requirements.txt`.
  2. Criar pasta `features/<modulo>.feature` com cenários de aceite de negócio.
  3. Loop recursivo: o agente roda `behave features/<modulo>.feature`, inspeciona os passos falhos, edita `services.py` e reexecuta até `exit 0`.
- **Quality Gate Validador:** `G_TESTES` (com bateria BDD integrada).
- **Critério de Aceite:** 100% dos cenários Gherkin homologados com `exit 0`.

---

#### Iniciativa 4.2: Orquestração Declarativa Kubernetes Helm & Terraform IaC
- **O Que Fazer:**  
  Gerar automaticamente na pasta `infra/` os módulos Terraform para provisionamento de banco gerenciado e VPC, e charts Helm para deploy em clusters Kubernetes.
- **Por Que Fazer:**  
  Permite que o projeto passe do ambiente local para produção em escala global em qualquer nuvem (AWS, GCP, Azure, DigitalOcean) em minutos.
- **Como Fazer:**
  1. Gerar `infra/terraform/main.tf` com provisionamento de PostgreSQL e Redis.
  2. Gerar `infra/helm/values.yaml`, `deployment.yaml`, `service.yaml`, `ingress.yaml` e `hpa.yaml` (Horizontal Pod Autoscaler).
- **Quality Gate Validador:** `G_HARNESS_COMPAT`.
- **Critério de Aceite:** `helm lint` e `terraform validate` aprovados com 0 erros.

---

#### Iniciativa 4.3: Telemetria OpenTelemetry & Métricas Prometheus (`/metrics`)
- **O Que Fazer:**  
  Expor endpoint nativo `/metrics` no formato Prometheus e instrumentar requisições HTTP e eventos com spans OpenTelemetry.
- **Por Que Fazer:**  
  Garante observabilidade de nível militar em produção, monitorando latência P95/P99, taxa de erros 5xx, throughput de requisições e saturação do banco de dados.
- **Como Fazer:**
  1. Implementar contador de requisições, histograma de latência e medidor de conexões abertas no SQLite/PostgreSQL.
  2. Expor métricas padronizadas em `GET /metrics` sem impacto na latência de aplicação (< 0.1ms overhead).
- **Quality Gate Validador:** `G_SEGURANCA` e `G_QUALIDADE`.
- **Critério de Aceite:** Endpoint `/metrics` retorna métricas válidas e interpretáveis por scraper Prometheus.

---

## 3. Matriz Consolidada de Execução e Responsabilidades

| Onda | Iniciativa | Arquivos Afetados | Complexidade | Versão Alvo |
| :---: | :--- | :--- | :---: | :---: |
| **1** | **1.1 DatabaseAdapter Poliglota** | `src/core/database.py`, `compose_suite.py` | Média | **v5.0-Alpha** |
| **1** | **1.2 Transactional Outbox Pattern** | `services.py`, `src/core/outbox_worker.py` | Baixa | **v5.0-Alpha** |
| **2** | **2.1 Distributed EventBus (Redis)** | `src/core/events.py` | Média | **v5.0-Beta** |
| **2** | **2.2 JobQueue Persistente & DLQ** | `src/core/jobs.py`, `src/server.py` | Média | **v5.0-Beta** |
| **3** | **3.1 Exportador Next.js TypeScript** | `scripts/aidd.py`, `src/openapi_to_ts.py` | Média | **v5.0-Release** |
| **3** | **3.2 Enterprise SSO (OAuth2 / OIDC)** | `src/core/security.py`, `src/server.py` | Alta | **v5.0-Release** |
| **4** | **4.1 IA BDD Domain Refiner** | `templates/agents/`, `scripts/aidd.py` | Alta | **v6.0-Enterprise** |
| **4** | **4.2 Kubernetes Helm & Terraform IaC** | `infra/helm/`, `infra/terraform/` | Média | **v6.0-Enterprise** |
| **4** | **4.3 OpenTelemetry & Prometheus** | `src/core/metrics.py`, `src/server.py` | Baixa | **v6.0-Enterprise** |

---

## 4. Como Ativar e Executar Este Plano no Futuro

Quando formos iniciar o ciclo de desenvolvimento das versões v5 ou v6:
1. **Comando de Retomada:** Abra o chat e aponte para este documento:
   `"Vamos iniciar a execução da Onda X do PLANO_ACAO_EVOLUCAO_V5_V6.md"`.
2. **Execução Isolada por Worktree / Mesa:** O Maestro criará uma branch/worktree dedicada para cada iniciativa, garantindo zero contaminação de contexto.
3. **Validação Contínua por Gates:** Nenhuma iniciativa será dada como concluída sem validação dos 7 Quality Gates locais (`python scripts/aidd.py audit --report`) com Exit Code 0.

---

## 5. A Experiência Fluida de Ponta a Ponta (Do Clone à Entrega em Produção)

O maior diferencial das versões v5 e v6 é transformar a arquitetura distribuída e corporativa em uma **experiência de usuário totalmente fluida, natural e com zero atrito cognitivo**.

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                          A JORNADA DO USUÁRIO NAS VERSÕES v5 E v6                                      │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                        │
│  FASE 0: BOOTSTRAP INVISÍVEL (Zero Setup / Smart Environment Detection)                                │
│  ├── Usuário clona o repositório ou abre a pasta.                                                      │
│  ├── Detecção automática de runtime: Python, Docker, PostgreSQL, Redis, Kubernetes ou ORCA.           │
│  └── Se nada estiver instalado: O sistema opera 100% autônomo em modo Local Embedded (Zero Config).    │
│                                                                                                        │
│  FASE 1: ENTRADA EM LINGUAGEM NATURAL PURA (Zero Atrito & Zero Flags Técnicas)                         │
│  ├── Usuário digita no chat: "Crie um ERP de vendas e faturamento com envio de boletos e relatórios". │
│  ├── O Maestro deduz os domínios, entidades DDD, eventos necessários e adapters recomendados.         │
│  └── Nenhuma exigência de comandos complexos ou configurações manuais de JSON.                         │
│                                                                                                        │
│  FASE 1.5: SPEC GATE CONVERSACIONAL (Alinhamento em 3 Níveis)                                          │
│  ├── Geração em segundos do SPEC em 3 níveis (Negócio, Backend e Frontend/UX).                         │
│  ├── O usuário revisa e pode iterar por conversa: "Adicione desconto progressivo para compras > 500".   │
│  └── Ao responder "Aprovado" ou "Pode criar", dispara automaticamente a esteira mecânica.              │
│                                                                                                        │
│  FASE 2: PROCESSAMENTO MECÂNICO & IA RECURSIVA (Execução Silenciosa e Blindada)                        │
│  ├── Scaffolding atômico das fatias verticais, Transactional Outbox e adaptadores poliglotas.          │
│  ├── Subagente de Domínio (BDD) implementa regras complexas guiado por cenários Gherkin.               │
│  ├── Execução em background via subprocessos/worktrees sem poluir o chat do usuário.                   │
│  └── Homologação obrigatória dos 7 Quality Gates + Benchmark de latência (< 5ms) e auto-cura.          │
│                                                                                                        │
│  FASE 3: ENTREGA IMEDIATA & OPERAÇÃO MULTI-PORTAL                                                      │
│  ├── Servidor sobe em porta livre (Port Fallback automático).                                          │
│  ├── 6 Portais disponíveis:                                                                            │
│  │   ├── 1. Super-App UI / Next.js (http://localhost:3000/)                                            │
│  │   ├── 2. Swagger Studio OpenAPI 3.1 (http://localhost:3000/docs)                                    │
│  │   ├── 3. Model Context Protocol (http://localhost:3000/mcp)                                         │
│  │   ├── 4. Webhook Studio HMAC SHA-256 (http://localhost:3000/webhooks)                                │
│  │   ├── 5. Background Jobs & DLQ (http://localhost:3000/jobs)                                         │
│  │   └── 6. Métricas Prometheus (/metrics)                                                             │
│  └── Relatório Factual Auditado (Score 100% Nota A+ Cibersegurança e Concorrência).                     │
│                                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### Comparativo de Fluidez: v5.1 vs v5 / v6

| Etapa do Fluxo | Versão v5.1 (Atual) | Versão v5 / v6 (Evolução Fluida) |
| :--- | :--- | :--- |
| **Clone & Setup** | Exige `python scripts/aidd.py setup` para pre-flight e pacotes. | **Zero Setup:** O bootstrap roda no primeiro input e autodetecta PostgreSQL/Docker/Redis se existirem. |
| **Entrada do Usuário** | Aceita prompt natural para planejar fatias CRUD básicas. | **Intenção Completa:** Aceita prompts de regras complexas, inferindo stack (Vanilla vs Next.js) e banco. |
| **Refinamento do Plano** | Usuário edita manualmente ou aprova o plano geral. | **Refinamento Conversacional:** O usuário pede ajustes na conversa e a IA reescreve apenas os deltas da SPEC. |
| **Processamento** | Geração estática de CRUD + 7 Gates mecânicos em ~5s. | **Processamento Híbrido:** Scaffolding mecânico + Subagente BDD para cálculos complexos + 7 Gates. |
| **Entrega** | 4 Portais (UI Vanilla, Swagger, MCP, Webhooks) + SQLite. | **6 Portais Enterprise:** UI Híbrida (Vanilla/Next.js), Swagger, MCP, Webhooks, Jobs e Prometheus. |

*Plano de Ação estruturado, homologado e salvo para execução estratégica imediata nas próximas versões.*

