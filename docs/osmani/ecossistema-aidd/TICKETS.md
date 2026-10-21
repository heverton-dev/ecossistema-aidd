# TICKETS — Resolução & Implementação para Prontidão de Produção (Playbook L)

> **Origem:** Auditoria Factual [RELATORIO-AUDITORIA.md](RELATORIO-AUDITORIA.md) baseada no contrato [CONSTRAINTS.md](../../../CONSTRAINTS.md).
> **Priorização:** Críticos e Altos (ordem de dependência topológica).

---

### TICKET-01: Atualização do Template Canônico `frontend-tanstack` para Padrão RevNault [CONCLUÍDO]
- **Severidade:** ALTA
- **Status:** **CONCLUÍDO (100% OK)**
- **Bloqueado por:** Nenhum (Fundação)
- **Escopo de Arquivos:** `componentes/compartilhado/templates/frontend-tanstack/package.json`, `template-manifest.json`, `CHECKLIST-CAMADAS-MERCADO.json`
- **Critério de Aceite Binário:**
  1. `package.json` atualizado com `react: ^19.0.0`, `react-dom: ^19.0.0`, `typescript: ^5.8.2`, `vite: ^6.2.0`, `@tanstack/react-query: ^5.67.1`, `@tanstack/react-router: ^1.114.12`, `tailwindcss: ^3.4.17`, `lucide-react: ^0.477.0`, primitivos `@radix-ui/react-*`, `cva`, `clsx`, `tailwind-merge`.
  2. `CHECKLIST-CAMADAS-MERCADO.json` e `DESIGN.md` refletem 100% da stack RevNault de Camadas 1, 2, 3 e 5.
  3. Gates `G_TEMPLATE_TANSTACK_OFFLINE.py`, `G_STACK_PADRAO_OURO.py` e `G_NOVE_CAMADAS_MERCADO.py` aprovados com `exit 0`.

---

### TICKET-02: Universalização do Exportador TanStack nos 3 Fluxos da Tríade e Master [CONCLUÍDO]
- **Severidade:** ALTA
- **Status:** **CONCLUÍDO (100% OK)**
- **Bloqueado por:** TICKET-01
- **Escopo de Arquivos:**
  - `componentes/compartilhado/src-core/tanstack_exporter.py`
  - `modulos/02-triade-motores/fluxo-01-pure/core/aidd-pure/scripts/pipeline_completo.py`
  - `modulos/02-triade-motores/fluxo-03-freedom/core/aidd-freedom/aidd_freedom/cli.py`
  - `modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/scripts/compose_suite.py`
- **Critério de Aceite Binário:**
  1. `TanStackRouterExporter` é acionado determinísticamente tanto no Fluxo 01 (`aidd-pure`) quanto no Fluxo 03 (`aidd-freedom`) e na montagem da suíte do `aidd-master`, gerando a pasta `frontend/` padronizada em qualquer nova aplicação.
  2. Substituição do HTML estático monolítico pela casca viva de produção TanStack Router + Vite.
  3. Teste unitário e de integração comprovando a exportação nas três frentes (12/12 testes aprovados em `test_orquestrador_sincrono.py`).

---

### TICKET-03: Módulo de Persistência Dual Assíncrona (SQLite WAL + Postgres 16 pgvector) [CONCLUÍDO]
- **Severidade:** ALTA
- **Status:** **CONCLUÍDO (100% OK)**
- **Bloqueado por:** Nenhum (Backend)
- **Escopo de Arquivos:**
  - `componentes/compartilhado/src-core/vector_store.py`
  - `modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/src/core/vector_store.py`
  - `modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise/src/core/vector_store.py`
  - `tests/unit/test_vector_store.py`
- **Critério de Aceite Binário:**
  1. Suporte a engine dual SQLAlchemy 2.0 Async (`get_write_db` e `get_read_db`) com chaveamento transparente entre SQLite WAL (`aiosqlite`) para dev/testes e PostgreSQL 16 (`asyncpg`) para produção.
  2. Módulo de busca vetorial nativo com `pgvector` e índice HNSW para RAG/embeddings sem acoplamento a SaaS proprietário (fallback local determinístico).
  3. Conformidade total com Clean Architecture aprovada pelo Quality Gate `G_ARQUITETURA_DELIVERABLE`.

---

### TICKET-04: Módulo de Infraestrutura de Borda e Mensageria no `aidd-ops` [CONCLUÍDO]
- **Severidade:** ALTA
- **Status:** **CONCLUÍDO (100% OK)**
- **Bloqueado por:** TICKET-02, TICKET-03
- **Escopo de Arquivos:**
  - `componentes/compartilhado/src-core/storage.py`
  - `modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/src/core/storage.py`
  - `modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise/src/core/storage.py`
  - `tests/unit/test_storage.py`
  - `.env.example`
- **Critério de Aceite Binário:**
  1. Scaffold de infraestrutura com `Traefik v3` configurado como reverse proxy, terminação TLS Let's Encrypt automática e rate limiting.
  2. Serviço `Redis 7` configurado com `Redis Streams` para mensageria assíncrona entre módulos VSA.
  3. Módulo cliente `Cloudflare R2` compatível com API S3v4 para upload direto via Presigned URLs sem custo de transferência de saída (zero egress) e proteção anti-IDOR.
  4. Documentação formal das variáveis de ambiente em `.env.example` com aprovação no `G_ENV_ROT`.

---

### TICKET-05: Homologação e Prova Factual Fim a Fim dos 3 Fluxos em Modo Produção [CONCLUÍDO]
- **Severidade:** CRÍTICA
- **Status:** **CONCLUÍDO (100% OK)**
- **Bloqueado por:** TICKET-01, TICKET-02, TICKET-03, TICKET-04
- **Escopo de Arquivos:** `scripts/orquestrador_sincrono.py`, `tests/test_orquestrador_sincrono.py`
- **Critério de Aceite Binário:**
  1. Execução de ponta a ponta dos três fluxos comprovada via testes automatizados e orquestrador determinístico:
     - `python ecossistema.py run-fluxo --fluxo pure ...`
     - `python ecossistema.py run-fluxo --fluxo open ...`
     - `python ecossistema.py run-fluxo --fluxo freedom ...`
  2. Geração e validação dos contratos canônicos C1 a C5 assinados com HMAC/SHA-256 e schema JSON.
  3. Injeção determinística do template canônico `frontend-tanstack` em substituição aos HTMLs legados, garantindo a stack RevNault de 9 camadas para qualquer aplicação gerada no ecossistema.

