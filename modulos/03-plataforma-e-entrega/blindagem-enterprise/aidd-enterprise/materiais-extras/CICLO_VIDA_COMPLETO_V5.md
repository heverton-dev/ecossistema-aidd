# Ciclo de Vida Completo do AIDD Master Pack v5.1 (Nível Mission-Critical — Financial-Grade)

## 1. Visão Geral do Ciclo

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ FASE 0: ACESSO E INSTALAÇÃO NO AMBIENTE DO USUÁRIO                                  │
│ 1. Obtenção do Pacote: git clone heverton-dev/aidd-master-pack (branch v5.1.0) │
│ 2. Bootstrap Automático: pip install -r requirements.txt (behave, psycopg2, pyjwt)  │
│ 3. Verificação de Saúde: detecção de modo (SQLite local vs. PostgreSQL remoto)      │
│    $ python scripts/aidd.py setup                                                   │
└──────────────────────────────────────┬──────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ FASE 1: ENTRADA DO USUÁRIO (ZERO ATRITO — LINGUAGEM NATURAL OU DECLARATIVO)         │
│ Modo A (Linguagem Natural):                                                         │
│ $ python scripts/aidd.py "Criar sistema financeiro multi-tenant com CRM e ERP"      │
│                                                                                     │
│ Modo B (Declarativo com seleção de banco):                                          │
│ $ python scripts/aidd.py compose ./meu-projeto "Suite Financeira" crm erp --db postgres│
│                                                                                     │
│ Modo C (Adição de Módulo Isolado):                                                  │
│ $ python scripts/aidd.py add-module cobranca --dir ./meu-projeto                   │
└──────────────────────────────────────┬──────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ FASE 1.5: ESPECIFICAÇÃO & ALINHAMENTO ARQUITETURAL EM 3 NÍVEIS (SPEC GATE)          │
│ 1. Geração de SPEC-ARQUITETURA.md (Negócio, Backend, Frontend/UX)                  │
│ 2. Geração do Manifesto PLANO-EXECUCAO-ESTRUTURADO.json com estado da Saga         │
│ 3. Revisão Interativa: Usuário aprova ou ajusta fatias e entidades                  │
│ 4. Gatilho de Aprovação: $ python scripts/aidd.py apply --dir <pasta>              │
└──────────────────────────────────────┬──────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ FASE 2: PROCESSAMENTO MECÂNICO (ELITE AGENTIC ENGINE — MISSION-CRITICAL KERNEL)     │
│                                                                                     │
│  [BLOCO 2A — PERSISTÊNCIA POLIGLOTA & AUDITORIA IMUTÁVEL]                          │
│  1.  DatabaseAdapter (Bridge SQLite WAL ↔ PostgreSQL RETURNING id + SERIAL DDL)    │
│  2.  Transactional Outbox Pattern (_outbox_events) — At-Least-Once Delivery        │
│  3.  WORM Audit Hash Chain (_audit_log com SHA-256 encadeado — Merkle Tree)        │
│  4.  Row-Level Security (PostgreSQL: SET app.current_tenant_id + RLS Policy)       │
│  5.  Controle de Migrações (_schema_migrations idempotente + seed fixtures)        │
│                                                                                     │
│  [BLOCO 2B — REGRAS DE NEGÓCIO, RESILIÊNCIA E IDENTIDADE]                          │
│  6.  Result Pattern Monádico (Result.ok / Result.fail — zero falha 500)            │
│  7.  Saga Orchestrator (Compensating Transactions automáticas em fluxos longos)     │
│  8.  Circuit Breaker Dinâmico (CLOSED→OPEN→HALF_OPEN — fast-fail em serviços ext.) │
│  9.  JobQueue Resiliente (backoff 2ⁿ×5s + Dead Letter Queue + /api/jobs)           │
│  10. Token Revocation List (TRL com jti + TTL em memória — logout imediato)        │
│  11. SSO Corporativo OIDC + PKCE RFC-7636 (RS256 JWKS + RBAC por grupos)          │
│                                                                                     │
│  [BLOCO 2C — MENSAGERIA DISTRIBUÍDA & RASTREABILIDADE]                              │
│  12. EventBus Plugável (InMemory driver local / RedisStreamsDriver distribuído)     │
│  13. Consumer Groups Redis (XADD/XREADGROUP — entrega balanceada multi-nó)         │
│  14. Distributed Tracing (X-Correlation-ID propagado: HTTP→Outbox→Job→Log)        │
│  15. OutboxWorker em Background (polling ordenado + isolamento de exceções)         │
│                                                                                     │
│  [BLOCO 2D — CONTRATOS, FRONT-END E CQRS]                                          │
│  16. Singleton RouteRegistry (thread-safe — rotas compartilhadas entre módulos)    │
│  17. OpenAPI 3.1 dinâmico + Swagger Studio (/docs) + MCP JSON-RPC 2.0 (/mcp)      │
│  18. Super-App SPA Offline-First (CSS 100% embutido — zero CDN, SVGs com width/h) │
│  19. CQRS ReadModel + Stale-While-Revalidate (leitura em O(1), cache 30s SWR)     │
│  20. Local-First CRDTSet (Grow-Only Set — merge offline sem conflito)              │
│  21. Exportador Next.js 14/TypeScript (aidd export-frontend --stack nextjs)        │
│                                                                                     │
│  [BLOCO 2E — OBSERVABILIDADE, IaC E QUALITY GATES]                                 │
│  22. Métricas Prometheus nativas (/metrics — contadores, histogramas, overhead<0.1ms)│
│  23. Tripla Probe Kubernetes (/live, /ready, /startup) gerada no Helm chart        │
│  24. Gerador IaC Terraform AWS (VPC + RDS + ElastiCache) + Kubernetes Helm Chart   │
│  25. Refinador BDD Behave/Gherkin (gate RED/GREEN via aidd refine-module)          │
│  26. Scanner Anti-Stub AST + Linter WCAG 2.1 Impeccable UI                        │
│  27. Execução dos 7 Quality Gates (62 testes unitários — 54 core + 8 v5.1)        │
│  28. Snapshot SHA-256 de Contratos + Auditoria dos 4 Portais Web                  │
│  29. Benchmark Concorrente (aidd bench -n 100 → ≥1.600 RPS, 0 lock, <1ms/req)    │
│  30. Sincronização Multi-IDE (.cursor/, .claude/, .agent/) + CONTEXTO-PROJETO.md  │
└──────────────────────────────────────┬──────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ FASE 3: SAÍDA ENTREGUE, OPERACIONAL E AUDITADA (OUTPUT MISSION-CRITICAL)            │
│                                                                                     │
│  PORTAIS ATIVOS (todos offline-first, zero CDN):                                   │
│  ○ http://localhost:3000/          → Super-App SPA Dark Mode + Cards KPIs + CRUD   │
│  ○ http://localhost:3000/docs      → Swagger Studio (OpenAPI 3.1 interativo)       │
│  ○ http://localhost:3000/webhooks  → Webhook Studio (HMAC SHA-256 assinado)        │
│  ○ http://localhost:3000/mcp       → MCP Native Studio (JSON-RPC 2.0 para IAs)    │
│  ○ http://localhost:3000/metrics   → Telemetria Prometheus (live)                  │
│                                                                                     │
│  ARTEFATOS GERADOS NO PROJETO:                                                     │
│  ○ src/server.py          → Servidor HTTP dinâmico + CORS + Probes                │
│  ○ src/core/              → 14 módulos do Kernel Mission-Critical                  │
│  ○ src/modules/<modulo>/  → Fatias verticais completas (Full CRUD + Testes)        │
│  ○ frontend/              → Next.js 14/TypeScript (se export-frontend executado)   │
│  ○ infra/terraform/       → main.tf AWS (VPC, RDS, ElastiCache)                   │
│  ○ infra/helm/            → Chart Helm com Probes e HPA                           │
│  ○ RELATORIO-AUDITORIA.json → Score de Blindagem 100.0% Nota A+                   │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Novos Comandos CLI Disponíveis na v5.1

| Comando | O Que Faz |
| :--- | :--- |
| `aidd.py compose <dir> <nome> [módulos] --db [sqlite\|postgres]` | Compõe suíte completa com escolha de motor de banco |
| `aidd.py add-module <nome> --dir <pasta>` | Adiciona fatia vertical atômica com CQRS + CRDT |
| `aidd.py export-frontend --stack nextjs` | Gera app Next.js 14/TypeScript tipado com TanStack Table |
| `aidd.py refine-module <módulo> --spec <feature>` | Executa ciclo BDD RED/GREEN com Behave |
| `aidd.py scaffold-infra` | Gera Terraform AWS + Helm Chart com Probes |
| `aidd.py audit --report` | Executa os 7 Gates + relatório JSON factual |
| `aidd.py bench -n 100` | Benchmark de carga concorrente (SQLite WAL) |

---

## 3. Matriz Completa dos 9 Pilares Mission-Critical v5.1

| # | Pilar v5.1 | Risco Eliminado | Arquivo Principal |
| :---: | :--- | :--- | :--- |
| **1** | **DatabaseAdapter Poliglota** | Lock-in de banco único e incompatibilidade de dialeto SQL. | `core/database.py` |
| **2** | **Transactional Outbox (At-Least-Once)** | Perda de eventos de domínio em crash de processo. | `core/database.py` / `outbox_worker.py` |
| **3** | **WORM Audit Hash Chain** | Adulteração de histórico de auditoria por DBA malicioso. | `core/database.py` (`_audit_log`) |
| **4** | **Saga Pattern + Compensating Tx** | Estado inconsistente em fluxos financeiros multi-passo. | `core/saga.py` |
| **5** | **Circuit Breaker & Bulkhead** | Cascata de falhas de serviços externos bloqueando o sistema inteiro. | `core/circuit_breaker.py` |
| **6** | **Token Revocation List (TRL)** | JWT stateless irrevogável após comprometimento de conta. | `core/token_revocation.py` |
| **7** | **CQRS + Stale-While-Revalidate** | Aggregations pesadas travando banco em dashboards de KPIs. | `core/cqrs.py` |
| **8** | **Local-First CRDTs** | Perda de dados e conflitos de merge em uso offline. | `core/local_first.py` |
| **9** | **Distributed Tracing (W3C)** | Impossibilidade de correlacionar erros assíncronos ponta a ponta. | `core/events.py` (`correlation_id`) |
