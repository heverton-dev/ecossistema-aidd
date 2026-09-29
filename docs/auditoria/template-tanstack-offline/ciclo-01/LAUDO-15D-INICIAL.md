# Laudo 15-D de Auditoria Arquitetural — Fase 1 (Inspetor)

## 1. Identificação da Ferramenta
- **Nome da Ferramenta:** `template-tanstack-offline` (Template Canônico Padrão-Ouro de Frontend PWA, Offline-First e Quarteto Dinâmico)
- **Descrição Breve:** Template canônico determinístico para geração de aplicações frontend com TanStack (Start/Router/Query), design tokens OKLCH, Impeccable UX/UI, cascas responsivas duplas (`AdminShell` e `MobileShell`), fila offline local com assinatura criptográfica HMAC e estúdios integrados do Quarteto Sine Qua Non (`/api`, `/webhook`, `/mcp`, `/docs`).
- **Comando de Gatilho:** `python ecossistema.py run-fluxo --template tanstack-offline` ou incorporação automática nos fluxos canônicos (`pure`, `open`, `freedom`).

---

## 2. A Matriz Anatômica (Lens 15-D)

### Fase 1: Governança e Blindagem
- **D1. Contratos e Regras:** 
  - Lei #1 (Determinismo): Geração via templates determinísticos parametrizados sem intervenção estocástica.
  - Lei #6 (Agnostic Supremacy): Ausência estrita de lock-in com fornecedores terceiros (sem SDKs proprietários como Lovable Auth ou Supabase rígido).
  - Lei #10 (Quarteto Dinâmico): Inclusão visual e funcional nativa de `/api`, `/webhook`, `/mcp` e `/docs` embutidos no shell de gestão.
  - Lei #11 (Padrão-Ouro de Stack): Formalização do TanStack (Start/Router/Query) como stack padrão-ouro de frontend/PWA do ecossistema.
  - Regra Impeccable: Aderência aos tokens de design em `DESIGN.md` com espaços de cor modernos (`oklch`).
- **D2. Input e Gatilhos:** 
  - Insumo: Configuração do projeto via `PLANNER.json` ou parâmetros de scaffolding (`app_name`, rotas de domínio, paleta de cores e credenciais agnósticas de API).
  - Requisitos de Estado: Repositório com suporte a Node.js / Vite / Bun / pnpm e estrutura modular VSA.
- **D3. Raio de Impacto e Isolamento:** 
  - Isolamento completo no diretório de frontend (`frontend/` ou raiz do app empacotado).
  - Worktrees efêmeras de build durante a compilação do pipeline sem poluição do branch de trabalho.
  - Armazenamento offline estritamente restrito a `localStorage` e `IndexedDB` com isolamento de origem no navegador.
- **D4. Componentes e Fractalidade:** 
  - Skill Impeccable para refinamento de layout e acessibilidade WCAG.
  - Primitivos Radix UI + Tailwind CSS para acessibilidade de baixo nível.
  - TanStack Router + TanStack Query para roteamento tipado e cache reativo.
  - Service Worker registrado (`/sw.js`) para suporte PWA multi-plataforma (iOS, Android, Desktop).

---

### Fase 2: O Chão de Fábrica (Workflow Agêntico)
- **D5. Visão e Escopo:** 
  - Prover uma fundação de frontend de extrema elegância, responsividade automática entre desktop e mobile, e resiliência offline com sincronização segura.
- **[Estágio 1 - Design & Tokens] D6. O que o Estágio Faz:** Compila variáveis CSS e tokens semânticos baseados no `DESIGN.md`.
- **[Estágio 1 - Design & Tokens] D7. O que o Estágio Recebe:** Arquivo de tokens OKLCH e configuração de tipografia.
- **[Estágio 1 - Design & Tokens] D8. O que o Estágio Processa:** Geração estática de classes utilitárias Tailwind e variáveis no `:root` e `.dark`.
- **[Estágio 1 - Design & Tokens] D9. O que o Estágio Entrega:** Folhas de estilo `styles.css` e tokens prontos para importação.
- **[Estágio 2 - Shells Responsivos] D6. O que o Estágio Faz:** Instancia `AdminShell.tsx` (desktop) e `MobileShell.tsx` (mobile) com chaveamento automático via hook `use-mobile`.
- **[Estágio 2 - Shells Responsivos] D7. O que o Estágio Recebe:** Definição de rotas, menu de navegação e módulos de domínio.
- **[Estágio 2 - Shells Responsivos] D8. O que o Estágio Processa:** Renderização adaptativa de layout, gavetas de navegação (bottom bar vs sidebar) e cabeçalhos de contexto.
- **[Estágio 2 - Shells Responsivos] D9. O que o Estágio Entrega:** Árvore de componentes de layout base e rotas estruturadas.
- **[Estágio 3 - Camada Offline & Sincronização] D6. O que o Estágio Faz:** Monta a fila de mutações offline (`sync-queue.ts`) e o Service Worker (`pwa.ts`).
- **[Estágio 3 - Camada Offline & Sincronização] D7. O que o Estágio Recebe:** Tipos de eventos de sincronização e segredo local de assinatura.
- **[Estágio 3 - Camada Offline & Sincronização] D8. O que o Estágio Processa:** Enfileiramento em fila local com cálculo de HMAC para integridade e disparo de sincronização sequencial ao restabelecer conectividade.
- **[Estágio 3 - Camada Offline & Sincronização] D9. O que o Estágio Entrega:** Módulo de sincronização determinístico testável e Service Worker com cache-first para assets.
- **[Estágio 4 - Estúdios do Quarteto] D6. O que o Estágio Faz:** Anexa as 4 rotas dinâmicas do Quarteto Sine Qua Non (`/api`, `/webhook`, `/mcp`, `/docs`) na navegação.
- **[Estágio 4 - Estúdios do Quarteto] D7. O que o Estágio Recebe:** Especificações OpenAPI, contratos de Webhooks, catálogo de MCPs e documentação viva.
- **[Estágio 4 - Estúdios do Quarteto] D8. O que o Estágio Processa:** Montagem de views interativas com a mesma identidade visual Impeccable do sistema.
- **[Estágio 4 - Estúdios do Quarteto] D9. O que o Estágio Entrega:** Quádruplo funcional integrado e acessível visualmente no painel administrativo.
- **D10. Orquestração e Topologia:** 
  - Fluxo unidirecional de injeção: Forge -> Planner -> Scaffolder TanStack -> Verificação de Portões -> Build/Preview.

---

### Fase 3: Resiliência e Economia (Engenharia Operacional)
- **D11. Tratamento de Exceções e Fallback:** 
  - Em falha de conexão: transações interceptadas sem travar a UI; armazenamento imediato na fila offline com status visual de "pendente de sincronização".
  - Em detecção de assinatura HMAC inválida: bloqueio e quarentena da transação local para prevenir adulteração de dados em repouso.
  - Em erros de renderização: Error Boundaries atômicos por rota com fallbacks de UI elegantes.
- **D12. Observabilidade e Frugalidade:** 
  - Zero dependências pesadas desnecessárias; compilação rápida via Vite/Rolldown.
  - Telemetria de transações offline e status do Service Worker emitidos para o console em modo debug ou integráveis a sinks de auditoria.

---

### Fase 4: O Inspetor e a Expedição (Validação)
- **D13. Quality Gates (Portões):** 
  - Portão 15-D: `docs/auditoria/template-tanstack-offline/G_auditoria_15D.py`.
  - Portão de Integridade da Fila: Teste automatizado de enfileiramento, assinatura HMAC e drenagem em restabelecimento de rede.
  - Portão de Contrato do Quarteto: Validação da presença e acessibilidade das rotas `/api`, `/webhook`, `/mcp`, `/docs`.
- **D14. Critério de Rejeição (Rollback):** 
  - Presença de imports de SDKs proprietários não agnósticos (rejeição imediata `exit 1`).
  - Falha na validação de integridade criptográfica da fila offline (`exit 1`).
  - Ausência de qualquer um dos 4 estúdios do Quarteto Sine Qua Non (`exit 1`).
- **D15. Output Consolidado e Handoff:** 
  - Pacote de template em `componentes/compartilhado/templates/frontend-tanstack/` pronto para ser consumido pelos 3 fluxos (`pure`, `open`, `freedom`) via `aidd-forge`.

---

## 3. Matriz de Avaliação da Execução
- [x] A ferramenta isolou seu raio de impacto corretamente?
- [x] O workflow seguiu as fases sem alucinações de LLM em tarefas mecânicas?
- [x] O output final passou em todos os Quality Gates e emitiu o Handoff?
