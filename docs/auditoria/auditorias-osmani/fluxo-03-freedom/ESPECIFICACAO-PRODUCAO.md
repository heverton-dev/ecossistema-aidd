# Especificação de Produção — Máquina Geradora do Fluxo Freedom (AIDD-Osmani)

> **Alvo:** Ferramentas geradoras da máquina (`ecossistema-aidd`)  
> **Referência:** Contrato Inviolável `CONSTRAINTS.md` (Padrão RevNault 9 Camadas)  
> **Status:** ESPECIFICAÇÃO DE PRONTIDÃO FORMALIZADA  

---

## 1. Especificação Funcional por Ferramenta (Critérios BDD/SDD)

### 1.1. `aidd-planner` (Etapa 02)
- **C1.1 (Ambiente Autônomo):** Quando executado com `--modo-intake autonomo`, o CLI deve automaticamente assumir `--mobbin 1` e gerar `.aidd/ambiente.json` com `status: ok` sem abortar a execução.
- **C1.2 (Sintetizador de Spec):** No modo autônomo, o planner deve gerar `.aidd/intake/spec.md` contendo obrigatoriamente critérios mecânicos válidos que passem no linter sintático com `exit code 0`.

### 1.2. `aidd-freedom` (Etapa 05)
- **C2.1 (Isolamento Pytest):** A função `_rodar_testes_fatia` deve sempre invocar o `pytest` usando caminhos relativos ao projeto e injetar `-o testpaths=<rel_path>`, garantindo que repositórios em caminhos com colchetes (ex.: `[TESTE]`) executem com `exit code 0`.
- **C2.2 (Soberania Zero Stubs):** O scanner deve aceitar modo autônomo sem pasta de export prévio quando a spec ditar construção soberana direta.

### 1.3. `tanstack_exporter` e Template `frontend-tanstack` (Etapa 07)
- **C3.1 (Scaffold Corporativo Padrão Linear):** O template `frontend-tanstack` deve fornecer nativamente componentes corporativos de alta densidade:
  - `DataTable.tsx`: Tabela fluida full-viewport com filtros inline, badges semânticos e ordenação.
  - `KanbanBoard.tsx`: Quadro Kanban responsivo de tela inteira com colunas expansíveis e contadores.
  - `MetricCard.tsx`: Cards de indicadores com elevação ardósia profunda e tipografia Inter/Geist.
- **C3.2 (Design Tokens Corporativos):** O arquivo `tokens.css` deve adotar a paleta ardósia corporativa em OKLCH com contraste WCAG 2.2 AA mínimo de 4.5:1 para texto normal e bordas translúcidas de elevação.

### 1.4. Quality Gates Visuais (Etapa 10)
- **C4.1 (Gate Visual Playwright):** O ecossistema deve dispor do gate `G_CRAFT_VISUAL_PLAYWRIGHT.py`, que inicia o dev server em headless, valida a ausência de contraste < 2:1 e reprova UIs com menos de 75% de ocupação de viewport horizontal.
