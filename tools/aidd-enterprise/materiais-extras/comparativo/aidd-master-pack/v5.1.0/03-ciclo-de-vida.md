# Ciclo de Vida Completo de Uso — AIDD Master Pack

> **Tag/Versão documentada:** `v5.1.0`
> **Fonte primária:** `CICLO_VIDA_COMPLETO_V5.md` (presente na própria tag), complementada com verificação em `scripts/aidd.py` e `SKILL.md` da mesma tag.
> **Escopo:** Somente o comportamento presente no snapshot da tag `v5.1.0`.

---

## Visão geral em 4 fases

```
FASE 0: Acesso e instalação no ambiente do usuário
   ↓
FASE 1: Entrada do usuário (linguagem natural ou comando declarativo)
   ↓
FASE 1.5: Especificação e alinhamento arquitetural em 3 níveis (Spec Gate)
   ↓
FASE 2: Processamento mecânico (motor de composição + kernel + gates)
   ↓
FASE 3: Saída entregue, operacional e auditada
```

---

## FASE 0 — Acesso e instalação

1. **Obtenção do pacote:**
   ```
   git clone https://github.com/heverton-dev/aidd-master-pack.git
   git checkout v5.1.0
   ```
2. **Bootstrap automático de dependências** (pytest, behave, psycopg2, pyjwt e afins):
   ```
   python scripts/aidd.py setup
   ```
   Esse comando executa diagnóstico de pré-voo e detecta automaticamente se o ambiente vai operar em modo SQLite local ou PostgreSQL remoto.

## FASE 1 — Entrada do usuário (zero atrito)

A tag suporta três modos de entrada, todos via a mesma CLI `scripts/aidd.py`:

- **Modo A — Linguagem natural:**
  ```
  python scripts/aidd.py "Criar sistema financeiro multi-tenant com CRM e ERP"
  ```
- **Modo B — Declarativo, com escolha de banco:**
  ```
  python scripts/aidd.py compose ./meu-projeto "Suite Financeira" crm erp --db postgres
  ```
- **Modo C — Adição de módulo isolado a um projeto já existente:**
  ```
  python scripts/aidd.py add-module cobranca --dir ./meu-projeto
  ```

## FASE 1.5 — Especificação e alinhamento arquitetural (Spec Gate)

Antes de qualquer geração de código, a tag gera artefatos de planejamento que o usuário revisa:

1. Geração de `SPEC-ARQUITETURA.md`, cobrindo a visão de Negócio, Backend e Frontend/UX.
2. Geração do manifesto `PLANO-EXECUCAO-ESTRUTURADO.json`, que registra o estado das fases do plano (uma espécie de saga de execução do próprio processo de geração).
3. Revisão interativa: o usuário aprova ou ajusta as fatias verticais e entidades propostas.
4. Gatilho de aprovação, que dispara a geração efetiva:
   ```
   python scripts/aidd.py apply --dir <pasta>
   ```

## FASE 2 — Processamento mecânico (o "motor" agindo)

Esta é a fase em que o kernel do AIDD materializa o projeto. Na tag `v5.1.0`, o processamento cobre cinco blocos de trabalho:

**Bloco 2A — Persistência e auditoria**
- `DatabaseAdapter` (ponte SQLite WAL ↔ PostgreSQL, incluindo tradução de `?`→`%s` e `AUTOINCREMENT`→`SERIAL`).
- Padrão de Outbox Transacional (`_outbox_events`) para entrega de eventos ao menos uma vez.
- Log de auditoria encadeado por hash (`_audit_log`, estilo WORM/Merkle).
- Row-Level Security quando o banco é PostgreSQL (`SET app.current_tenant_id`).
- Controle de migrações idempotente (`_schema_migrations`) e seeds.

**Bloco 2B — Regras de negócio, resiliência e identidade**
- Padrão `Result` monádico (`Result.ok`/`Result.fail`) para eliminar falhas 500 não tratadas.
- Orquestrador de Saga com transações compensatórias.
- Circuit Breaker dinâmico (CLOSED → OPEN → HALF_OPEN).
- `JobQueue` resiliente com backoff exponencial e Dead Letter Queue, exposta via `/api/jobs`.
- Lista de revogação de tokens (TRL) em memória.
- SSO corporativo via OIDC + PKCE (RFC 7636), com RBAC baseado em grupos.

**Bloco 2C — Mensageria distribuída e rastreabilidade**
- `EventBus` plugável (driver InMemory local, ou Redis Streams para operação distribuída).
- Consumer Groups do Redis (`XADD`/`XREADGROUP`) quando aplicável.
- Propagação de `X-Correlation-ID` (tracing distribuído) de HTTP → Outbox → Job → Log.
- `OutboxWorker` em background, com isolamento de exceções.

**Bloco 2D — Contratos, front-end e CQRS**
- `RouteRegistry` singleton, thread-safe, compartilhado entre módulos.
- OpenAPI 3.1 dinâmico + Swagger Studio (`/docs`) + servidor MCP JSON-RPC 2.0 (`/mcp`).
- SPA offline-first (Super-App), CSS 100% embutido, sem dependência de CDN.
- Camada CQRS de leitura com cache stale-while-revalidate.
- Estruturas Local-First (CRDT Grow-Only Set) para merge de dados offline sem conflito.
- Exportador opcional de front-end Next.js 14/TypeScript (`aidd export-frontend`).

**Bloco 2E — Observabilidade, IaC e Quality Gates**
- Métricas Prometheus nativas (`/metrics`).
- Probes de Kubernetes (`/live`, `/ready`, `/startup`) quando o Helm chart é gerado.
- Geração opcional de IaC Terraform AWS e Helm Chart (`aidd scaffold-infra`).
- Refinador BDD via `behave`/Gherkin (`aidd refine-module`).
- Scanner anti-stub (AST) e linter WCAG 2.1 do Impeccable UI.
- Execução dos 7 Quality Gates mecânicos, bloqueantes.
- Snapshot SHA-256 dos contratos de API.
- Benchmark de concorrência (`aidd bench -n 100`).
- Sincronização de contexto multi-IDE (`.cursor/`, `.claude/`, `.agent/`) e `CONTEXTO-PROJETO.md`.

## FASE 3 — Saída entregue, operacional e auditada

Ao final do ciclo, o usuário recebe um projeto funcional com portais ativos (todos offline-first):

| Portal | URL padrão | Função |
| :--- | :--- | :--- |
| Super-App SPA | `http://localhost:3000/` | Interface dark mode com cards de KPIs e CRUD completo |
| Swagger Studio | `http://localhost:3000/docs` | Documentação interativa OpenAPI 3.1 |
| Webhook Studio | `http://localhost:3000/webhooks` | Painel de disparo de eventos assinados HMAC SHA-256 |
| MCP Native Studio | `http://localhost:3000/mcp` | Endpoint JSON-RPC 2.0 para IAs (Claude, Cursor etc.) |
| Telemetria | `http://localhost:3000/metrics` | Métricas Prometheus (quando composta no projeto) |

E artefatos gerados em disco, entre eles: `src/server.py`, `src/core/` (kernel), `src/modules/<modulo>/` (fatias verticais completas com testes), opcionalmente `frontend/` (Next.js), `infra/terraform/` e `infra/helm/` (quando `scaffold-infra` é executado), e um `RELATORIO-AUDITORIA.json` com o score de qualidade obtido pelos gates.

## Comandos de CLI disponíveis na v5.1.0

| Comando | Função |
| :--- | :--- |
| `aidd.py compose <dir> <nome> [módulos] --db [sqlite\|postgres]` | Compõe a suíte completa com escolha do motor de banco |
| `aidd.py add-module <nome> --dir <pasta>` | Adiciona uma fatia vertical atômica |
| `aidd.py export-frontend --stack nextjs` | Gera app Next.js 14/TypeScript tipado |
| `aidd.py refine-module <módulo> --spec <feature>` | Executa ciclo BDD RED/GREEN com Behave |
| `aidd.py scaffold-infra` | Gera Terraform AWS + Helm Chart |
| `aidd.py audit --report` | Executa os 7 gates e emite relatório JSON |
| `aidd.py bench -n 100` | Executa benchmark de carga concorrente |
| `aidd.py setup` / `plan` / `apply` / `test` / `heal` / `status` / `deploy` / `init` | Demais etapas do ciclo de vida (bootstrap, planejamento, aplicação, testes, auto-remediação, status, deploy e provisionamento) |

*Todos os comandos acima foram confirmados como existentes em `scripts/aidd.py` na tag `v5.1.0`.*
