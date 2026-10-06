# Matriz Atômica de Qualidade do AIDD Master Pack v5.1 (Nível Mission-Critical)

> **Documento de Governança Arquitetural - Extensão de Alta Disponibilidade (Fintech & Multi-Tenant)**
> **Escopo:** Isolamento Nível Banco (RLS), Criptografia de Envelope, Sagas Distribuídas, WORM Audit e Edge/Local-First.
> **Lema Inegociável:** Zero Trust. 100% de Isolamento Matemático e Rastreabilidade Absoluta.

Esta matriz atua de forma aditiva sobre a `MATRIZ_QUALIDADE_ATOMICA_V5.md`, elevando o sistema para conformidade SOC 2, HIPAA e PCI-DSS.

---

## 1. Critérios de Qualidade Nível "Mission-Critical" por Camada

### A. Persistência de Dados e Isolamento Extremo (Zero Trust Data)
- **Row-Level Security (RLS) Nativo:** Isolamento Multi-Tenant forçado pelo motor do banco (PostgreSQL/Supabase). Aplicação realiza `SET app.current_tenant_id` no início da transação; o banco bloqueia vazamentos independente da query SQL.
- **CQRS e Materialized Views:** Separação rígida de Comandos e Consultas. Dashboards de KPIs (`/metricas`) nunca executam aggregations (`COUNT`, `SUM`) em tabelas transacionais críticas, consumindo apenas dados pré-computados (O(1)).

### B. Criptografia, Privacidade e Auditoria
- **Criptografia de Envelope (KMS):** PII (Informações Pessoalmente Identificáveis) e dados sensíveis criptografados via AES-256-GCM na camada de aplicação via Data Encryption Key (DEK), envelopada por uma Key Encryption Key (KEK) externa.
- **Log de Auditoria Encadeado (Merkle Chain / WORM):** Tabela `_audit_log` onde cada linha contém o `SHA-256` do hash da linha anterior. A quebra de um bit no histórico é imediatamente detectada (Write Once, Read Many).

### C. Sistemas Distribuídos e Orquestração Resiliente
- **Saga Pattern Coreografado/Orquestrado:** Operações de múltiplos passos distribuídos não dependem de disparo cego. Se um fluxo falha, o sistema executa *Compensating Transactions* garantidas pelo Outbox.
- **Circuit Breaker Dinâmico & Bulkhead:** Interceptadores de I/O de rede. Fast-fail (abertura de circuito) após 5 timeouts consecutivos em serviços externos, isolando pools de threads (Bulkhead) para não afetar requisições primárias.
- **Distributed Tracing (W3C Trace Context):** Injeção de cabeçalho `X-Correlation-ID` propagado do Edge (HTTP) → Outbox → Mensageria → Job Worker → Logs Estruturados.

### D. Identidade, ReBAC e Governança de Sessão
- **Relationship-Based Access Control (ReBAC):** Grafos de relacionamento para políticas hiper-granulares (ex: "Usuário X só edita Y se pertencer ao Dept Z"), desacoplado da lógica de negócio local (padrão Zanzibar).
- **Token Revocation List (TRL) com Latência Sub-Ms:** Blacklist efêmera em Redis baseada em `jti` (JWT ID). Interceptação e bloqueio de sessões revogadas antes do fim do TTL sem perda de performance.

### E. Edge, Front-End e Disponibilidade Contínua
- **Local-First Architecture (CRDTs):** Front-End apto para operação 100% offline via IndexedDB/RxDB usando *Conflict-free Replicated Data Types*. Latência de salvamento de 0ms percebida pelo usuário e reconciliação assíncrona automática em plano de fundo sem conflitos.
- **Stale-While-Revalidate (SWR) Agressivo:** Camada de CDN ou Nginx servindo último cache bom (Uptime 99.999% percebido) enquanto dados frescos são hidratados silenciosamente em background caso o banco enfrente instabilidade.

---

## 2. Upgrade dos Quality Gates Mecânicos

Para garantir essa arquitetura, os Gates da v5.0 ganham as seguintes sub-rotinas bloqueantes:

| Gate Afetado | Nova Sub-Rotina de Auditoria (v5.1) | Condição de Bloqueio Imediato (Exit 1) |
| :--- | :--- | :--- |
| **G_SEGURANCA** | **Verificação de RLS e Auditoria Hash:** Analisa scripts DDL exigindo `ENABLE ROW LEVEL SECURITY`. Verifica assinatura do Merkle Hash na tabela de log. | Tabela crítica de negócios sem RLS ativo; ou tabela de auditoria sem hash encadeado validado. |
| **G_QUALIDADE** | **Linter de Correlation-ID e Saga:** O AST garante que todo evento disparado contém `correlation_id` e que operações multi-entidade declaram handlers de compensação (Rollback). | Evento emitido sem contexto de rastreio ou fluxo longo sem rollback explícito detectado. |
| **G_TESTES** | **Testes de Compensação de Saga:** Injeta erro falso no meio do fluxo transacional. Valida se o banco termina no estado exato de antes da operação (compensado corretamente). | Banco termina em estado inconsistente ou bloqueado após uma falha programada. |
