# Padrão-Ouro Arquitetural por Camadas — Estado da Arte de Mercado (2026)

> **Documento Canônico de Arquitetura:** `docs/padroes/PADRAO-OURO-ARQUITETURA-CAMADAS-MERCADO.md`  
> **Classificação:** Mega Ultra Padrão de Mercado — Engenharia de Software de Alta Performance, Offline-First, PWA e Governança Agêntica.

---

## Sumário Executivo

Este documento estabelece o referencial arquitetural definitivo para todas as aplicações desenvolvidas ou geradas pelo ecossistema (`aidd-pure`, `aidd-open`, `aidd-freedom`). Analisa em profundidade cada uma das **9 camadas críticas** de uma aplicação moderna, fundamentando escolhas técnicas nas tecnologias mais avançadas do mercado global (TanStack Start, Local-First Sync Engines, PWA Capabilities v2, Tailwind v4, OKLCH, Vertical Slice Architecture e o Quarteto Sine Qua Non).

```
┌────────────────────────────────────────────────────────────────────────┐
│                   ARQUITETURA CANÔNICA POR CAMADAS                     │
├────────────────────────────────────────────────────────────────────────┤
│ Camada 1: Design Tokens, Estética & Microinterações (OKLCH + Impeccable) │
│ Camada 2: Roteamento & Shells Isomórficos (TanStack Router + Start)     │
│ Camada 3: PWA Moderno & Web Capabilities (Vite PWA + Workbox 7)        │
│ Camada 4: Resiliência Offline-First & Sincronização (Local-First Engine) │
│ Camada 5: Estado Reativo, Cache & Contratos (TanStack Query + Zod)     │
│ Camada 6: Backend Modular & API (VSA + OpenAPI 3.1)                     │
│ Camada 7: Persistência & Transações (PostgreSQL / SQLite WAL)          │
│ Camada 8: Quarteto Sine Qua Non Dinâmico (/api, /webhook, /mcp, /docs)  │
│ Camada 9: Observabilidade, Quality Gates & Testes Reais (Zero Stubs)   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Camada 1: Design Tokens, Estética & Microinterações (Visual Shell)

### O Estado da Arte
O mercado abandonou modelos legados de cor (RGB/HSL) em favor de espaços de cor perceptualmente uniformes (**OKLCH**) suportados por monitores Wide Color Gamut (Display P3). A camada visual é governada por tokens semânticos e pela disciplina estética **Impeccable**.

### Diretrizes de Engenharia
1. **Espaço de Cor OKLCH:**
   - Luminância perceptual constante independente do matiz: garante contraste acessível idêntico em qualquer tema (claro/escuro).
   - Semântica de paleta:
     - `primary`: Ação primária de alto impacto (ex: `oklch(0.555 0.215 27.5)`);
     - `background` / `foreground`: Neutros balanceados com micro-saturação para evitar o cinza "lavado";
     - Estados funcionais: `destructive`, `success`, `warning`, `info` calibrados em luminosidade equivalente.
2. **Motor de Estilização — Tailwind CSS v4:**
   - Compilação nativa em Rust via Lightning CSS (10x mais veloz que PostCSS).
   - Diretiva canônica `@theme` no CSS elimina a dependência de arquivos de configuração JS pesados.
3. **Primitivos Acessíveis (Radix UI / Zag.js / React Aria):**
   - Headless components que provêm 100% de conformidade WCAG 2.2 AA (navegação completa por teclado, ARIA roles dinâmicas, focus trap e tap targets mínimos de 24x24px no mobile).
4. **Tipografia Estruturada:**
   - Fonte corporativa com rendering de precisão (Public Sans / Geist / Inter).
   - Escalas tipográficas estritas com leading proporcional para evitar quebras em telas densas.

---

## Camada 2: Roteamento & Shells Isomórficos (App Shell)

### O Estado da Arte
Aplicações de alto nível não utilizam roteamento frouxo baseado em strings. O padrão-ouro é o **TanStack Router / Start**, oferecendo tipagem ponta a ponta em tempo de compilação, validação de Search Params e carregamento com zero layout shift (CLS < 0.1).

### Diretrizes de Engenharia
1. **Tipagem Estrita de Rotas (Type-Safe Routing):**
   - Rotas, parâmetros de URL (`$id`) e query strings são tipados e autocompletados pelo compilador.
   - Validação de Search Params em tempo de execução via Zod: parâmetros corrompidos na URL nunca quebram o componente filho.
2. **Casca Dupla Adaptativa (Dual Shell Architecture):**
   - **`AdminShell.tsx` (Desktop/Tablet):**
     - Sidebar fixa com hierarquia visual clara, colapso suave e indicador persistente de conectividade;
     - Acesso direto e contínuo aos estúdios de governança e documentação.
   - **`MobileShell.tsx` (Mobile First / Viewport < 768px):**
     - Header enxuto com status de rede simplificado;
     - Bottom Navigation Bar com 3 a 5 pontos de fuga de alta frequência;
     - Suporte a gestos (swipe to back, pull-to-refresh) e feedback háptico em ações críticas.
3. **Preload Inteligente:**
   - Preload de rotas e dados no hover ou no viewport (`preload: 'intent'`), transformando navegações em transições instantâneas de 0ms perceptíveis.

---

## Camada 3: PWA Moderno & Web Capabilities (PWA & Native Bridge)

### O Estado da Arte
O PWA em 2026 transcendeu o mero "ícone na tela". Com o amadurecimento das APIs de capacidades web, um PWA entrega paridade quase total com aplicações nativas no iOS, Android, macOS e Windows.

### Diretrizes de Engenharia
1. **Orquestração de Service Worker (`vite-plugin-pwa` + Workbox 7):**
   - Modo `autoUpdate` para atualização transparente em segundo plano, evitando telas "presas" em versões obsoletas;
   - Geração determinística de Web App Manifest v2 (ícones mascaráveis, splash screens automáticas, `display: standalone`, `theme_color`, shortcuts de ação rápida);
   - Registro resiliente com tratamento de erros e fallbacks específicos para iOS Safari e Android Chromium.
2. **Estratégias de Cache no Service Worker:**
   - **Static Assets (JS, CSS, Fontes, SVGs):** `CacheFirst` com hash no nome de arquivo (invalidação atômica);
   - **Imagens e Mídias:** `CacheFirst` com expiração de tempo e cota máxima (ex: maxEntries: 60, maxAgeSeconds: 30 dias);
   - **Rotas de Documento (HTML/Shell):** `NetworkFirst` com fallback instantâneo para o shell pré-armazenado no cache offline.
3. **APIs de Plataforma Nativas (Web Capabilities):**
   - **StorageManager API:** Solicitação de `navigator.storage.persist()` para garantir que o navegador nunca expurgue os dados offline do usuário durante limpezas automáticas de disco;
   - **Web Locks API:** Coordenação segura de acessos concorrentes entre múltiplas abas da aplicação ao banco local;
   - **Badging API:** Notificação de itens pendentes de sincronização diretamente no ícone do aplicativo no sistema operacional (`navigator.setAppBadge`);
   - **Instalabilidade Guiada:** Interceptação do evento `beforeinstallprompt` com modal de onboarding customizado, e guia visual específico para Safari no iOS ("Compartilhar -> Adicionar à Tela de Início").

---

## Camada 4: Resiliência Offline-First & Motor de Sincronização

### O Estado da Arte
Aplicações de referência não tratam a falta de conexão como um erro (`fetch failed`), mas como um estado operacional normal. O paradigma **Local-First** garante que todas as leituras e escritas aconteçam instantaneamente no armazenamento local, enquanto a sincronização para a nuvem ocorre em background de forma determinística.

### Diretrizes de Engenharia
1. **Fila Local Imutável com Assinatura Criptográfica HMAC:**
   - Toda mutação realizada offline é empacotada em um payload com identificador UUID v7, timestamp ISO e kind de evento;
   - Cálculo de assinatura digital via **Web Crypto API (HMAC SHA-256)** no momento da criação: qualquer tentativa de manipulação local dos dados em repouso no `localStorage` ou `IndexedDB` invalida a assinatura e envia o item para quarentena;
   - Despacho sequencial estrito (FIFO): previne reversão de ordem lógica (ex: não processar uma conclusão antes da criação).
2. **Motores de Sincronização de Nova Geração (Mercado 2026):**
   - **Zero (Rocicorp):** Sincronização baseada em consultas reativas com cache SQLite embutido no client;
   - **ElectricSQL / PGlite:** Postgres compilado em WebAssembly rodando direto no navegador com sincronização reativa bidirecional e CRDTs;
   - **PowerSync:** Replicação parcial de alta escala entre SQLite do cliente e PostgreSQL de produção.
3. **Resolução de Conflitos e Idempotência:**
   - Chaves de idempotência únicas geradas no cliente e enviadas no cabeçalho `Idempotency-Key`;
   - O servidor garante que retransmissões acidentais resultem no mesmo estado sem duplicações de registros.

---

## Camada 5: Estado Reativo, Cache & Contratos de Dados

### O Estado da Arte
Separação estrita entre **Estado do Servidor (Server State)** e **Estado da Interface (Client UI State)**. O estado do servidor pertence ao cache assíncrono; o estado da interface deve ser atômico, leve e de escopo mínimo.

### Diretrizes de Engenharia
1. **Gerenciamento de Cache com TanStack Query v5:**
   - Garbage collection automatizado e deduplicação de requisições idênticas simultâneas;
   - **Optimistic Updates:** A interface reflete imediatamente a intenção do usuário antes da resposta da rede; em caso de falha de rede irrecuperável, o estado realiza rollback atômico sem corrupção visual.
2. **Contratos e Validação de Esquema (Zod v4 / Valibot):**
   - Validação bidirecional rigorosa: dados que chegam da API e dados digitados pelo usuário passam pelo mesmo validador;
   - Inferência automática de tipos TypeScript (`z.infer<typeof Schema>`), garantindo que alterações no backend quebrem a compilação do frontend antes de chegarem à produção.
3. **Estado Global Efêmero:**
   - Utilização de stores atômicas (Zustand ou Nanostores) apenas para dados voláteis de tela (modais abertos, abas ativas, filtros de tabela), eliminando re-renderizações em cascata.

---

## Camada 6: Backend Modular & API (VSA Backend)

### O Estado da Arte
Arquitetura por Fatias Verticais (**Vertical Slice Architecture — VSA**). Em vez de camadas horizontais que espalham a mesma funcionalidade por controllers, services e repositories distantes, cada fatia de negócio é autossuficiente e isolada.

### Diretrizes de Engenharia
1. **Vertical Slice Architecture (VSA):**
   - Cada funcionalidade reside em seu próprio módulo:
     ```
     src/features/rotas/
       ├── criar_rota.py (ou .ts)     # Handler + Rota + Contrato
       ├── models.py                  # Entidade da fatia
       ├── test_criar_rota.py         # Teste de contrato da fatia
     ```
   - Mudanças em uma funcionalidade possuem raio de impacto zero sobre as demais.
2. **Contrato OpenAPI 3.1 Dinâmico e Vivo:**
   - Schemas de rotas gerados deterministicamente a partir do código fonte (sem documentações manuais desatualizadas);
   - Tipagem automática para o frontend gerada via pipelines do ecossistema.
3. **Frameworks de Baixa Latência:**
   - Python moderno (Litestar / FastAPI com Pydantic v2 / uvloop);
   - Alternativa Node/Bun: Fastify ou Elysia com validação nativa TypeBox.

---

## Camada 7: Persistência de Dados & Concorrência

### O Estado da Arte
Persistência estruturada, determinística e transacional. Eliminação de bancos NoSQL frouxos sem esquema e adoção de motores relacionais modernos com alto throughput.

### Diretrizes de Engenharia
1. **Motores Recomendados:**
   - **PostgreSQL 16+:** Padrão-ouro empresarial com suporte a JSONB indexado, row-level security (RLS) e replicação lógica para sync engines.
   - **SQLite com WAL Mode (Write-Ahead Logging):** Para monólitos e microsserviços de borda:
     - `PRAGMA journal_mode = WAL;` (leituras e escritas concorrentes sem travamento);
     - `PRAGMA synchronous = NORMAL;` (segurança de dados com máximo IOPS);
     - `PRAGMA busy_timeout = 5000;` (elimina erros de banco travado sob carga).
2. **Migrations Determinísticas e Reversíveis:**
   - Esquemas versionados via código (Drizzle ORM ou Alembic);
   - Proibição absoluta de alterações manuais no banco sem script de migração auditado.

---

## Camada 8: O Quarteto Sine Qua Non Dinâmico

### O Estado da Arte
Definido pela **Lei #10 do Ecossistema AIDD**, toda aplicação gerada no ecossistema deve nascer nativamente com 4 estúdios completos, interativos e integrados à sua casca visual.

### Especificação dos 4 Estúdios
| Estúdio | Rota | Finalidade Arquitetural |
|---|---|---|
| **OpenAPI Studio** | `/api` | Documentação interativa (Swagger / Scalar) com teste dinâmico de todos os endpoints e schemas do sistema. |
| **Webhook Studio** | `/webhook` | Painel de controle para registro de webhooks, inspeção de entregas, visualização de payloads e re-disparo (replay) de eventos com assinatura HMAC. |
| **MCP Studio** | `/mcp` | Catálogo de servidores e ferramentas MCP (Model Context Protocol) nativos do sistema para consumo seguro por agentes de IA e IDEs agênticas. |
| **Central de Documentação** | `/docs` | Manual do usuário e documentação técnica viva em Markdown, sincronizada deterministicamente com os módulos ativos do sistema. |

---

## Camada 9: Observabilidade, Quality Gates & Testes Reais

### O Estado da Arte
Engenharia baseada em **Zero Stubs / Zero Mocks (Lei #5)** e **Portões Determinísticos que Provam que Mordem (Lei #13)**. Não se aceitam testes falsos ou que validam apenas caminhos felizes sem comprovar rejeição em caso de falha.

### Diretrizes de Engenharia
1. **Tooling de Alta Velocidade:**
   - Linter e Formatter: **Biome** (execução em Rust sub-milissegundos, substituindo a combinação lenta de ESLint + Prettier);
   - Test Runner: **Vitest** (compatível com Vite, multithreaded e instantâneo) para unit/integration tests;
   - E2E: **Playwright** rodando contra instâncias reais de navegador com gravação de traces de falha.
2. **Regra de Ouro dos Quality Gates (Lei #13):**
   - Todo portão de qualidade (`G_*.py`) DEVE ter um teste automatizado que force a condição de falha e asserte `exit 1`. Portão que só testa `exit 0` é classificado como fachada.
3. **Métricas de Performance Real (Core Web Vitals):**
   - **LCP (Largest Contentful Paint):** < 2.0s;
   - **INP (Interaction to Next Paint):** ≤ 150ms;
   - **CLS (Cumulative Layout Shift):** < 0.05.

---

## Matriz de Conformidade Canônica para Geradores

Toda geração ou evolução de software pelos motores do ecossistema (`aidd-generator`, `aidd-factory`, `aidd-bridge`) deve auditar a aderência aos padrões deste documento conforme a tabela abaixo:

| Camada | Tecnologia Canônica | Verificação Automatizada |
|---|---|---|
| **1. Visual Shell** | Tailwind v4 + OKLCH + Radix UI + Impeccable | Validador de CSS & Tokens em `DESIGN.md` |
| **2. App Shell** | TanStack Router / Start + Casca Dupla (`Admin`/`Mobile`) | `G_TEMPLATE_TANSTACK_OFFLINE.py` |
| **3. PWA Engine** | `vite-plugin-pwa` + Workbox 7 + Web App Manifest v2 | Teste de registro de SW e manifest audit |
| **4. Offline-First** | Fila Local FIFO + Web Crypto HMAC SHA-256 | Teste de integridade de assinatura criptográfica |
| **5. State & Schema**| TanStack Query v5 + Zod v4 / Valibot | TypeScript Typecheck estrito (`tsc --noEmit`) |
| **6. Backend** | Python / Litestar / FastAPI (VSA) | Testes de contrato de rota |
| **7. Database** | PostgreSQL / SQLite WAL | Portão de concorrência e migrations reversíveis |
| **8. Quarteto** | `/api`, `/webhook`, `/mcp`, `/docs` integrados | `G_QUARTETO_SINE_QUA_NON.py` |
| **9. Quality Gates** | Pytest / Vitest / Playwright + Lei #13 | `G_PORTAO_PROVA_QUE_MORDE.py` |

---

*Documento aprovado e registrado para orientação determinística dos fluxos do ecossistema AIDD.*
