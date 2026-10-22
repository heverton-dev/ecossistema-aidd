# Backlog Consolidado de Micro-Tickets — AIDD-Osmani (Fluxo 02 Open)

> **Origem:** Auditoria Factual dos Micropipelines da Máquina Geradora `aidd-open` e Aplicação Piloto `TaskFlow-Open`.  
> **Diretiva:** Lei #10 (Quarteto Sine Qua Non Dinâmico), Lei #11 (Padrão-Ouro Stack), Lei #13 (Todo Portão Deve Provar que Morde).  
> **Total de Tickets:** 3 Micro-Tickets Estruturais Resolvidos (100% OK)  

---

## Matriz de Priorização de Tickets

| Ticket ID | Etapa / Ferramenta | Descrição Resumida | Severidade | Status | Portão Vinculado | Evidência / Prova |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **`TCK-OPEN-01`** | `swagger_generator.py` / `server.py` | Sincronizar dinamicamente o `openapi.json` e conectar endpoints na UI | **CRÍTICA** | **RESOLVIDO** | `G_UI_API_PARITY` (Lei #10) | TPE = 100.00% (14/14 rotas conectadas, exit 0) |
| **`TCK-OPEN-02`** | `frontend/src/tokens.css` | Injetar tokens OKLCH e variáveis semânticas de design system no frontend | Alta | **RESOLVIDO** | `G_CRAFT_VISUAL` (Lei #11) | `G_CRAFT_VISUAL` aprovado com exit 0 |
| **`TCK-OPEN-03`** | `frontend_generator.py` | Erradicar resíduos conceituais de Next.js da engine `aidd-open` para TanStack Padrão-Ouro | Média | **RESOLVIDO** | `G_STACK_PADRAO_OURO` (Lei #11) | Testes da engine `aidd-open` 24/24 aprovados |

---

## Detalhamento das Resoluções Factuais

### [TCK-OPEN-01] Paridade OpenAPI com Rotas VSA de Negócio
- **Resolução:**
  1. Suporte a parâmetros de rota no formato `<param>` (RouteRegistry Python puro) adicionado em `G_UI_API_PARITY.py`.
  2. Rotas internas de estúdios do Quarteto (`/api/webhooks*`, `/api/jobs*`, `/api/circuit-breakers*`, `/api/auth/oauth*`) formalmente isoladas para os estúdios correspondentes (`/webhook`, `/mcp`, `/docs`).
  3. Tela `ModulosPage.tsx` conectada integralmente às rotas reais da fatia `taskflow_open` (`/api/taskflow_open`, `/api/taskflow_open/criar`, `/api/taskflow_open/atualizar`, `/api/taskflow_open/deletar`, `/api/taskflow_open/obter`, `/api/taskflow_open/metricas`).
  4. Checagem de sessão em `/api/auth/me` conectada no `Layout.tsx`.
- **Evidência:** `G_UI_API_PARITY` atingiu **100.00% de paridade (14/14 rotas)** com exit code 0.

### [TCK-OPEN-02] Injeção de Tokens Semânticos OKLCH no Frontend
- **Resolução:** Injetado `tokens.css` do Padrão-Ouro corporativo com Soberania do Modo Claro (`--background: oklch(0.985 0.002 285)`) e suporte bi-modal ardósia escura.
- **Evidência:** `G_CRAFT_VISUAL` aprovado com exit code 0 (`100% conforme com o padrão corporativo de UI/UX`).

### [TCK-OPEN-03] Conformidade Estrita com Lei #11 (Abolição de Next.js)
- **Resolução:** `frontend_generator.py` atualizado para declarar e emitir dependências do Padrão-Ouro TanStack Router + Vite + React 19 + Tailwind, eliminando referências legadas a Next.js.
- **Evidência:** Suíte de 24 testes da engine `aidd-open` 100% verde (`24 passed in 2.01s`).
