# Matriz Atômica de Qualidade do AIDD Master Pack v5.0 (Nível Enterprise Distribuído)

> **Documento de Governança Arquitetural:** Critérios de Aceite Atômicos, Quality Gates Mecânicos e Padrões de Entrega para a Versão 5.0.0.  
> **Escopo:** Persistência Poliglota, Transactional Outbox, Distributed EventBus, Frontend Híbrido, SSO OIDC, BDD Recursivo e Cloud Native IaC.  
> **Lema Inegociável:** 100% é Mínimo (Zero Atendimentos Parciais, Zero Stubs, Zero Locks de Concorrência).

---

## 1. Critérios de Qualidade por Camada de Entrega

### A. Camada de Persistência Poliglota & Outbox Transacional (`src/core/database.py` / `outbox_worker.py`)
- **Padrão Bridge (`DatabaseAdapter`):** Interface unificada para SQLite WAL local e PostgreSQL/Supabase remoto (`--db [sqlite|postgres]`).
- **Proxy Transparente de Conexão (`PostgresConnectionProxy`):** Tradução automática de placeholders (`?` → `%s`), emulação de `cursor.lastrowid` via injeção de `RETURNING id` e conversão de DDL (`AUTOINCREMENT` → `SERIAL`).
- **Transactional Outbox Pattern (`_outbox_events`):** Toda mutação de estado (`criar`, `atualizar`, `deletar`) grava o evento no outbox dentro da mesma transação SQL (`with conn:`), garantindo entrega garantida (*At-Least-Once Delivery*) mesmo em caso de crash do processo.
- **Worker Resiliente em Background (`OutboxWorker`):** Processamento assíncrono ordenado por `id ASC`, com recuperação automática de eventos pendentes e isolamento contra exceções de handlers.
- **Concorrência & WAL:** SQLite configurado com `PRAGMA journal_mode=WAL;`, `synchronous=NORMAL` e `busy_timeout=5000`.
- **Integridade & Soft-Delete:** Suporte a exclusão lógica via coluna `deletado_em` e tabela interna `_schema_migrations` idempotente.
- **Gate Validador:** `G_ESTRUTURA`, `G_TESTES` e `G_SEGURANCA`.

---

### B. Camada de Front-End Híbrido & Design System Offline-First (`index.html` / `frontend/`)
- **Super-App Vanilla SPA Offline-First:** CSS 100% embutido na tag `<style>` com variáveis CSS, paleta Dark Mode (Slate/Sky/Emerald) e zero dependência de CDNs externos.
- **Dimensões Físicas Travadas em SVGs:** Todo ícone possui `width="14" height="14"` no próprio elemento SVG para prevenir distorções visuais.
- **Modais e Abas com Display Encapsulado:** Regra CSS nativa `.modal-overlay { display: none !important; }` garantindo que modais nasçam ocultos e só abram via clique.
- **Cards de KPIs no Topo:** Indicadores consolidados em tempo real (`Total`, `Ativos`, `Concluídos`, `Taxa de Conclusão`) consumindo `/api/<modulo>/metricas`.
- **Exportador Next.js 14+ / TypeScript (`aidd export-frontend`):** Geração automática de aplicação React TypeScript (`.tsx`) com App Router, Tailwind CSS, TanStack Table e tipos inferidos a partir dos esquemas OpenAPI 3.1.
- **Acessibilidade WCAG 2.1:** Botões com `type="button"`, `aria-label`, foco acessível e toasts assíncronos (zero `alert()`).
- **Gate Validador:** `G_ESTRUTURA`, `G_QUALIDADE` e `G_CONTRACTS`.

---

### C. Camada de Back-End, Result Pattern & Jobs com DLQ (`services.py` / `jobs.py`)
- **Full CRUD Rigoroso:** 5 métodos reais (`listar()`, `obter_por_id()`, `criar()`, `atualizar()`, `deletar()`) + `obter_metricas()` em cada fatia vertical.
- **Padrão Resultado Monádico (`Result`):** Retornos encapsulados com `Result.ok(valor)` ou `Result.fail(erro, codigo)`, eliminando falhas 500 não tratadas.
- **Fila de Tarefas Resiliente (`JobQueue`):** Persistência de jobs em tabela `_jobs`, retentativas exponenciais automáticas ($t = 2^n \times 5s$) e encaminhamento para *Dead Letter Queue* (DLQ) após esgotamento.
- **Painel de Jobs & Reprocessamento:** Endpoints `GET /api/jobs` e `POST /api/jobs/reprocessar` para inspeção e reexecução de falhas.
- **Zero Anti-Patterns:** Proibição estrita de stubs vazios (`pass`, `...`, `TODO`, `NotImplementedError`).
- **Gate Validador:** `G_ESTRUTURA`, `G_QUALIDADE` e `G_TESTES`.

---

### D. Camada de APIs, OpenAPI 3.1 & Model Context Protocol (`openapi.py` / `mcp_server.py`)
- **Singleton RouteRegistry:** Registro compartilhado de forma thread-safe entre todos os módulos e o despachante do servidor HTTP.
- **OpenAPI 3.1 & Swagger Studio:** Interface interativa viva em `/docs` e `/docs/guia` com formulários *Try it out* e esquemas JSON validados.
- **Servidor Universal MCP JSON-RPC 2.0:** Endpoint `/mcp` com ferramentas dinâmicas registradas para cada fatia vertical (`mod_<modulo>_listar`, `mod_<modulo>_criar`, etc.).
- **Snapshot Criptográfico SHA-256:** Verificação de integridade no `G_CONTRACTS` para prevenir quebras de contrato de rotas ou esquemas.
- **CORS Preflight Middleware:** Resposta automática a requisições `OPTIONS` com headers de acesso liberados.
- **Gate Validador:** `G_CONTRACTS` e `G_HARNESS_COMPAT`.

---

### E. Camada de Mensageria Distribuída Cross-Domain (`events.py` / `webhooks.py`)
- **Driver Plugável de EventBus:** Suporte a `InMemoryEventBusDriver` (padrão local) e `RedisStreamsDriver` (distribuído multi-instância via `EVENTBUS_URL`).
- **Consumer Groups do Redis:** Uso de `XADD` e `XREADGROUP` garantindo entrega balanceada e idempotente entre múltiplos nós.
- **Envelope Padronizado com Tracing:** Transmissão de eventos com `event_id` (UUID), `event_name`, `timestamp` UTC, `origin_module` e `data`.
- **Webhook Studio com HMAC SHA-256:** Disparador assíncrono com cabeçalho de assinatura criptográfica `X-Hub-Signature-256`.
- **Gate Validador:** `G_TESTES` e `G_SEGURANCA`.

---

### F. Camada de Cibersegurança, SSO Corporativo & RBAC (`security.py`)
- **SSO Corporativo OAuth2 / OIDC com PKCE (RFC 7636):** Fluxo Authorization Code com `code_verifier` e `code_challenge` S256, integrando Google Workspace, Microsoft Entra ID e Okta.
- **Validação Criptográfica RS256 via JWKS:** Decodificação e validação de chaves públicas do provedor de identidade com verificação de `iss`, `aud` e `exp`.
- **Mapeamento Declarativo de Grupos para RBAC:** Conversão automática de claims corporativas para perfis internos (`admin`, `operador`, `leitor`).
- **19 Testes Ativos de Cibersegurança OWASP:** Headers de segurança estritos (`nosniff`, `DENY`, `CSP`), JWT HS256 com PBKDF2 local (100k rounds), queries 100% parametrizadas (`?`) e Docker Non-Root (`aidduser` UID 10001).
- **Gate Validador:** `G_SEGURANCA` (Score 100.0% Nota A+ Obrigatório).

---

### G. Camada de IA Recursiva BDD, IaC Declarativa & Observabilidade (`behave` / `metrics.py` / `infra/`)
- **Refinador de Domínio BDD (`aidd refine-module`):** Execução do framework `behave` como gate determinístico RED/GREEN, permitindo que o agente implemente lógicas de negócio complexas guiado por cenários Gherkin (`features/<modulo>.feature`).
- **Infraestrutura como Código (Terraform AWS + Kubernetes Helm):** Geração automática de `infra/terraform/main.tf` (VPC, RDS PostgreSQL, ElastiCache Redis) e charts Helm (`Chart.yaml`, `values.yaml`, `deployment.yaml`, `service.yaml`, `ingress.yaml`, `hpa.yaml`).
- **Telemetria Nativa Prometheus (`/metrics`):** Endpoint nativo expondo contadores de requisições, histogramas de latência e medidores de conexões com overhead < 0.1ms.
- **Gate Validador:** `G_TESTES`, `G_HARNESS_COMPAT` e `G_QUALIDADE`.

---

## 2. Tabela Consolidada dos 7 Quality Gates Mecânicos

| Gate | O Que Audita no Código Real do Projeto | Condição de Bloqueio Imediato (Exit 1) |
| :--- | :--- | :--- |
| **1. G_ESTRUTURA** | Layout modular em `src/modules/`, fatias verticais completas, Linter AST Anti-Acoplamento e Scanner Anti-Vazamento de Conexões SQLite/Postgres. | Falta de fatias, import direto proibido entre módulos irmãos ou vazamento de conexões. |
| **2. G_QUALIDADE** | Compilação estática `py_compile`, varredura AST anti-stubs (`pass`, `...`, `TODO`) e Linter WCAG 2.1 Impeccable UI. | Erro de sintaxe, funções vazias ("preguiça da IA") ou diálogos nativos `alert()`. |
| **3. G_TESTES** | Execução real da suíte unitária e BDD com `pytest` em `tests/unit/`, asserções de mutação e healthchecks. | Qualquer teste FAILED ou 0 testes encontrados. |
| **4. G_CONTRACTS** | Conformidade de esquemas OpenAPI 3.1, ferramentas MCP JSON-RPC, Snapshot SHA-256 e integridade visual dos 4 Portais Web (CSS embutido, SVGs travados). | Quebra de contrato de API, ferramentas MCP inválidas ou front-end desestilizado. |
| **5. G_SEGREDOS** | Scanner de Entropia de Shannon ($H > 4.75$) e Regex contra chaves privadas e credenciais hardcoded. | Chave de API, segredo ou token exposto no código. |
| **6. G_HARNESS_COMPAT** | Zero API Key nativo, compatibilidade multiplataforma (Windows/Linux/Mac) e validação de IaC/Helm. | Dependência paga bloqueante ou comando de harness quebrado. |
| **7. G_SEGURANCA** | 19 baterias de cibersegurança OWASP, JWT HS256/RS256, Zero SQLi, Docker Non-Root e Nginx Shield. | Vulnerabilidade detectada (Score de Blindagem < 100.0%). |

---

## 3. Matriz de Cobertura de Testes Automatizados da Versão v5.0

```text
================================================================================
BATERIA DE TESTES AUTOMATIZADOS HOMOLOGADOS (v5.1.0):
   - DatabaseAdapter & Outbox Proxy:  13 testes unitários PASS (1 skip docker)
   - EventBus Driver & Redis Streams:  4 testes unitários PASS (1 skip redis live)
   - JobQueue Resiliente & DLQ:        7 testes unitários PASS
   - Métricas Prometheus (/metrics):   6 testes unitários PASS (overhead < 0.1ms)
   - SSO Corporativo OIDC & PKCE:      8 testes unitários PASS
   - OutboxWorker em Background:       5 testes unitários PASS
   - Scaffold IaC (Helm + Terraform): 11 testes estruturais PASS (2 skip binários)
   -----------------------------------------------------------------------------
   TOTAL: 54 TESTES UNITÁRIOS APROVADOS (100% PASS) EM 4.89s
================================================================================
```

*Matriz Atômica de Qualidade homologada, versionada e vinculada à tag v5.1.0 no repositório oficial.*
