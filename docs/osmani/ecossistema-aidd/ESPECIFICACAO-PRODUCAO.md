# ESPECIFICAÇÃO DE PRONTIDÃO DE PRODUÇÃO (Estágio 3 — AIDD-Osmani)

> **Iniciativa:** Ecossistema AIDD 100% Funcional em Produção (Padrão 9 Camadas RevNault)
> **Referencial:** [CONSTRAINTS.md](../../../CONSTRAINTS.md), [RELATORIO-AUDITORIA.md](RELATORIO-AUDITORIA.md) e [TICKETS.md](TICKETS.md)
> **Habilidade:** `spec-driven-development`

---

## 1. Mapa de Capacidades & Ordem de Construção

| ID do Módulo | Responsabilidade | Depende de |
|---|---|---|
| `mod-01-frontend-ouro` | Atualização do template `frontend-tanstack` (React 19, TS 5.8, Vite 6, TanStack Router/Query, Radix, Tailwind) e universalização do `TanStackRouterExporter` para os 3 fluxos e master | — |
| `mod-02-persistencia-dual` | Scaffold de banco assíncrono híbrido (SQLite WAL para dev + PostgreSQL 16 com `pgvector` e `asyncpg` para produção) e migrações Alembic | — |
| `mod-03-infra-borda` | Scaffold de infraestrutura de alta performance no `aidd-ops` (Traefik v3 com Let's Encrypt, Redis 7 Streams XGROUP/XREADGROUP e cliente Cloudflare R2 S3v4) | `mod-01-frontend-ouro`, `mod-02-persistencia-dual` |
| `mod-04-prova-triade` | Execução síncrona real e certificação fim a fim dos 3 fluxos (`pure`, `open`, `freedom`) via `orquestrador_sincrono.py` com `exit 0` | `mod-01-frontend-ouro`, `mod-02-persistencia-dual`, `mod-03-infra-borda` |

**Ordem de Construção:** `mod-01-frontend-ouro` & `mod-02-persistencia-dual` ➔ `mod-03-infra-borda` ➔ `mod-04-prova-triade`.

---

## 2. Critérios de Aceite por Módulo

### Módulo 1: `mod-01-frontend-ouro` (TICKET-01 + TICKET-02)
- **C1.1:** `componentes/compartilhado/templates/frontend-tanstack/package.json` possui dependências atualizadas:
  - `react`: `^19.0.0` e `react-dom`: `^19.0.0`
  - `typescript`: `^5.8.2`
  - `vite`: `^6.2.0`
  - `@tanstack/react-query`: `^5.67.1`
  - `@tanstack/react-router`: `^1.114.12`
  - `tailwindcss`: `^3.4.17`
  - `lucide-react`: `^0.477.0`
  - Radix UI Primitives (`dialog`, `dropdown-menu`, `slot`, `tabs`, `toast`, `avatar`), `class-variance-authority`, `clsx`, `tailwind-merge`
- **C1.2:** `TanStackRouterExporter` (`componentes/compartilhado/src-core/tanstack_exporter.py`) exporta a estrutura limpa e parametrizada com o nome da suíte em `frontend/` e é integrado em:
  - `aidd-pure` (Fluxo 01)
  - `aidd-freedom` (Fluxo 03)
  - `aidd-master` (`compose_suite.py`)
- **C1.3:** Quality Gates `G_STACK_PADRAO_OURO.py` e `G_TEMPLATE_TANSTACK_OFFLINE.py` aprovados com `exit 0`.

### Módulo 2: `mod-02-persistencia-dual` (TICKET-03)
- **C2.1:** Template de banco de dados assíncrono em `src/core/database.py` suportando:
  - Conexão local em `sqlite+aiosqlite:///app.db` com `PRAGMA journal_mode=WAL` e `PRAGMA foreign_keys=ON`.
  - Conexão cluster em `postgresql+asyncpg://...` com separação `get_write_db` e `get_read_db`.
- **C2.2:** Módulo `src/core/vector_store.py` fornecendo interface de busca por similaridade de cosseno com `pgvector` HNSW e fallback matricial em SQLite/numpy.
- **C2.3:** Configuração padrão de migrações `alembic.ini` e `migrations/env.py` pronta para deploy.

### Módulo 3: `mod-03-infra-borda` (TICKET-04)
- **C3.1:** `docker-compose.yml` e `docker-stack.yml` gerados pelo `aidd-ops` incorporam serviço `traefik:v3.3` com labels dinâmicas, SSL Let's Encrypt automático e headers de segurança HSTS.
- **C3.2:** Serviço `redis:7-alpine` provisionado com script de inicialização de Consumer Groups no Redis Streams (`XGROUP CREATE`).
- **C3.3:** Módulo `src/core/storage.py` com `R2StorageClient` autenticado via Boto3 (AWS S3v4) com suporte a URLs pré-assinadas temporárias e validação anti-IDOR.

### Módulo 4: `mod-04-prova-triade` (TICKET-05)
- **C4.1:** Testes automatizados executam cada um dos 3 fluxos (`pure`, `open`, `freedom`) gerando um projeto funcional com as 9 camadas em pasta temporária.
- **C4.2:** Todos os 5 contratos de handoff (C1 a C5) gravados com `sha256` autêntico e validados contra os schemas formais em `componentes/compartilhado/specs/`.
- **C4.3:** Portão `python ecossistema.py audit` e `pre-commit run --all-files` aprovados com 100% verde (`exit 0`).
