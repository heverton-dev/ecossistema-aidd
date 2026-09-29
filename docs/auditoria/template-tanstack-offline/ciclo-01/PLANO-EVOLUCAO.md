# Plano de Evolução (Fase 2) - template-tanstack-offline

Este plano foi gerado pelo Arquiteto (Fase 2) do Pipeline Linear de Auditoria 4F, com o objetivo de estruturar e certificar o template canônico `template-tanstack-offline` em conformidade com o Laudo 15-D e a Definição de Pronto (DoD).

## Estratégia de Execução
Todos os tickets abaixo requerem ciclo TDD estrito (Red-Green-Refactor). Para cada requisito funcional, testes automatizados (exit 0 / exit 1) devem ser criados antes da implementação real.

### Ticket 1: Extração e Canonicalização do Molde TanStack (Refere-se a D1 / D5 / DoD 1)
- **Falha 15-D:** `D1. Contratos e Regras`
- **Artefato de Handoff:** `componentes/compartilhado/templates/frontend-tanstack/template-manifest.json`
- **Requisito TDD (Red):** Criar teste que falhe caso o diretório canônico do template não contenha a configuração pura do TanStack (sem referências a Lovable Auth).
- **Implementação Técnica:**
  - Extrair de `rotaprime-replica` a fundação visual base: `DESIGN.md` com tokens OKLCH, `styles.css` e configuração de tipografia corporativa.
  - Sanitizar dependências proprietárias, estabelecendo `package.json` agnóstico com TanStack Start, Router, Query e Tailwind.
- **Verificação (Green):** Teste de integridade do template passa com exit 0 ao validar ausência de pacotes proprietários.
- **Construtor Prompt (EN):**
  - Write test first: assert absence of proprietary auth packages in template package.json.
  - Extract base visual design tokens (oklch, typography, styles.css) to componentes/compartilhado/templates/frontend-tanstack/.
  - Provide sanitized package.json and template-manifest.json.
  - Run test to ensure 100% agnostic package structure.

### Ticket 2: Casca Dupla Responsiva e Integração do Quarteto (Refere-se a D6 / D9 / DoD 2)
- **Falha 15-D:** `D6. O que o Estágio Faz`
- **Artefato de Handoff:** `componentes/compartilhado/templates/frontend-tanstack/src/components/AdminShell.tsx`
- **Requisito TDD (Red):** Teste deve falhar se os 4 estúdios obrigatórios (`/api`, `/webhook`, `/mcp`, `/docs`) não estiverem mapeados na navegação do shell administrativo.
- **Implementação Técnica:**
  - Implementar `AdminShell.tsx` (desktop) e `MobileShell.tsx` (mobile) com chaveamento baseado no hook `use-mobile.tsx`.
  - Inserir links de navegação e páginas stub elegantes para os 4 pilares da Lei #10 (OpenAPI, Webhooks, MCP e Docs) com estética Impeccable.
- **Verificação (Green):** Teste de renderização e rotas do shell valida presença e acessibilidade dos 4 estúdios.
- **Construtor Prompt (EN):**
  - Write test first: verify AdminShell and MobileShell expose /api, /webhook, /mcp, /docs navigation links.
  - Implement AdminShell.tsx, MobileShell.tsx and use-mobile.tsx inside template components.
  - Wire aesthetic route placeholders adhering to Impeccable standards.
  - Run test to confirm route presence and layout toggle.

### Ticket 3: Resiliência Offline e Fila Assinada HMAC (Refere-se a D8 / D11 / DoD 3)
- **Falha 15-D:** `D8. O que o Estágio Processa`
- **Artefato de Handoff:** `componentes/compartilhado/templates/frontend-tanstack/src/lib/offline/sync-queue.ts`
- **Requisito TDD (Red):** Testar que itens adicionados à fila offline sem assinatura válida HMAC sejam rejeitados ou sinalizados como corrompidos (exit 1).
- **Implementação Técnica:**
  - Extrair e modularizar `sync-queue.ts` com gerador de assinatura de integridade HMAC SHA-256 (`seguranca.ts`).
  - Implementar Service Worker (`pwa.ts`) com rotinas de interceptação de rede e eventos de instalação PWA.
- **Verificação (Green):** Teste automatizado de enfileiramento offline e verificação criptográfica passa com sucesso.
- **Construtor Prompt (EN):**
  - Write test first: simulate offline queue item tampering and assert HMAC verification fails.
  - Implement sync-queue.ts and seguranca.ts in template lib/offline.
  - Add Service Worker registration helper in pwa.ts.
  - Run test to ensure tamper-proof queue persistence.

### Ticket 4: Quality Gate e Suíte de Validação Determinística (Refere-se a D13 / D14 / DoD 4)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `gates/G_TEMPLATE_TANSTACK_OFFLINE.py`
- **Requisito TDD (Red):** Criar `gates/G_TEMPLATE_TANSTACK_OFFLINE.py` que falhe (exit 1) quando executado contra um diretório incompleto de template.
- **Implementação Técnica:**
  - Codificar o portão determinístico que verifica: 1) ausência de lock-in, 2) presença dos componentes de casca dupla, 3) presença do módulo de fila HMAC e 4) rotas do Quarteto Sine Qua Non.
  - Registrar teste que quebra deliberadamente cada condição e asserta exit 1 (conforme Lei #13 - Portão Deve Provar que Morde).
- **Verificação (Green):** Gate retorna exit 0 na verificação do template e exit 1 na prova de mordida.
- **Construtor Prompt (EN):**
  - Write test first: create broken template fixtures and assert gate exits with code 1.
  - Implement gates/G_TEMPLATE_TANSTACK_OFFLINE.py checking lock-in absence, shells, HMAC queue and Quarteto.
  - Add test proving gate bites according to Inviolable Law #13.
  - Run gate test battery to ensure exit 0 on genuine template.
