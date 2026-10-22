# ANATOMIA ATÔMICA DOS PIPELINES DO ECOSSISTEMA AIDD (MACRO ➔ MESO ➔ MICRO ➔ NANO)

> **Data de Emissão:** 21/10/2026  
> **Status:** Referência Canônica de Governança e Arquitetura de Pipelines  
> **Caso de Estudo Modelo:** `Revnault` / `proj_revops` (`C:\Users\trcnologia\Desktop\_inbox\proj_revops`)  
> **Leis Fundamentais Vinculadas:** Lei #1 (Determinismo), Lei #2 (Saída Binária), Lei #4 (Economia de Tokens), Lei #8 (Honestidade de Rótulo), Lei #10 (Quarteto Sine Qua Non), Lei #11 (Padrão-Ouro & Modo Claro Soberano), Lei #14 (Graph-First).

---

## 1. INTRODUÇÃO: O DIAGNÓSTICO FORENSE DA MÁQUINA GERADORA

O Ecossistema AIDD não é apenas um conjunto de scripts utilitários, mas uma **fábrica meta-orquestrada de software corporativo**. Durante as auditorias profundas de ponta a ponta (Pipeline Osmani), identificou-se uma disparidade estrutural entre a robustez do Backend gerado e a superficialidade de certas interfaces de Frontend:

1. **A Armadilha das Referências Genéricas:** Na ausência de uma ponte determinística entre a entrevista socrática e a pesquisa visual, o gerador tendia a usar atalhos mentais com aplicações "de vitrine" consagradas do Vale do Silício (*Linear*, *Asana*, *Stripe*). Se o domínio solicitado fosse um ERP cirúrgico e de consignação hospitalar (como o **Revnault**), a aplicação recebia cascas visuais de rastreador de tickets genérico.
2. **A Armadilha dos Primitivos Estáticos:** Componentes como `MetricCard`, `DataTable` e `KanbanBoard` foram assumidos como a "solução universal" para qualquer tela, levando à subutilização severa das regras de negócio do backend.
3. **O Caso Real Revnault (`proj_revops`):**
   - **Backend:** 19 sub-domínios, 196 rotas REST únicas, 223 operações HTTP no FastAPI.
   - **Frontend:** Apenas 27 chamadas `fetch()` mapeadas (comprovado pelo script analítico [`scratch_scan_frontend.py`](file:///C:/Users/trcnologia/Desktop/_inbox/proj_revops/scratch_scan_frontend.py)).
   - **Subutilização Real:** **87,89% dos motores ficaram invisíveis** para o usuário final, gerando "cascas cosméticas" onde botões complexos de contrato ou tecnovigilância ANVISA eram representados por uma caixa genérica de upload do R2 (`<R2DirectUploader />`).

Para sanar definitivamente esse comportamento, disseca-se a seguir a arquitetura do ecossistema em **4 níveis anatômicos estritos**: **MACRO**, **MESO**, **MICRO** e **NANO**.

---

## 2. NÍVEL MACRO: A TRÍADE CANÔNICA DE FLUXOS

O nível Macro rege a estratégia de vida e nascimento de qualquer software no ecossistema, dividida em 3 caminhos mutuamente exclusivos na entrada, mas convergentes na entrega:

```
                  ┌────────────────────────────────────────────────────────┐
                  │                 [1. FORGE] + [2. PLANNER]              │
                  │    (Governança Suprema + Intake Socrático + BDD/SDD)    │
                  └──────────────────────────┬─────────────────────────────┘
                                             │
             ┌───────────────────────────────┼───────────────────────────────┐
             ▼                               ▼                               ▼
    ┌─────────────────┐             ┌─────────────────┐             ┌─────────────────┐
    │    FLUXO 01     │             │    FLUXO 02     │             │    FLUXO 03     │
    │   `aidd-pure`   │             │   `aidd-open`   │             │  `aidd-freedom` │
    │   (Do Zero)     │             │ (Motores Open)  │             │   (Desacopla)   │
    │  TDD 8 Fases    │             │  Strapi/Directus│             │  Lovable/v0/Bolt│
    └────────┬────────┘             └────────┬────────┘             └────────┬────────┘
             │                               │                               │
             └───────────────────────────────┼───────────────────────────────┘
                                             ▼
                  ┌────────────────────────────────────────────────────────┐
                  │           [3. MASTER] ➔ [4. DISPATCH (VSA)]            │
                  │         Harmonização Monólito Modular + Worktrees      │
                  └──────────────────────────┬─────────────────────────────┘
                                             ▼
                  ┌────────────────────────────────────────────────────────┐
                  │          [7. ENTERPRISE] ➔ [8. OPS] ➔ [9. GATES]       │
                  │         Blindagem SHA-256 + Docker + 54 Macro-Gates    │
                  └──────────────────────────┬─────────────────────────────┘
                                             ▼
                  ┌────────────────────────────────────────────────────────┐
                  │                 [10. COMMIT CONSOLIDADO]               │
                  │             Selo HMAC + Evidência de Entrega           │
                  └────────────────────────────────────────────────────────┘
```

1. **FLUXO 01 — `aidd-pure` (`/pure`):**
   - *Missão:* Construção do zero absoluto orientada a TDD estrito (Red-Green-Refactor).
   - *Stack Padrão-Ouro (Lei #11):* Backend Python puro com SQLite WAL (ou PostgreSQL), contratos OpenAPI 3.1 tipados, Frontend TanStack Router + React 19 + TypeScript + Tailwind CSS.
2. **FLUXO 02 — `aidd-open` (`/aidd-open` ou `/factory`):**
   - *Missão:* Curadoria e orquestração de fatias baseadas em motores open-source consagrados (ex: Strapi, Directus, n8n, Superset, Cal.com, Evolution API).
   - *Isolamento:* Integração via fatias verticais VSA autocontidas sem dependências cruzadas fora de `interface.py`.
3. **FLUXO 03 — `aidd-freedom` (`/freedom`):**
   - *Missão:* Desacoplamento cirúrgico de aplicações concebidas em plataformas low-code/unificadas (Lovable, v0, Bolt).
   - *Eradicação de Lock-in (Lei #6):* Limpeza de credenciais Supabase/Firebase, substituição por banco relacional local (SQLite WAL/Postgres) e preservação estrita do design craft.

---

## 3. NÍVEL MESO: A ESTEIRA DE 10 FERRAMENTAS CANÔNICAS

Cada fluxo macro executa obrigatoriamente a cadeia sequencial linear de 10 etapas parametrizadas com gates em dois níveis (Shift-Left):

| Etapa | Ferramenta / Módulo | Papel no Pipeline | Contrato Emitido / Consumido |
| :---: | :--- | :--- | :--- |
| **01** | `aidd-forge` | Bootstrap e blindagem de governança do repositório alvo (quality gates, hooks pre-commit, regras de IDE e fatiamento). | Emite: `HANDOFF_FORGE_PLANNER.json` (Contrato C1). |
| **02** | `aidd-planner` | Intake interativo: entrevista socrática, especificação BDD/SDD, benchmark de design tokens e plano de arquitetura. | Emite: `PLANNER.json` com `payload_sha256` (Contrato C2). |
| **03** | `aidd-master` | Fatiamento da arquitetura em Monólito Modular VSA (fatias verticais de domínio + núcleo horizontal compartilhado). | Emite: `VSA_DISPATCH.json` (Contrato C3). |
| **04** | `aidd-dispatch` | Resolução topológica (DAG de Kahn) e criação de Git Worktrees paralelas/efêmeras para isolamento das fatias. | Cria worktrees em `.worktrees/vsa-<slice>`. |
| **05** | **Motor da Tríade** | Execução e materialização do código dentro das worktrees isoladas (`aidd-pure`, `aidd-open` ou `aidd-freedom`). | Código funcional + testes unitários e de integração por fatia. |
| **06** | **Barreira de Sincronização** | Micro-gates de worktree (< 2s), rebase preventivo contra a branch de integração e resolução limpa de merge. | Emite: `dispatch_rollback_report.json` em caso de conflito. |
| **07** | `aidd-enterprise` | Injeção determinística de componentes auditados (SHA-256) e blindagem criptográfica do monólito unificado. | Emite: `HANDOFF_MASTER_ENTERPRISE.json` (Contrato C4). |
| **08** | `aidd-ops` | Geração da infraestrutura em Docker Compose, dimensionamento de VPS, hardening de portas e telemetria Uptime Kuma. | Emite: `docker-compose.yml`, perfis de nicho e scripts VPS. |
| **09** | **54 Macro-Gates** | Bateria global de conformidade executada via `python ecossistema.py audit` e hooks pre-commit (AST, Segredos, Leis). | Exit 0 = Aprovado integralmente; Exit 1 = Bloqueio imediato. |
| **10** | **Commit Consolidado** | Selo de integridade final no git com assinatura HMAC e gravação das evidências em `docs/teste-end-to-end/`. | Commit no histórico com fechamento do ciclo. |

---

## 4. NÍVEL MICRO: ANATOMIA INTERNA DO `aidd-planner`

O **`aidd-planner`** é o coração da inteligência e do design do ecossistema. Quando ele falha, todo o downstream (Master, Engine, Frontend) sofre com cascas cosméticas. A sua anatomia interna desdobra-se em **6 sub-fases determinísticas**:

```
[2.1 Socrático: aidd-grill] ➔ [2.2 BDD/SDD: aidd-spec] ➔ [2.3 Benchmark: mobbin-mcp]
                                                                     │
[2.6 PLANNER.json (SHA-256)] ◄── [2.5 Design Tokens] ◄── [2.4 Mapeamento Tela ➔ Endpoints]
```

### Micro-Etapa 2.1: Interrogatório Socrático (`aidd-grill`)
- **Papel:** Extrair do usuário (ou do arquivo de briefing) o propósito real do sistema, restrições não-negociáveis e vocabulário semântico.
- **Entrada:** Solicitação do usuário ou documento de escopo.
- **Saída:** `.aidd/intake/grill.md`.
- **Invariante:** Não pode conter perguntas genéricas sem contexto. Se o domínio for "RevOps Cirúrgico", as perguntas devem cobrir faturamento CFOP, conformidade ANVISA e rastreamento de kits.

### Micro-Etapa 2.2: Especificação Funcional BDD/SDD (`aidd-spec`)
- **Papel:** Transformar o entendimento socrático em cenários executáveis no formato Gherkin (Dado/Quando/Então) e delimitação de Bounded Contexts.
- **Entrada:** `.aidd/intake/grill.md`.
- **Saída:** `.aidd/intake/spec.md`.
- **Bloco Mandatório `### Visual Direction`:**
  - `tom:` (ex: "Clínico, corporativo, alta precisão, denso").
  - `cor_primaria:` (ex: `#0F172A` ou OKLCH slate).
  - `referencias:` (ex: "Veeva Systems, Epic Systems, NetSuite ERP, Stripe Billing"). **PROIBIDO chumbamento estático de Linear/Asana sem pertinência de domínio!**
  - `publico:` (ex: "Auditores fiscais, cirurgiões bucomaxilofaciais, gestores de logística").

### Micro-Etapa 2.3: Benchmark Visual Dinâmico no Mobbin (`mobbin-mcp`)
- **Papel:** Consultar o Mobbin MCP de forma contextualizada usando as palavras-chave extraídas das referências da especificação.
- **Ferramentas NANO acionadas:**
  - `mobbin_buscar_telas(query="healthcare inventory tracking tables")`.
  - `mobbin_extrair_tokens(screen_id=...)`.
  - `mobbin_compilar_design_system(tokens=...)`.
- **Saída:** `.aidd/intake/DESIGN-SYSTEM.json`.

### Micro-Etapa 2.4: Mapeamento Obrigatório Tela ➔ Endpoints (Cura do Bug do Revnault)
- **Papel:** Garantir a paridade biunívoca entre o Contrato OpenAPI 3.1 do Backend e as Telas do Frontend.
- **Regra Determinística:** Para cada Bounded Context (ex: `contracts`, `tickets`, `contacts`):
  - Listar **100% dos endpoints REST declarados**.
  - Declarar a qual componente de UI cada endpoint está conectado (Tabela, Formulário Modal, Gaveta de Ações, Gráfico).
  - **Proibição de Cascas Cosméticas:** Se um endpoint `POST /api/v1/tickets/anvisa-rma` existe no backend, é proibido renderizar apenas uma caixa genérica de upload na tela de RMA; deve existir o formulário de lote ANVISA e a tabela de quarentena.

### Micro-Etapa 2.5: Geração de Tokens Bi-Modais (`tokens.css`)
- **Papel:** Produzir o CSS soberano conforme a Lei #11.
- **Invariante de Modo Claro (Light Mode Sovereign):**
  - `:root` em Light Mode (`oklch(0.985 0.002 285)`, superfícies off-white/brancas, bordas slate de 1px, contraste WCAG 2.2 AA).
  - `.dark` como suporte complementar persistido no `localStorage`.

### Micro-Etapa 2.6: Compilação Criptográfica do `PLANNER.json`
- **Papel:** Serializar o blueprint completo do sistema com assinatura SHA-256 no payload canônico.
- **Saída:** `.aidd/intake/PLANNER.json`.
- **Validação:** Consumido pelo `aidd-master` para gerar o fatiamento VSA.

---

## 5. NÍVEL NANO: AS PEÇAS ATÔMICAS DE EXECUÇÃO

O nível Nano compreende os blocos elementares e determinísticos que executam o trabalho mecânico em cada micro-fase:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                             PEÇAS NANO (ATÔMICAS)                        │
├─────────────────┬──────────────────┬──────────────────┬──────────────────┤
│      MCPs       │      SKILLS      │   QUALITY GATES  │    GIT HOOKS     │
│  (Ferramentas)  │  (Raciocínio)    │  (Travas Código) │  (Barreiras OS)  │
├─────────────────┼──────────────────┼──────────────────┼──────────────────┤
│ • mobbin-mcp    │ • aidd-grill     │ • G_DETERMINISMO │ • pre-commit     │
│ • memory-mcp    │ • aidd-spec      │ • G_CRAFT_VISUAL │ • regra10_check  │
│ • playwright    │ • aidd-planner   │ • G_TESTES_REAIS │ • auto_session   │
│ • chrome-mcp    │ • aidd-impeccable│ • G_UI_PARITY    │ • anti_headless  │
└─────────────────┴──────────────────┴──────────────────┴──────────────────┘
```

1. **MCPs (Model Context Protocol):**
   - `mobbin-mcp`: Busca real de telas (`mobbin_buscar_telas`), extração de tokens (`mobbin_extrair_tokens`) e compilação de design system.
   - `codebase-memory-mcp`: Indexação semântica e grafo de dependências do repositório (Lei #14 Graph-First).
   - `playwright`: Navegador headless para inspeção visual em tempo de execução, captura de screenshots e auditoria de contraste/layout bi-modal.
   - `chrome-devtools-mcp`: Inspeção do DOM, extração de estilos CSS computados e validação de acessibilidade WCAG.
2. **Skills:**
   - `aidd-grill`: Condução da entrevista socrática de extração de requisitos.
   - `aidd-spec`: Redação de especificação formal em BDD/SDD.
   - `aidd-planner`: Síntese e orquestração do blueprint.
   - `aidd-impeccable-full`: Esteira de 7 etapas de lapidação de UI (`init` ➔ `document` ➔ `critique` ➔ `audit` ➔ `polish` ➔ `harden` ➔ `extract`).
3. **Quality Gates Determinísticos (Python AST / Regex):**
   - Execução pura (< 1s por gate), zero LLM, saída estritamente binária (`exit 0` = aprova, `exit 1` = bloqueia per Lei #2).
   - Teste mandatório que prova que morde (Lei #13).
4. **Git Hooks & Pre-commit:**
   - Bloqueio de commits no sistema operacional caso qualquer micro-gate ou segredo seja violado.

---

## 6. CASO DE ESTUDO: ANÁLISE FORENSE DO `Revnault` (`proj_revops`)

O projeto [proj_revops](file:///C:/Users/trcnologia/Desktop/_inbox/proj_revops) exemplifica na prática o que ocorre quando a esteira falha nas micro-etapas 2.3 e 2.4:

### 6.1 Os Fatos Mensuráveis
Conforme auditado pelo script [`scratch_scan_frontend.py`](file:///C:/Users/trcnologia/Desktop/_inbox/proj_revops/scratch_scan_frontend.py) e pelo [RELATORIO_HOMOLOGACAO_PROFUNDA_E2E_REVNAULT.md](file:///C:/Users/trcnologia/Desktop/_inbox/proj_revops/RELATORIO_HOMOLOGACAO_PROFUNDA_E2E_REVNAULT.md):

- **Endpoints Backend Construídos:** `196` caminhos OpenAPI únicos, cobrindo regras fiscais brasileiras (CFOP 5917/1918/5113), conformidade ANVISA, CRM odontológico e telemetria cirúrgica.
- **Chamadas Reais no Frontend:** Apenas `27` requisições `fetch()` ativas no código TypeScript.
- **Taxa de Utilização dos Motores:** **`12,11%`**.
- **Módulos com 0% de UI:** 27 de 38 sub-módulos ficaram completamente invisíveis para o utilizador.

### 6.2 As 7 Cascas Cosméticas Mapeadas
1. **Contratos Documenso:** Prometia calculadora de alçada comercial e assinaturas digitais SHA-256; exibia apenas uma caixa genérica pontilhada de upload para o R2 (`<R2DirectUploader />`).
2. **Suporte & RMA ANVISA:** Prometia garantia de osseointegração e bloqueio de lote contaminado; exibia a mesma caixa de upload de arquivo da tela de contratos.
3. **Cal.com Reativação:** Três telas diferentes (`Cockpit Executivo`, `BI Superset` e `Cal.com Reativação`) renderizavam exatamente o mesmo iframe do Apache Superset.
4. **Inteligência Artificial:** 6 motores de IA (RAG cirúrgico, Text-to-SQL, Estoque $SOK$, Margem clínica por cadeira, Health Score $HSC$, Transcrição Whisper) foram omitidos em favor de um card travado em `dealId="d-101"`.
5. **CRM de Cirurgiões:** Ausência de listagem de contatos e validação CFO; exibia apenas um input solto de teste de CRO.
6. **Consignação e DENTGO:** Telas renderizadas como *EmptyState* sem botões para criação de novas ordens ou despacho express.
7. **Omnichannel:** Exibia cirurgião não identificado (`cnt-01`) e erro HTTP 404 em visualizador 3D, sem caixa de mensagens WhatsApp.

---

## 7. A SOLUÇÃO DEFINITIVA: O NOVO QUALITY GATE `G_UI_API_PARITY`

Para eliminar de forma permanente a ocorrência de cascas cosméticas e subutilização de motores, introduz-se a especificação do novo portão de qualidade determinístico:

### Especificação do Gate `G_UI_API_PARITY.py`
- **Localização:** `modulos/01-governanca-e-qualidade/gates/G_UI_API_PARITY.py`.
- **Fase de Ativação:** Etapa 6 (Barreira de Sincronização) e Etapa 9 (Macro-Gates).
- **Mecânica Determinística (Zero LLM):**
  1. O gate lê a árvore de rotas OpenAPI 3.1 do backend (`src/**/router.py` ou `openapi.json`).
  2. O gate executa um parser estático (AST / Regex derivado de `scratch_scan_frontend.py`) em todos os arquivos `.ts` e `.tsx` de `frontend/src/`, catalogando todos os endpoints invocados.
  3. Calcula-se a **Taxa de Paridade de Endpoints** ($TPE$):
     $$TPE = \frac{\text{Endpoints Conectados na UI}}{\text{Endpoints Totais da API}} \times 100$$
  4. **Critério Binário de Aprovação (Lei #2):**
     - Se $TPE \ge 85\%$: **Aprovado (`exit 0`)**.
     - Se $TPE < 85\%$: **Reprovado (`exit 1`)**, listando cada endpoint órfão e a fatia responsável.
  5. **Trava Anti-Casca Cosmética:** Proíbe componentes que contenham o mesmo template genérico repetido em mais de 2 rotas de domínio distintas sem parâmetros funcionais dedicados.

---

## 8. CONCLUSÃO E DIRETRIZES DE EXECUÇÃO

1. **Referências Dinâmicas:** Todo plano de UI deve nascer exclusivamente das palavras-chave do Bounded Context extraídas em `grill.md`, sendo banido qualquer chumbamento de referências padrão.
2. **Design System Soberano:** Modo Claro como padrão obrigatório de entrada, com suporte bi-modal persistido via tokens OKLCH.
3. **Paridade Funcional Absoluta:** O frontend gerado deve refletir a totalidade das regras e modelos construídos no backend, honrando a capacidade máxima da engenharia AIDD.
