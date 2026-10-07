# Mandato Tecnológico Soberano — A Matriz Canônica de Ponta (2026)

> **Documento Canônico:** `docs/protocolos/MANDATO-TECNOLOGICO-SOBERANO.md`  
> **Status:** Ativo e Mandatório para Todos os Fluxos (`pure`, `open`, `freedom`).  
> **Regra Suprema:** Zero concessão a tecnologias legadas, frágeis ou proprietárias. Todo componente gerado ou evoluído no Ecossistema AIDD implementa exclusivamente o ápice tecnológico do mercado atual.

---

## A Matriz Soberana Camada por Camada

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      MATRIZ TECNOLÓGICA SOBERANA 2026                       │
├──────────────────────┬──────────────────────────────────────────────────────┤
│ 1. Frontend & UI     │ TanStack Start / Router + React 19 + Tailwind CSS v4 │
│                      │ Tokens OKLCH + Radix UI + Princípios Impeccable      │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ 2. Offline & PWA     │ Service Worker Workbox 7 + Web Capabilities v2       │
│                      │ Fila Local FIFO Assinada com HMAC SHA-256 Anti-Tamper│
├──────────────────────┼──────────────────────────────────────────────────────┤
│ 3. Estado & Cache    │ TanStack Query v5 + Zod v4 / Valibot                 │
│                      │ Optimistic Updates + Rollback Determinístico         │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ 4. Backend & VSA     │ Python Puro (Litestar/FastAPI) em Vertical Slices    │
│                      │ Fatias verticais autossuficientes com raio zero      │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ 5. Banco de Dados    │ SQLite WAL Mode de Alta Concorrência / PostgreSQL 16+│
│                      │ Drizzle ORM / Alembic (Migrações Reversíveis)        │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ 6. API Studio        │ OpenAPI 3.1 Estrito em /api com Scalar / Swagger UI  │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ 7. Webhook Studio    │ /webhook Nativo com HMAC, Replay de Eventos e Traces │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ 8. MCP Studio        │ /mcp com Model Context Protocol para Agentes de IA   │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ 9. Docs Hub          │ /docs com Central de Documentação e Guia Vivo        │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ 10. Quality & Gates  │ Biome + Vitest + Pytest + Lei #13 (Prova de Mordida) │
└──────────────────────┴──────────────────────────────────────────────────────┘
```

---

## 1. Camada de Frontend (UI/UX Impeccable)
- **Framework Soberano:** **TanStack Start / TanStack Router** (Next.js formalmente abolido).
- **Linguagem & Tipagem:** TypeScript em modo estrito (`strict: true`, `noImplicitAny: true`).
- **Design Tokens & Cores:** Espaço de cor **OKLCH** em 100% dos componentes, garantindo harmonia visual e precisão de contraste em displays modernos (P3).
- **Estilização:** Tailwind CSS v4 compilado via Lightning CSS (Rust nativo).
- **Acessibilidade:** Primitivos Radix UI sem estilização acoplada, cumprindo WCAG 2.2 AA com tap targets mínimos de 24x24px.
- **Arquitetura de Casca Dupla:** 
  - `AdminShell.tsx` para desktop/gestão com colapso fluído;
  - `MobileShell.tsx` com navegação inferior e suporte a gestos.

---

## 2. Camada Offline-First & PWA
- **Service Worker:** Gerenciado via `vite-plugin-pwa` e Workbox 7 com estratégia `autoUpdate`.
- **Estratégias de Cache:** `CacheFirst` para assets imutáveis e `StaleWhileRevalidate` com fallback offline.
- **Fila de Sincronização Segura:** Armazenamento local estruturado (IndexedDB / localStorage) com empacotamento FIFO.
- **Criptografia Anti-Adulteração:** Toda transação offline recebe assinatura gerada via **Web Crypto API (HMAC SHA-256)** no momento da criação. Transações com assinatura divergente são isoladas em quarentena imediata.

---

## 3. Camada de Estado & Esquemas
- **Gerenciamento de Cache Assíncrono:** **TanStack Query v5** com deduplicação nativa, garbage collection inteligente e mutações otimistas com restauração de snapshot em caso de erro.
- **Validação de Contrato no Edge:** Schemas Zod v4 / Valibot aplicados na fronteira de dados (input de formulários e parsing de payloads de API).
- **Estado Local Efêmero:** Zustand / Nanostores exclusivamente para UI transitória.

---

## 4. Camada de Backend (Vertical Slice Architecture)
- **Monólito Modular VSA:** Eliminação total de camadas horizontais dispersas. Cada funcionalidade é encapsulada em uma fatia vertical contendo rota, handler, entidade e teste.
- **Runtime de Alta Velocidade:** Python moderno com tipagem estrita (Litestar / FastAPI) ou Fastify/Elysia para runtimes JavaScript/Bun.
- **Isolamento de Domínio:** Comunicação entre fatias realizada exclusivamente via contratos tipados e eventos de domínio.

---

## 5. Camada de Banco de Dados & Persistência
- **Padrão-Ouro SQLite WAL:**
  - `PRAGMA journal_mode = WAL;` (Leituras e escritas concorrentes simultâneas);
  - `PRAGMA synchronous = NORMAL;` (Proteção contra corrupção com throughput máximo);
  - `PRAGMA busy_timeout = 5000;` (Resiliência contra contenção de escrita sob alta concorrência).
- **Alternativa Corporativa:** PostgreSQL 16+ com suporte a JSONB indexado e streaming replication.
- **Gerenciador de Esquemas:** Drizzle ORM ou Alembic com migrações determinísticas, testáveis e 100% reversíveis.

---

## 6, 7, 8 e 9. O Quarteto Sine Qua Non Dinâmico (Lei #10)
Toda aplicação nasce com os 4 estúdios plenamente funcionais:
1. **/api (OpenAPI Studio):** Documentação interativa em OpenAPI 3.1 com interface de testes em tempo real;
2. **/webhook (Webhook Studio):** Gestão visual de endpoints de webhook, inspeção detalhada de cabeçalhos/payloads e botão de re-disparo (replay) de eventos assinado com HMAC;
3. **/mcp (MCP Studio):** Servidor Model Context Protocol nativo expondo ferramentas, recursos e prompts operacionais para consumo direto por agentes de IA e IDEs agênticas;
4. **/docs (Central de Documentação):** Manual interativo e dinâmico sincronizado em tempo real com a versão e os módulos ativos da aplicação.

---

## 10. Camada de Qualidade, Portões & Testes (Lei #5 e Lei #13)
- **Zero Mocks em Produção (Lei #5):** 100% de código real e tipado; proibição absoluta de stubs que simulam funcionamento inexistente.
- **Portões que Provam que Mordem (Lei #13):** Todo Quality Gate (`G_*.py`) possui obrigatoriamente suíte de testes automatizados que forçam deliberadamente o cenário de falha e assertam `exit 1`.
- **Validação Automatizada Contínua:**
  - `modulos/02-triade-motores/fluxo-01-pure/gates/G_STACK_PADRAO_OURO.py`
  - `modulos/02-triade-motores/fluxo-01-pure/gates/G_TEMPLATE_TANSTACK_OFFLINE.py`
  - `modulos/02-triade-motores/fluxo-01-pure/gates/G_NOVE_CAMADAS_MERCADO.py`
  - `modulos/03-plataforma-e-entrega/gates/G_QUARTETO_SINE_QUA_NON.py`
  - `modulos/02-triade-motores/fluxo-02-open/gates/G_COMPONENTE_AGNOSTICO.py`
