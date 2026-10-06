# Matriz Atômica de Qualidade por Camada de Entrega — AIDD Master Pack

> **Tag/Versão documentada:** `v5.1.0`
> **Fonte primária:** `MATRIZ_QUALIDADE_ATOMICA_V5_1.md` (extensão "Mission-Critical" presente na própria tag), somada aos critérios base de `MATRIZ_QUALIDADE_ATOMICA_V5.md` (também presente na tag, e sobre a qual a V5_1 atua de forma aditiva).
> **Escopo:** Gates e mecanismos de qualidade fisicamente presentes no snapshot da tag `v5.1.0` (`scripts/gates/*.py` e módulos de `templates/v2/`).

---

## 1. Os 7 Quality Gates mecânicos (bloqueantes, exit code 0 obrigatório)

| Gate | O que audita no código real do projeto | Condição de bloqueio imediato (exit 1) |
| :--- | :--- | :--- |
| **G_ESTRUTURA** | Layout modular em `src/modules/`, presença de fatias verticais completas, linter AST anti-acoplamento e scanner anti-vazamento de conexões SQLite/Postgres. | Falta de fatias, import direto proibido entre módulos irmãos, ou vazamento de conexões. |
| **G_QUALIDADE** | Compilação estática (`py_compile`), varredura AST anti-stubs (`pass`, `...`, `TODO`, `NotImplementedError`) e linter WCAG 2.1 do Impeccable UI. | Erro de sintaxe, função vazia ("preguiça da IA") ou uso de diálogo nativo `alert()`. |
| **G_TESTES** | Execução real da suíte unitária e BDD com `pytest` em `tests/unit/`, asserções de mutação e healthchecks. | Qualquer teste com falha, ou zero testes encontrados. |
| **G_CONTRACTS** | Conformidade dos esquemas OpenAPI 3.1, validade das ferramentas MCP JSON-RPC, snapshot SHA-256 de contratos e integridade visual dos portais web (CSS embutido, SVGs com dimensões travadas). | Quebra de contrato de API, ferramenta MCP inválida ou front-end desestilizado. |
| **G_SEGREDOS** | Scanner de entropia de Shannon (H > 4,75) e regex contra chaves privadas e credenciais hardcoded. | Chave de API, segredo ou token exposto no código. |
| **G_HARNESS_COMPAT** | Ausência de dependência de API key nativa obrigatória, compatibilidade multiplataforma (Windows/Linux/Mac) e validação estrutural de IaC/Helm. | Dependência paga bloqueante, ou comando de harness quebrado. |
| **G_SEGURANCA** | Baterias de checagem de cibersegurança (headers estritos, JWT, SQLi, Docker non-root, etc.). | Vulnerabilidade detectada (score de blindagem abaixo de 100%). |

*Confirmado no código: os 7 arquivos existem tanto em `scripts/gates/` quanto em `templates/gates/` na tag `v5.1.0` (ex.: `G_SEGURANCA.py` com 330 linhas, `G_QUALIDADE.py` com 85 linhas).*

## 2. Critérios de qualidade por camada de entrega

### A. Persistência de dados e isolamento (`core/database.py`)
- **DatabaseAdapter (padrão Bridge):** interface unificada para SQLite WAL local e PostgreSQL/Supabase remoto.
- **Proxy transparente de conexão:** tradução automática de placeholders (`?` → `%s`), emulação de `cursor.lastrowid` via `RETURNING id`, conversão de DDL (`AUTOINCREMENT` → `SERIAL`).
- **Transactional Outbox (`_outbox_events`):** toda mutação de estado grava o evento no outbox dentro da mesma transação SQL, visando entrega "ao menos uma vez".
- **Row-Level Security (quando PostgreSQL):** isolamento multi-tenant via `SET app.current_tenant_id` no início da transação.
- **WORM Audit Hash Chain:** tabela `_audit_log` com hash SHA-256 encadeado entre linhas, para detecção de adulteração de histórico.
- **Concorrência e WAL:** SQLite com `PRAGMA journal_mode=WAL`, `synchronous=NORMAL` e `busy_timeout=5000`.
- Gate validador: `G_ESTRUTURA`, `G_TESTES`, `G_SEGURANCA`.

### B. Front-end e Design System (Impeccable UI)
- Super-App vanilla SPA offline-first, CSS 100% embutido, paleta dark mode, zero dependência de CDN externo.
- Dimensões físicas travadas em SVGs (`width`/`height` no próprio elemento).
- Modais com `display: none !important` por padrão, abrindo apenas via interação.
- Cards de KPIs consumindo `/api/<modulo>/metricas`.
- Exportador opcional Next.js 14+/TypeScript com App Router, Tailwind e TanStack Table.
- Acessibilidade WCAG 2.1 (botões com `type="button"`, `aria-label`, sem `alert()`).
- Gate validador: `G_ESTRUTURA`, `G_QUALIDADE`, `G_CONTRACTS`.

### C. Back-end, Result Pattern e Jobs
- Full CRUD rigoroso: `listar()`, `obter_por_id()`, `criar()`, `atualizar()`, `deletar()` + `obter_metricas()` em cada fatia vertical.
- Padrão `Result` monádico (`Result.ok`/`Result.fail`), eliminando falhas 500 não tratadas.
- `JobQueue` resiliente: persistência em tabela `_jobs`, retentativas exponenciais (2ⁿ×5s) e Dead Letter Queue.
- Endpoints `GET /api/jobs` e `POST /api/jobs/reprocessar`.
- Proibição estrita de stubs vazios (`pass`, `...`, `TODO`, `NotImplementedError`).
- Gate validador: `G_ESTRUTURA`, `G_QUALIDADE`, `G_TESTES`.

### D. APIs, OpenAPI 3.1 e Model Context Protocol
- `RouteRegistry` singleton thread-safe, compartilhado entre módulos e o dispatcher HTTP.
- Swagger Studio interativo em `/docs` e `/docs/guia`.
- Servidor MCP JSON-RPC 2.0 em `/mcp`, com ferramentas dinâmicas por fatia vertical (`mod_<modulo>_listar`, `mod_<modulo>_criar`, etc.).
- Snapshot criptográfico SHA-256 para prevenir quebras de contrato.
- Middleware de CORS preflight (resposta automática a `OPTIONS`).
- Gate validador: `G_CONTRACTS`, `G_HARNESS_COMPAT`.

### E. Mensageria distribuída cross-domain
- Driver plugável de EventBus: `InMemoryEventBusDriver` (padrão local) e `RedisStreamsDriver` (distribuído, via `EVENTBUS_URL`).
- Consumer Groups do Redis (`XADD`/`XREADGROUP`).
- Envelope padronizado de evento: `event_id` (UUID), `event_name`, `timestamp` UTC, `origin_module`, `data`.
- Webhook Studio com assinatura HMAC SHA-256 (`X-Hub-Signature-256`).
- Gate validador: `G_TESTES`, `G_SEGURANCA`.

### F. Cibersegurança, SSO corporativo e RBAC
- SSO OAuth2/OIDC com PKCE (RFC 7636), integrável a Google Workspace, Microsoft Entra ID e Okta.
- Validação criptográfica RS256 via JWKS (checagem de `iss`, `aud`, `exp`).
- Mapeamento declarativo de grupos/claims para perfis internos (`admin`, `operador`, `leitor`).
- Baterias de cibersegurança OWASP: headers estritos (`nosniff`, `DENY`, `CSP`), JWT HS256 com PBKDF2 local (100k rounds), queries 100% parametrizadas, Docker non-root (usuário `aidduser`, UID 10001).
- Gate validador: `G_SEGURANCA` (score 100% exigido).

### G. IA recursiva BDD, IaC declarativa e observabilidade
- Refinador de domínio via `behave` (RED/GREEN), permitindo implementar regras de negócio complexas guiadas por cenários Gherkin (`features/<modulo>.feature`).
- Geração de IaC: Terraform AWS (VPC, RDS, ElastiCache) e Helm Chart (`Chart.yaml`, `values.yaml`, `deployment.yaml`, `service.yaml`, `ingress.yaml`, `hpa.yaml`).
- Telemetria Prometheus nativa (`/metrics`) — disponível como template a ser composto no projeto gerado.
- Gate validador: `G_TESTES`, `G_HARNESS_COMPAT`, `G_QUALIDADE`.

## 3. Extensão Mission-Critical (aditiva à matriz v5.0, específica desta tag)

A tag `v5.1.0` adiciona sub-rotinas de auditoria bloqueantes aos gates já existentes, elevando o padrão de conformidade em direção a SOC 2 / HIPAA / PCI-DSS:

| Gate afetado | Nova sub-rotina de auditoria (v5.1) | Condição de bloqueio imediato |
| :--- | :--- | :--- |
| **G_SEGURANCA** | Verificação de RLS e auditoria hash: analisa DDL exigindo `ENABLE ROW LEVEL SECURITY`; verifica assinatura do Merkle Hash na tabela de log. | Tabela crítica de negócio sem RLS ativo, ou tabela de auditoria sem hash encadeado validado. |
| **G_QUALIDADE** | Linter de Correlation-ID e Saga: o AST garante que todo evento disparado contém `correlation_id` e que operações multi-entidade declaram handlers de compensação. | Evento emitido sem contexto de rastreio, ou fluxo longo sem rollback explícito detectado. |
| **G_TESTES** | Testes de compensação de Saga: injeta erro simulado no meio do fluxo transacional e valida se o banco retorna ao estado anterior (compensação correta). | Banco termina em estado inconsistente ou bloqueado após uma falha programada. |

Outros pilares descritos nesta extensão (ReBAC estilo Zanzibar, criptografia de envelope com KMS/DEK/KEK, CRDTs local-first, Stale-While-Revalidate agressivo) estão implementados como padrões arquiteturais funcionais em `templates/v2/` — de forma enxuta (dezenas de linhas por módulo), suficiente para cumprir os testes unitários e os gates descritos, mas não equivalentes a soluções de mensageria/observabilidade dedicadas de mercado.

## 4. Cobertura de testes homologada nesta tag

Segundo `MATRIZ_QUALIDADE_ATOMICA_V5.md` (documento presente na tag), a bateria homologada soma **54 testes unitários aprovados (100% pass)**, distribuídos por área:

- DatabaseAdapter & Outbox Proxy: 13 testes (1 skip condicionado a Docker)
- EventBus Driver & Redis Streams: 4 testes (1 skip condicionado a Redis ao vivo)
- JobQueue resiliente & DLQ: 7 testes
- Métricas Prometheus (`/metrics`): 6 testes (overhead < 0,1ms)
- SSO corporativo OIDC & PKCE: 8 testes
- OutboxWorker em background: 5 testes
- Scaffold IaC (Helm + Terraform): 11 testes estruturais (2 skip condicionados a binários externos)

No repositório da tag, o diretório `tests/unit/` contém 8 arquivos de teste correspondentes a essas áreas (`test_database_adapter.py`, `test_events_driver.py`, `test_jobs_queue.py`, `test_metrics.py`, `test_oidc_sso.py`, `test_outbox_worker.py`, `test_scaffold_infra.py`, `test_cqrs_local_first.py`), confirmando fisicamente a existência dessa bateria.
